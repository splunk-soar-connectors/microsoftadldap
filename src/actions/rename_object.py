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

from ..app import Asset, app
from ..helper import LdapHelper


class RenameObjectParams(Params):
    object: str = Param(
        description="The object to be renamed",
        required=True,
        primary=True,
        cef_types=["user name"],
        column_name="Object",
    )
    use_samaccountname: bool = Param(
        description="Use sAMAccountName instead of distinguishedName",
        required=False,
        default=False,
    )
    new_name: str = Param(
        description="New name for the object",
        required=True,
        primary=True,
        cef_types=["user name"],
        column_name="New Name",
    )


class RenameObjectOutput(ActionOutput):
    status: str = OutputField(
        column_name="Status", example_values=["success", "failed"]
    )
    message: str | None = None


class RenameObjectSummary(ActionOutput):
    summary: str | None = None


@app.action(
    description="Rename the object",
    verbose="When 'use_samaccountname' is false, the 'object' parameter should include the distinguishedName. Otherwise, "
    "use the sAMAccountName. For the 'new_name' parameter, append the new name to the attribute name. For example, to "
    "rename a user, use 'cn=New_user_name'; for an OU, use 'ou=New_OU_name'.",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=RenameObjectSummary,
)
def rename_object(
    params: RenameObjectParams, soar: SOARClient, asset: Asset
) -> RenameObjectOutput:
    helper = LdapHelper(asset)
    obj = params.object.lower()

    if params.use_samaccountname:
        resolved = helper.sam_to_dn([obj])
        if resolved[obj] is False:
            raise ValueError("No users found")
        obj = resolved[obj]

    helper.rename_object(obj, params.new_name)

    soar.set_summary(RenameObjectSummary(summary="Successfully Renamed Object"))
    soar.set_message("Summary: Successfully Renamed Object")
    return RenameObjectOutput(status="success", message="Success")
