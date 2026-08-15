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
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.params import Param, Params

from ..app import Asset
from ..helper import LdapHelper
from .run_query import AttributesOutput, EntriesOutput, render_display_attributes  # noqa: F401


class GetAttributesParams(Params):
    principals: str = Param(
        description="The semi-colon separated principals. These can be sAMAccountName, userprincipalname, or "
        "distinguishedName",
        required=True,
    )
    attributes: str = Param(
        description="Semi-colon separated list of attributes to collect",
        required=True,
        default="sAMAccountName",
    )


class GetAttributesOutput(ActionOutput):
    entries: list[EntriesOutput] = OutputField()


class GetAttributesSummary(ActionOutput):
    total_objects: int | None = None


def get_attributes(
    params: GetAttributesParams, soar: SOARClient, asset: Asset
) -> GetAttributesOutput:
    helper = LdapHelper(asset)
    principals = [i.strip() for i in params.principals.split(";")]
    resp = helper.get_attributes(principals, params.attributes)

    entries = [
        EntriesOutput(
            dn=entry["dn"], attributes=AttributesOutput(**entry["attributes"])
        )
        for entry in resp["entries"]
    ]

    total_objects = len(helper.get_filtered_response())
    soar.set_summary(GetAttributesSummary(total_objects=total_objects))
    soar.set_message(f"Total objects: {total_objects}")
    return GetAttributesOutput(entries=entries)
