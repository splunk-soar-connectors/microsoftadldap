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


class SetPasswordParams(Params):
    use_samaccountname: bool = Param(
        description="Specify sAMAccountName instead of distinguishedName",
        required=False,
        default=False,
    )
    user: str = Param(
        description="Specify the user whose password will be set. If 'use samaccountname' is false, then this must be the user's distinguishedName",
        required=True,
        primary=True,
        cef_types=["user name"],
        column_name="Target User",
    )
    password: str = Param(description="New password", required=True, sensitive=True)
    confirm_password: str = Param(
        description="Re-type the password", required=True, sensitive=True
    )


class SetPasswordOutput(ActionOutput):
    pass


class SetPasswordSummary(ActionOutput):
    set: bool | None = OutputField(column_name="Password Was Set")


@app.action(
    description="Set a user's password",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=SetPasswordSummary,
)
def set_password(
    params: SetPasswordParams, soar: SOARClient, asset: Asset
) -> SetPasswordOutput:
    from ..helper import LdapHelper

    if params.password != params.confirm_password:
        raise ValueError("Passwords do not match")

    helper = LdapHelper(asset)
    user = params.user.lower()

    if params.use_samaccountname:
        resolved = helper.sam_to_dn([user])
        if resolved[user] is False:
            raise ValueError("No users found")
        user = resolved[user]

    try:
        set_ok = helper.set_password(user, params.password)
    except Exception as e:
        raise Exception(
            f"{e!s}. Also, please make sure that the account in asset has permissions to Set Password "
            "and password meets complexity requirements"
        ) from e

    if not set_ok:
        raise ValueError("Failed to set password")

    soar.set_summary(SetPasswordSummary(set=True))
    soar.set_message("Set: True")
    return SetPasswordOutput()
