# File: adldap_connector.py
#
# Copyright (c) 2021-2025 Splunk Inc.
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
#
#
# Phantom App imports
import json
import os
import ssl
import sys

# switched from python-ldap to ldap3 for this app. -gsh
import ldap3
import ldap3.extend.microsoft.addMembersToGroups
import ldap3.extend.microsoft.removeMembersFromGroups
import ldap3.extend.microsoft.unlockAccount
import phantom.app as phantom
from ldap3 import Tls
from ldap3.utils.dn import parse_dn
from phantom.action_result import ActionResult

# import json
from phantom.base_connector import BaseConnector
from phantom_common import paths

from adldap_consts import *


class RetVal(tuple):
    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class AdLdapConnector(BaseConnector):
    def __init__(self):
        super().__init__()

    def replace_null_values(self, data):
        return json.loads(json.dumps(data).replace("\\u0000", "\\\\u0000"))

    def _dump_error_log(self, error, message="Exception occurred."):
        self.error_print(message, dump_object=error)

    def _ldap_bind(self, action_result=None):
        """
        returns phantom.APP_SUCCESS if connection succeeded,
        else phantom.APP_ERROR.

        If an action_result is passed in, method will
        appropriately use it. Otherwise just return
        APP_SUCCESS/APP_ERROR
        """
        if self._ldap_connection and self._ldap_connection.bound and not self._ldap_connection.closed:
            return True
        elif self._ldap_connection is not None:
            self._ldap_connection.unbind()

        try:
            if self._validate_ssl_cert:
                tls = Tls(ca_certs_file=paths.CA_CERTS_PEM, validate=ssl.CERT_REQUIRED)
            else:
                tls = Tls(validate=ssl.CERT_NONE)

            server_param = {"use_ssl": self._ssl, "port": self._ssl_port, "host": self._server, "get_info": ldap3.ALL, "tls": tls}

            self._ldap_server = ldap3.Server(**server_param)
            self.save_progress(f"configured server {self._server}...")
            self._ldap_connection = ldap3.Connection(self._ldap_server, user=self._username, password=self._password, raise_exceptions=True)
            self.save_progress("binding to directory...")

            if not self._ldap_connection.bind():
                if action_result:
                    return action_result.set_status(phantom.APP_ERROR, self._ldap_connection.result["description"])
                else:
                    return phantom.APP_ERROR

            if action_result:
                return action_result.set_status(phantom.APP_SUCCESS)
            else:
                return phantom.APP_SUCCESS

        except Exception as e:
            self.debug_print(f"ldap_bind, e = {e!s}")
            self._dump_error_log(e)
            if action_result:
                return action_result.set_status(phantom.APP_ERROR, str(e))
            else:
                return phantom.APP_ERROR

    def _get_root_dn(self, action_result=None):
        """
        returns root dn (str) if found, else False.
        """
        if self._ldap_bind():
            try:
                return self._ldap_connection.server.info.other["defaultNamingContext"][0]
            except Exception:
                return False
        else:
            return False

    def _sam_to_dn(self, sam, action_result=None):
        """
        This method will take a list of samaccountnames
        and return a dictionary with the key as the
        samaccountname and the value as the distinguishedname.

        If a corresponding distinguishedname was not found, then
        the key will be the samaccountname and the value will be
        False.
        """

        # create a usable ldap filter
        filter = "(|"
        for users in sam:
            filter = filter + f"(samaccountname={users})"
        filter = filter + ")"

        query_params = {"attributes": "distinguishedname;samaccountname", "filter": filter}

        ret_val, dn = self._query(action_result, query_params)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), {}
        dn = json.loads(dn)

        # construct a dict of Name = False (default) for each samaccountname given
        # then, if we find our samaccountname in the result, grab the distinguishedname,
        # put it in the dict, and return it (else the default of False).
        return_value = {name.lower(): False for name in sam}
        self.debug_print("_sam_to_dn entries = {}".format(dn["entries"]))
        for entries in dn["entries"]:
            samaccountname = (entries["attributes"]["sAMAccountName"]).lower()
            if samaccountname in return_value:
                return_value[samaccountname] = (entries["attributes"]["distinguishedName"]).lower()

        self.debug_print(f"_sam_to_dn return_value = {return_value}")

        return action_result.set_status(phantom.APP_SUCCESS), return_value

    def _get_filtered_response(self):
        """
        returns a list of objects from LDAP results
        that do not match type=searchResRef
        """
        try:
            return [i for i in self._ldap_connection.response if i["type"] != "searchResRef"]
        except Exception as e:
            self.debug_print(f"get_filtered_response(), exception: {e!s}")
            return []

    def _handle_group_members(self, param, add):
        """
        handles membership additions and removals.
        if add=True then add to groups,
        otherwise: remove from groups.
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        if not self._ldap_bind(action_result):
            return action_result.get_status()

        members = [i.strip() for i in param["members"].split(";")]
        groups = [i.strip() for i in param["groups"].split(";")]

        # resolve samaccountname -> distinguishedname if option selected
        if param.get("use_samaccountname", False):
            n_members = []  # new list of users
            n_groups = []  # new list of groups
            member_nf = []  # not found users
            group_nf = []  # not found groups

            # finding users dn by sam
            ret_val, t_users = self._sam_to_dn(members, action_result=action_result)
            if phantom.is_fail(ret_val):
                return action_result.get_status()

            # add summary regarding number of records requested
            # vs number of records found.
            action_result.update_summary(
                {"requested_user_records": len(members), "found_user_records": len([k for (k, v) in list(t_users.items()) if v is not False])}
            )
            for k, v in list(t_users.items()):
                if v is False:
                    member_nf.append(k)
                else:
                    n_members.append(v)

            # the next two blocks could be abstracted into a method,
            # but the author feels that somewhat duplicate code is a small
            # cost for arguably greater readability.

            # finding groups dn by sam
            ret_val, t_group = self._sam_to_dn(groups, action_result=action_result)
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            for k, v in list(t_group.items()):
                if v is False:
                    group_nf.append(k)
                else:
                    n_groups.append(v)

            # ensure we actually have a least 1 user and group to modify
            if len(n_members) > 0 and len(n_groups) > 0:
                members = n_members
                groups = n_groups
            else:
                self.debug_print(f"n_members = {n_members}")
                self.debug_print(f"n_groups = {n_groups}")
                return action_result.set_status(phantom.APP_ERROR, "Not enough groups or members")

        try:
            if add:
                func = "added"
                ldap3.extend.microsoft.addMembersToGroups.ad_add_members_to_groups(
                    connection=self._ldap_connection, members_dn=members, groups_dn=groups, fix=True, raise_error=True
                )
            else:
                func = "removed"
                ldap3.extend.microsoft.removeMembersFromGroups.ad_remove_members_from_groups(
                    connection=self._ldap_connection, members_dn=members, groups_dn=groups, fix=True, raise_error=True
                )
        except Exception as e:
            self._dump_error_log(e)
            if type(e).__name__ == "LDAPInvalidDnError":
                error_msg = (
                    "LDAPInvalidDnError: If 'use samaccountname' is unchecked, member(s) and group(s) values must be in distinguishedName format"
                )
            else:
                error_msg = str(e)
            return action_result.set_status(phantom.APP_ERROR, error_msg)

        # add action data results
        for i in members:
            for j in groups:
                action_result.add_data({"member": i, "group": j, "function": func})
        return action_result.set_status(phantom.APP_SUCCESS, "{} member(s) {} group(s)".format(func, "to" if func == "added" else "from"))

    def _handle_unlock_account(self, param):
        """
        This method unlocks an active directory account.

        If the use_samaccountname is checked, method will resolve
        the input samaccountname(user) -> distinguishedName and then use the
        ldap3 library to unlock the account.
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        summary = action_result.update_summary({})
        user = param["user"].lower()
        ar_data = {}  # data for action_result

        if param.get("use_samaccountname", False):
            ret_val, user_dn = self._sam_to_dn([user], action_result=action_result)  # _sam_to_dn requires a list.
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            if len(user_dn) == 0 or user_dn[user] is False:
                ar_data["unlocked"] = summary["unlocked"] = False
                action_result.add_data(ar_data)
                return action_result.set_status(phantom.APP_ERROR, "No users found")
            ar_data["user_dn"] = user_dn[user]
            ar_data["samaccountname"] = user
            user = user_dn[user]
        else:
            ar_data["user_dn"] = user

        if not self._ldap_bind(action_result):
            ar_data["unlocked"] = summary["unlocked"] = False
            action_result.add_data(ar_data)
            return action_result.get_status()

        try:
            ldap3.extend.microsoft.unlockAccount.ad_unlock_account(
                self._ldap_connection,
                user_dn=ar_data["user_dn"],
            )
            ar_data["unlocked"] = True
        except Exception as e:
            self._dump_error_log(e)
            ar_data["unlocked"] = summary["unlocked"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR, str(e))

        action_result.add_data(ar_data)
        summary["unlocked"] = True
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_account_status(self, param, disable=False):
        """
        This reads in the existing UAC and _only_ modifies the disabled flag. Does not
        reset any additional flags.
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        summary = action_result.update_summary({})
        actstr = "disabled" if disable else "enabled"
        if not self._ldap_bind(action_result):
            return action_result.get_status()

        user = param["user"].lower()
        ar_data = {}

        # let the analyst use samaccountname if they wish
        if param.get("use_samaccountname", False):
            ret_val, user_info = self._sam_to_dn([user], action_result=action_result)
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            ar_data["samaccountname"] = user
            if user_info[user] is False:
                return action_result.set_status(phantom.APP_ERROR, "No users found")
            else:
                ar_data["user_dn"] = user_info[user]
                ar_data["samaccountname"] = user
                user = user_info[user]
        else:
            ar_data["user_dn"] = user

        try:
            query_params = {"attributes": "useraccountcontrol", "filter": f"(distinguishedname={user})"}
            ret_val, resp = self._query(action_result, query_params)
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            resp = json.loads(resp)

            if len(resp["entries"]) == 0:
                return action_result.set_status(phantom.APP_ERROR, "No user found")

            uac = int(resp["entries"][0]["attributes"]["userAccountControl"])

            # capture the original status for logging
            init_status = "disabled" if (uac & 0x02 != 0) else "enabled"
            ar_data["starting_status"] = init_status

            if disable:
                mod_uac = uac | 0x02
            else:  # enable
                mod_uac = uac & (0xFFFFFFFF ^ 0x02)

            res = self._ldap_connection.modify(user, {"userAccountControl": [(ldap3.MODIFY_REPLACE, [mod_uac])]})
            if not res:
                return action_result.set_status(phantom.APP_ERROR, self._ldap_connection.result)
        except Exception as e:
            self._dump_error_log(e)
            self.debug_print(f"disable_account error = {e!s}")
            return action_result.set_status(phantom.APP_ERROR, str(e))

        summary["account_status"] = actstr
        action_result.add_data(ar_data)
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_move_object(self, param):
        """
        Moves an arbitrary object within the
        directory to a new OU.
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        summary = action_result.update_summary({})
        ar_data = {}

        obj = param["object"]
        destination_ou = param["destination_ou"]
        self.debug_print("Moving an object in AD")

        if not self._ldap_bind(action_result):
            ar_data["moved"] = summary["moved"] = False
            action_result.add_data(ar_data)
            return action_result.get_status()

        try:
            cn = "=".join(parse_dn(obj)[0][:-1])
            res = self._ldap_connection.modify_dn(obj, cn, new_superior=destination_ou)
            if not res:
                ar_data["moved"] = summary["moved"] = False
                action_result.add_data(ar_data)
                return action_result.set_status(phantom.APP_ERROR, self._ldap_connection.result)
            ar_data["source_object"] = obj
            ar_data["destination_container"] = destination_ou
        except Exception as e:
            self._dump_error_log(e)
            ar_data["moved"] = summary["moved"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR, str(e))
        action_result.add_data(ar_data)
        summary["moved"] = True
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        # failure
        if not self._ldap_bind(action_result):
            self.save_progress("Test Connectivity Failed")
            return action_result.get_status()

        # success
        self.save_progress("Test Connectivity Passed")
        return action_result.set_status(action_result.get_status())

    def _handle_get_attributes(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        summary = action_result.update_summary({})

        if not self._ldap_bind(action_result):
            return action_result.get_status()

        query = "(|"
        principal = [i.strip() for i in param["principals"].split(";")]
        self.debug_print("Fetching attributes for a principal")

        # build a query on the fly with the principals provided
        for i in principal:
            query += f"(userprincipalname={i})(samaccountname={i})(distinguishedname={i})"
        query += ")"

        ret_val, resp = self._query(action_result, {"filter": query, "attributes": param["attributes"]})
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        action_result.add_data(json.loads(resp))
        summary["total_objects"] = len(self._get_filtered_response())
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_set_attribute(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        summary = action_result.update_summary({})

        user = param["user"].lower()
        attribute = param["attribute"]
        value = param.get("value")
        action = param["action"]

        if (action == "ADD" or action == "REPLACE") and value is None:
            action_result.add_data({"message": "Failed"})
            summary["message"] = "Failed"
            return action_result.set_status(phantom.APP_ERROR, f"Value parameter must be filled when using {action} action")

        ar_data = {}
        if param["use_samaccountname"]:
            ret_val, user_dn = self._sam_to_dn([user], action_result=action_result)  # _sam_to_dn requires a list.
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            if len(user_dn) == 0 or user_dn[user] is False:
                action_result.add_data({"message": "Failed"})
                summary["message"] = "Failed"
                return action_result.set_status(phantom.APP_ERROR, "No users found")

            ar_data["user_dn"] = user_dn[user]
            ar_data["samaccountname"] = user
            user = user_dn[user]
        else:
            ar_data["user_dn"] = user

        changes = {}

        if action == "ADD":
            changes[attribute] = [(ldap3.MODIFY_ADD, [value])]
        elif action == "DELETE":
            changes[attribute] = [(ldap3.MODIFY_DELETE, [])]
        elif action == "REPLACE":
            changes[attribute] = [(ldap3.MODIFY_REPLACE, [value])]

        if not self._ldap_bind(action_result):
            action_result.add_data({"message": "Failed"})
            summary["message"] = "Failed"
            return action_result.get_status()

        try:
            self.debug_print(f"mod_string = {changes}")
            ret = self._ldap_connection.modify(dn=ar_data["user_dn"], changes=changes)
            self.debug_print(f"handle_set_attribute, ret = {ret}")
        except Exception as e:
            self._dump_error_log(e)
            action_result.add_data({"message": "Failed"})
            summary["message"] = "Failed"
            return action_result.set_status(phantom.APP_ERROR, str(e))

        action_result.add_data({"message": ("Success" if ret else "Failed")})
        action_result.set_status(ret)
        summary["summary"] = "Successfully Set Attribute"
        self.debug_print(f"resp = {self._ldap_connection.response_to_json()}")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_rename_object(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        summary = action_result.update_summary({})

        ar_data = {}
        user = param["object"].lower()
        new_name = param["new_name"]

        if not self._ldap_bind(action_result):
            action_result.add_data({"message": "Failed"})
            summary["message"] = "Failed"
            return action_result.get_status()

        if param.get("use_samaccountname", False):
            ret_val, user_dn = self._sam_to_dn([user], action_result=action_result)
            if phantom.is_fail(ret_val):
                return action_result.get_status()

            if not user_dn or user_dn.get(user) is False:
                action_result.add_data({"message": "Failed"})
                summary["message"] = "Failed"
                return action_result.set_status(phantom.APP_ERROR, "No users found")

            ar_data["user_dn"] = user_dn[user]
            ar_data["samaccountname"] = user
            user = user_dn[user]
        else:
            ar_data["user_dn"] = user

        try:
            self.debug_print(f"rename distinguishedName {user} to {new_name} ")
            ret = self._ldap_connection.modify_dn(ar_data["user_dn"], new_name)
            self.debug_print(f"handle_rename_object, ret = {ret}")
        except Exception as e:
            self._dump_error_log(e)
            action_result.add_data({"message": "Failed"})
            summary["message"] = "Failed"
            return action_result.set_status(phantom.APP_ERROR, str(e))

        action_result.add_data({"message": ("Success" if ret else "Failed")})
        action_result.set_status(ret)
        summary["summary"] = "Successfully Renamed Object"
        self.debug_print(f"resp = {self._ldap_connection.response_to_json()}")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _query(self, action_result, param):
        """
        This method handles the query and returns
        the response in the ldap connection object
        as json.

        Returns the data or throws and exception.
        param must include:
            - attributes (to retrieve - semi-colon separated string:
                e.g. "mail;samaccountname;pwdlastset")
            - filter (ldap query)
        """
        attrs = [i.strip() for i in param["attributes"].split(";")]
        filter = param["filter"]
        search_base = param.get("search_base", self._get_root_dn())

        try:
            # throw exception if we cannot bind
            if not self._ldap_bind(action_result):
                return action_result.get_status(), {}

            self._ldap_connection.search(search_base=search_base, search_filter=filter, search_scope=ldap3.SUBTREE, attributes=attrs)
        except Exception as e:
            self._dump_error_log(e)
            self.debug_print(f"{e!s}")
            return action_result.set_status(phantom.APP_ERROR, str(e)), {}

        return action_result.set_status(phantom.APP_SUCCESS), self._ldap_connection.response_to_json()

    def _handle_run_query(self, param):
        """
        This method handles arbitrary LDAP queries for
        those who are skilled w/ that syntax.
        e.g.
        "(|(&(mail=alice@company*)(samaccountname=alice*))(manager=bob))
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")

        summary = action_result.update_summary({})

        ret_val, resp = self._query(action_result, param)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        # unify the attributes returned from AD to lowercase keys
        out_data = json.loads(resp)
        for i, _ in enumerate(out_data["entries"]):
            out_data["entries"][i]["attributes"] = {k.lower(): v for k, v in list(out_data["entries"][i]["attributes"].items())}

        # set data path stuff and exit
        action_result.add_data(out_data)
        summary["total_objects"] = len(self._get_filtered_response())
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_reset_password(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        user = param["user"].lower()
        summary = action_result.update_summary({})

        ar_data = {}
        if param.get("use_samaccountname", False):
            ret_val, user_dn = self._sam_to_dn([user], action_result=action_result)  # _sam_to_dn requires a list.
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            if len(user_dn) == 0 or user_dn[user] is False:
                ar_data["reset"] = summary["reset"] = False
                action_result.add_data(ar_data)
                return action_result.set_status(phantom.APP_ERROR, "No users found")

            ar_data["user_dn"] = user_dn[user]
            ar_data["samaccountname"] = user
            user = user_dn[user]
        else:
            ar_data["user_dn"] = user

        changes = {}
        changes["pwdlastset"] = [(ldap3.MODIFY_REPLACE, [str(0)])]

        if not self._ldap_bind(action_result):
            ar_data["reset"] = summary["reset"] = False
            action_result.add_data(ar_data)
            return action_result.get_status()

        try:
            self.debug_print(f"mod_string = {changes}")
            ret = self._ldap_connection.modify(dn=ar_data["user_dn"], changes=changes)
            self.debug_print(f"handle_reset_attribute, ret = {ret}")
        except Exception as e:
            self._dump_error_log(e)
            ar_data["reset"] = summary["reset"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR, str(e))

        self.debug_print(f"resp = {self._ldap_connection.response_to_json()}")

        if ret:
            ar_data["reset"] = summary["reset"] = True
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_SUCCESS)
        else:
            ar_data["reset"] = summary["reset"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR)

    def _handle_set_password(self, param):
        """
        This method sets a users password.
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        summary = action_result.update_summary({})
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        self.debug_print("handle_set_password")

        user = param["user"].lower()
        pwd = param["password"]
        confirm_pwd = param["confirm_password"]
        ar_data = {}
        if pwd != confirm_pwd:
            ar_data["set"] = summary["set"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR, "Passwords do not match")

        if not self._ldap_bind(action_result):
            self.debug_print("handle_set_password - no bind")
            ar_data["set"] = summary["set"] = False
            action_result.add_data(ar_data)
            return action_result.get_status()

        if param.get("use_samaccountname", False):
            ret_val, user_dn = self._sam_to_dn([user], action_result=action_result)  # _sam_to_dn requires a list.
            if phantom.is_fail(ret_val):
                return action_result.get_status()
            if len(user_dn) == 0 or user_dn[user] is False:
                ar_data["set"] = summary["set"] = False
                action_result.add_data(ar_data)
                return action_result.set_status(phantom.APP_ERROR, "No users found")

            ar_data["user_dn"] = user_dn[user]
            ar_data["samaccountname"] = user
            user = user_dn[user]
        else:
            ar_data["user_dn"] = user

        try:
            self.debug_print("about to attempt password set...")
            ret = self._ldap_connection.extend.microsoft.modify_password(user, pwd)
        except Exception as e:
            self._dump_error_log(e)
            self.debug_print(f"handle_set_password, e = {e!s}")
            ar_data["set"] = summary["set"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(
                phantom.APP_ERROR,
                f"""{e!s}. Also, please make sure that the account in asset has permissions
                                            to Set Password and password meets complexity requirements""",
            )
        self.debug_print(f"handle_set_password, ret = {ret}")
        if ret:
            ar_data["set"] = summary["set"] = True
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_SUCCESS)
        else:
            ar_data["set"] = summary["set"] = False
            action_result.add_data(ar_data)
            return action_result.set_status(phantom.APP_ERROR)

    def _handle_add_group_members(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        self.debug_print("Adding objects to groups")

        return self._handle_group_members(param, True)

    def _handle_remove_group_members(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        self.debug_print("Removing objects from groups")

        return self._handle_group_members(param, False)

    def _handle_disable_account(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        self.debug_print("Disabling an AD account")

        return self._handle_account_status(param, disable=True)

    def _handle_enable_account(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        self.debug_print("Enabling a disabled AD account")

        return self._handle_account_status(param, disable=False)

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        action_id = self.get_action_identifier()
        self.debug_print(f"ADLDAPENV = {os.environ}")
        self.debug_print("action_id", self.get_action_identifier())

        if action_id == "test_connectivity":
            ret_val = self._handle_test_connectivity(param)

        elif action_id == "run_query":
            ret_val = self._handle_run_query(param)

        elif action_id == "add_group_members":
            ret_val = self._handle_add_group_members(param)

        elif action_id == "remove_group_members":
            ret_val = self._handle_remove_group_members(param)

        elif action_id == "unlock_account":
            ret_val = self._handle_unlock_account(param)

        elif action_id == "disable_account":
            ret_val = self._handle_disable_account(param)

        elif action_id == "enable_account":
            ret_val = self._handle_enable_account(param)

        elif action_id == "move_object":
            ret_val = self._handle_move_object(param)

        elif action_id == "get_attributes":
            ret_val = self._handle_get_attributes(param)

        elif action_id == "set_attribute":
            ret_val = self._handle_set_attribute(param)

        elif action_id == "reset_password":
            ret_val = self._handle_reset_password(param)

        elif action_id == "set_password":
            ret_val = self._handle_set_password(param)
        elif action_id == "rename_object":
            ret_val = self._handle_rename_object(param)

        action_results = self.get_action_results()
        if len(action_results) > 0:
            action_result = action_results[-1]
            action_result._ActionResult__data = self.replace_null_values(action_result._ActionResult__data)
            action_result.set_status(ret_val, self.replace_null_values(action_result.get_message()))
        return ret_val

    def initialize(self):
        # Load the state in initialize, use it to store data
        # that needs to be accessed across actions
        self._state = self.load_state()
        if not isinstance(self._state, dict):
            self.debug_print("Resetting the state file with the default format")
            self._state = {"app_version": self.get_app_json().get("app_version")}

        # get the asset config
        config = self.get_config()

        # load our config for use.
        self._server = config["server"]
        self._username = config["username"]
        self._password = config["password"]
        self._ssl = config["force_ssl"]
        self._validate_ssl_cert = config.get("validate_ssl_cert", False)
        self._ssl_port = int(config["ssl_port"])
        self.connected = False
        self._ldap_connection = None

        return phantom.APP_SUCCESS

    def finalize(self):
        # Save the state, this data is saved across actions and app upgrades
        self.save_state(self._state)
        return phantom.APP_SUCCESS


if __name__ == "__main__":
    import argparse

    import pudb
    import requests

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument("input_test_json", help="Input Test JSON file")
    argparser.add_argument("-u", "--username", help="username", required=False)
    argparser.add_argument("-p", "--password", help="password", required=False)
    argparser.add_argument("-v", "--verify", action="store_true", help="verify", required=False, default=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password
    verify = args.verify

    if username is not None and password is None:
        # User specified a username but not a password, so ask
        import getpass

        password = getpass.getpass("Password: ")

    if username and password:
        try:
            login_url = AdLdapConnector._get_phantom_base_url() + "login"

            print("Accessing the Login page")
            r = requests.get(login_url, verify=verify, timeout=DEFAULT_TIMEOUT)
            csrftoken = r.cookies["csrftoken"]

            data = dict()
            data["username"] = username
            data["password"] = password
            data["csrfmiddlewaretoken"] = csrftoken

            headers = dict()
            headers["Cookie"] = "csrftoken=" + csrftoken
            headers["Referer"] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=verify, data=data, headers=headers, timeout=DEFAULT_TIMEOUT)
            session_id = r2.cookies["sessionid"]
        except Exception as e:
            print("Unable to get session id from the platform. Error: " + str(e))
            sys.exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = AdLdapConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json["user_session_token"] = session_id
            connector._set_csrf_info(csrftoken, headers["Referer"])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    sys.exit(0)
