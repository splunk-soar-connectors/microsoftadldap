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

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput
from soar_sdk.params import Param, Params

from ..app import Asset
from ..helper import LdapHelper


class RunQueryParams(Params):
    filter: str = Param(
        description="The LDAP filter (must be in LDAP Syntax)", required=True
    )
    search_base: str | None = Param(
        description="The search base to use in its distinguishedName format. If not specified, the "
        "'defaultNamingContext' will be used"
    )
    attributes: str = Param(
        description="Semi-colon separated list of attributes to collect (e.g. sAMAccountName;mail)",
        required=True,
        default="sAMAccountName",
    )


class AttributesOutput(PermissiveActionOutput):
    pass


class EntriesOutput(ActionOutput):
    dn: str | None = OutputField(example_values=["CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB"])
    attributes: AttributesOutput | None = None


class QueryOutput(ActionOutput):
    entries: list[EntriesOutput] = OutputField()


class QuerySummary(ActionOutput):
    total_objects: int | None = None


def render_display_attributes(output: list[QueryOutput]) -> dict:
    results = []
    for item in output:
        entries = [
            {
                "dn": entry.dn,
                "attributes": entry.attributes.model_dump() if entry.attributes else {},
            }
            for entry in item.entries
        ]
        results.append(
            {"data": True, "total_objects": len(entries), "entries": entries}
        )
    return {"results": results}


def run_query(params: RunQueryParams, soar: SOARClient, asset: Asset) -> QueryOutput:
    helper = LdapHelper(asset)
    resp = helper.query(
        params.filter, params.attributes, search_base=params.search_base
    )

    entries = []
    for entry in resp["entries"]:
        attrs = {k.lower(): v for k, v in entry["attributes"].items()}
        entries.append(
            EntriesOutput(dn=entry["dn"], attributes=AttributesOutput(**attrs))
        )

    total_objects = len(helper.get_filtered_response())
    soar.set_summary(QuerySummary(total_objects=total_objects))
    soar.set_message(f"Total objects: {total_objects}")
    return QueryOutput(entries=entries)
