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
from soar_sdk.params import Param

from ..app import Asset, app
from .add_group_members import (
    GroupMemberOutput,
    GroupMembersParams,
    GroupMembersSummary,
    _modify_group_members,
)


class RemoveGroupMembersParams(GroupMembersParams):
    use_samaccountname: bool = Param(
        description="Specify members AND groups as sAMAccountName(s) instead of distinguishedName(s)",
        required=False,
        default=False,
    )
    groups: str = Param(
        description="Semi-colon (';') separated list of groups from which the members will be removed. If 'use samaccountname' is false, then these must be distinguishedName(s)",
        required=True,
    )


@app.action(
    description="Removes one or more Active Directory objects from one or more groups",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=GroupMembersSummary,
)
def remove_group_members(
    params: RemoveGroupMembersParams, soar: SOARClient, asset: Asset
) -> list[GroupMemberOutput]:
    return _modify_group_members(params, soar, asset, add=False)
