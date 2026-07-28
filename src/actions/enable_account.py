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

from ..app import Asset, app
from .disable_account import (
    AccountStatusOutput,
    AccountStatusParams,
    AccountStatusSummary,
    _set_account_status,
)


@app.action(
    description="Enables a disabled Active Directory account",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=AccountStatusSummary,
)
def enable_account(
    params: AccountStatusParams, soar: SOARClient, asset: Asset
) -> AccountStatusOutput:
    return _set_account_status(params, soar, asset, disable=False)
