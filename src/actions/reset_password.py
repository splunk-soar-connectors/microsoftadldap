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


class ResetPasswordParams(Params):
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
        column_name="Target User",
    )


class ResetPasswordOutput(ActionOutput):
    user_dn: str | None = None
    samaccountname: str | None = None
    reset: bool | None = OutputField(column_name="Password Was Reset")


class ResetPasswordSummary(ActionOutput):
    reset: bool | None = None


@app.action(
    description="Resets the password of a user, requiring the user to change password at next login",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=ResetPasswordSummary,
)
def reset_password(
    params: ResetPasswordParams, soar: SOARClient, asset: Asset
) -> ResetPasswordOutput:
    from ..helper import LdapHelper

    helper = LdapHelper(asset)
    user = params.user.lower()
    data = {"user_dn": user}

    if params.use_samaccountname:
        resolved = helper.sam_to_dn([user])
        if resolved[user] is False:
            raise ValueError("No users found")
        data["user_dn"] = resolved[user]
        data["samaccountname"] = user
        user = resolved[user]

    if not helper.reset_password(user):
        raise ValueError("Failed to reset password")

    data["reset"] = True

    soar.set_summary(ResetPasswordSummary(reset=True))
    soar.set_message("Reset: True")
    return ResetPasswordOutput(**data)
