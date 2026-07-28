# Copyright (c) 2021-2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.

import json
import ssl

import ldap3
import ldap3.extend.microsoft.addMembersToGroups
import ldap3.extend.microsoft.removeMembersFromGroups
import ldap3.extend.microsoft.unlockAccount
from ldap3 import Tls
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import parse_dn
from soar_sdk.logging import getLogger

from .consts import CA_CERTS_PEM


logger = getLogger()


class LdapHelper:
    def __init__(self, asset):
        self._server = asset.server
        self._username = asset.username
        self._password = asset.password
        self._ssl = asset.force_ssl
        self._validate_ssl_cert = asset.validate_ssl_cert
        self._ssl_port = int(asset.ssl_port)
        self._ldap_server = None
        self._ldap_connection = None

    def bind(self) -> None:
        if (
            self._ldap_connection
            and self._ldap_connection.bound
            and not self._ldap_connection.closed
        ):
            return
        if self._ldap_connection is not None:
            self._ldap_connection.unbind()

        if self._validate_ssl_cert:
            tls = Tls(ca_certs_file=CA_CERTS_PEM, validate=ssl.CERT_REQUIRED)
        else:
            tls = Tls(validate=ssl.CERT_NONE)

        server_param = {
            "use_ssl": self._ssl,
            "port": self._ssl_port,
            "host": self._server,
            "get_info": ldap3.ALL,
            "tls": tls,
        }
        self._ldap_server = ldap3.Server(**server_param)
        self._ldap_connection = ldap3.Connection(
            self._ldap_server,
            user=self._username,
            password=self._password,
            raise_exceptions=True,
        )
        if not self._ldap_connection.bind():
            raise Exception(self._ldap_connection.result["description"])

    def get_root_dn(self) -> str | None:
        self.bind()
        try:
            return self._ldap_connection.server.info.other["defaultNamingContext"][0]
        except Exception:
            return None

    def get_filtered_response(self) -> list:
        try:
            return [
                i for i in self._ldap_connection.response if i["type"] != "searchResRef"
            ]
        except Exception as e:
            logger.debug(f"get_filtered_response(), exception: {e!s}")
            return []

    def get_attributes(self, principals: list[str], attributes: str) -> dict:
        query = "(|"
        for principal in principals:
            escaped = escape_filter_chars(principal)
            query += f"(userprincipalname={escaped})(samaccountname={escaped})(distinguishedname={escaped})"
        query += ")"
        return self.query(query, attributes)

    def query(
        self, search_filter: str, attributes: str, search_base: str | None = None
    ) -> dict:
        self.bind()
        attrs = [i.strip() for i in attributes.split(";")]
        if search_base is None:
            search_base = self.get_root_dn()

        self._ldap_connection.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=ldap3.SUBTREE,
            attributes=attrs,
        )
        return json.loads(self._ldap_connection.response_to_json())

    def sam_to_dn(self, sam: list[str]) -> dict[str, str | bool]:
        """Resolve sAMAccountName(s) to distinguishedName(s).

        Returns a dict keyed by the (lowercased) sAMAccountName. Any name that could
        not be resolved maps to False.
        """
        filter_str = "(|"
        for user in sam:
            filter_str += f"(samaccountname={escape_filter_chars(user)})"
        filter_str += ")"

        resp = self.query(filter_str, "distinguishedname;samaccountname")

        return_value: dict[str, str | bool] = dict.fromkeys(sam, False)
        for entry in resp["entries"]:
            samaccountname = entry["attributes"]["sAMAccountName"].lower()
            if samaccountname in return_value:
                return_value[samaccountname] = entry["attributes"][
                    "distinguishedName"
                ].lower()
        return return_value

    def modify_group_members(
        self, members: list[str], groups: list[str], add: bool
    ) -> None:
        self.bind()
        try:
            if add:
                ldap3.extend.microsoft.addMembersToGroups.ad_add_members_to_groups(
                    connection=self._ldap_connection,
                    members_dn=members,
                    groups_dn=groups,
                    fix=True,
                    raise_error=True,
                )
            else:
                ldap3.extend.microsoft.removeMembersFromGroups.ad_remove_members_from_groups(
                    connection=self._ldap_connection,
                    members_dn=members,
                    groups_dn=groups,
                    fix=True,
                    raise_error=True,
                )
        except Exception as e:
            if type(e).__name__ == "LDAPInvalidDnError":
                raise ValueError(
                    "LDAPInvalidDnError: If 'use samaccountname' is unchecked, member(s) and group(s) values must be in distinguishedName format"
                ) from e
            raise

    def unlock_account(self, user_dn: str) -> None:
        self.bind()
        ldap3.extend.microsoft.unlockAccount.ad_unlock_account(
            self._ldap_connection, user_dn=user_dn
        )

    def set_account_status(self, user_dn: str, disable: bool) -> str:
        """Flips only the disabled bit of userAccountControl. Returns the starting status."""
        self.bind()
        resp = self.query(
            f"(distinguishedname={escape_filter_chars(user_dn)})", "useraccountcontrol"
        )
        if len(resp["entries"]) == 0:
            raise ValueError("No user found")

        uac = int(resp["entries"][0]["attributes"]["userAccountControl"])
        starting_status = "disabled" if (uac & 0x02 != 0) else "enabled"

        mod_uac = (uac | 0x02) if disable else (uac & (0xFFFFFFFF ^ 0x02))
        res = self._ldap_connection.modify(
            user_dn, {"userAccountControl": [(ldap3.MODIFY_REPLACE, [mod_uac])]}
        )
        if not res:
            raise Exception(self._ldap_connection.result)
        return starting_status

    def move_object(self, obj: str, destination_ou: str) -> None:
        self.bind()
        cn = "=".join(parse_dn(obj)[0][:-1])
        res = self._ldap_connection.modify_dn(obj, cn, new_superior=destination_ou)
        if not res:
            raise Exception(self._ldap_connection.result)

    def set_attribute(
        self, user_dn: str, attribute: str, value: str | None, action: str
    ) -> None:
        self.bind()
        changes = {}
        if action == "ADD":
            changes[attribute] = [(ldap3.MODIFY_ADD, [value])]
        elif action == "DELETE":
            changes[attribute] = [(ldap3.MODIFY_DELETE, [])]
        elif action == "REPLACE":
            changes[attribute] = [(ldap3.MODIFY_REPLACE, [value])]

        ret = self._ldap_connection.modify(dn=user_dn, changes=changes)
        if not ret:
            ldap_result = self._ldap_connection.result or {}
            error_message = (
                ldap_result.get("message")
                or ldap_result.get("description")
                or "Failed to set attribute"
            )
            raise Exception(error_message)

    def rename_object(self, user_dn: str, new_name: str) -> bool:
        self.bind()
        return self._ldap_connection.modify_dn(user_dn, new_name)

    def reset_password(self, user_dn: str) -> bool:
        self.bind()
        changes = {"pwdlastset": [(ldap3.MODIFY_REPLACE, [str(0)])]}
        return self._ldap_connection.modify(dn=user_dn, changes=changes)

    def set_password(self, user_dn: str, password: str) -> bool:
        self.bind()
        return self._ldap_connection.extend.microsoft.modify_password(user_dn, password)
