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


class AccountStatusParams(Params):
    use_samaccountname: bool = Param(
        description="Specify sAMAccountName instead of distinguishedName",
        required=False,
        default=False,
    )
    user: str = Param(
        description="Specify the user to enable/disable. If 'use samaccountname' is false, then this must be the user's distinguishedName",
        required=True,
        primary=True,
        cef_types=["user name"],
        column_name="Target User",
    )


class AccountStatusOutput(ActionOutput):
    starting_status: str | None = OutputField(column_name="Started Status")
    user_dn: str | None = None


class AccountStatusSummary(ActionOutput):
    account_status: str | None = OutputField(column_name="Current Status")


def _set_account_status(
    params: AccountStatusParams, soar: SOARClient, asset: Asset, disable: bool
) -> AccountStatusOutput:
    from ..helper import LdapHelper

    helper = LdapHelper(asset)
    user = params.user.lower()

    if params.use_samaccountname:
        resolved = helper.sam_to_dn([user])
        if resolved[user] is False:
            raise ValueError("No users found")
        user = resolved[user]

    starting_status = helper.set_account_status(user, disable=disable)
    account_status = "disabled" if disable else "enabled"

    soar.set_summary(AccountStatusSummary(account_status=account_status))
    soar.set_message(f"Account status: {account_status}")
    return AccountStatusOutput(user_dn=user, starting_status=starting_status)


@app.action(
    description="Disables an Active Directory account",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=AccountStatusSummary,
)
def disable_account(
    params: AccountStatusParams, soar: SOARClient, asset: Asset
) -> AccountStatusOutput:
    return _set_account_status(params, soar, asset, disable=True)
