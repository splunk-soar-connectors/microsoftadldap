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


class UnlockAccountParams(Params):
    use_samaccountname: bool = Param(
        description="Use sAMAccountName for user instead of distinguishedName(s)",
        required=False,
        default=False,
    )
    user: str = Param(
        description="Specify the user to unlock. If 'use samaccountname' is false, then this must be the user's distinguishedName",
        required=True,
        primary=True,
        cef_types=["user name"],
    )


class UnlockAccountOutput(ActionOutput):
    user_dn: str | None = OutputField(column_name="User Dn")
    samaccountname: str | None = OutputField(column_name="SAM Account Name")
    unlocked: bool | None = OutputField(column_name="Unlocked")


class UnlockAccountSummary(ActionOutput):
    unlocked: bool | None = None


@app.action(
    description="Unlocks a locked Active Directory account",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=UnlockAccountSummary,
)
def unlock_account(
    params: UnlockAccountParams, soar: SOARClient, asset: Asset
) -> UnlockAccountOutput:
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

    helper.unlock_account(user)
    data["unlocked"] = True

    soar.set_summary(UnlockAccountSummary(unlocked=True))
    soar.set_message("Unlocked: True")
    return UnlockAccountOutput(**data)
