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
from soar_sdk.action_results import ActionOutput
from soar_sdk.params import Param, Params

from ..app import Asset, app


class SetAttributeParams(Params):
    use_samaccountname: bool = Param(
        description="Use sAMAccountName instead of distinguishedName",
        required=False,
        default=False,
    )
    user: str = Param(
        description="User whose attributes are to be modified",
        required=True,
        primary=True,
        cef_types=["user name"],
        column_name="User",
    )
    attribute: str = Param(
        description="The attribute to modify (add/delete/replace)",
        required=True,
        default="mail",
        column_name="Attribute",
    )
    value: str | None = Param(
        description="Attribute value", default="user@foo.bar", column_name="New Value"
    )
    action: str = Param(
        description="Semi-colon separated list of attributes to collect",
        required=True,
        value_list=["ADD", "DELETE", "REPLACE"],
        column_name="Action",
    )


class SetAttributeOutput(ActionOutput):
    message: str | None = None


class SetAttributeSummary(ActionOutput):
    summary: str | None = None


@app.action(
    description="Add, delete, or replace an attribute of a user",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=SetAttributeSummary,
)
def set_attribute(
    params: SetAttributeParams, soar: SOARClient, asset: Asset
) -> SetAttributeOutput:
    from ..helper import LdapHelper

    if params.action in ("ADD", "REPLACE") and params.value is None:
        raise ValueError(
            f"Value parameter must be filled when using {params.action} action"
        )

    helper = LdapHelper(asset)
    user = params.user.lower()

    if params.use_samaccountname:
        resolved = helper.sam_to_dn([user])
        if resolved[user] is False:
            raise ValueError("No users found")
        user = resolved[user]

    helper.set_attribute(user, params.attribute, params.value, params.action)

    soar.set_summary(SetAttributeSummary(summary="Successfully Set Attribute"))
    soar.set_message("Summary: Successfully Set Attribute")
    return SetAttributeOutput(message="Success")
