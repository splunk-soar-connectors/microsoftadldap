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


class GroupMembersParams(Params):
    use_samaccountname: bool = Param(
        description="Specify members AND groups as sAMAccountName(s) instead of distinguishedName(s) (note: member AND groups will use sAMAccountName if selected)",
        required=False,
        default=False,
    )
    members: str = Param(
        description="Semi-colon (';') separated list of users. If 'use samaccountname' is false, then these must be distinguishedName(s)",
        required=True,
    )
    groups: str = Param(
        description="Semi-colon (';') separated list of groups to which the members will be added. If 'use samaccountname' is false, then these must be distinguishedName(s)",
        required=True,
    )


class GroupMemberOutput(ActionOutput):
    member: str | None = OutputField(column_name="Member")
    function: str | None = OutputField(column_name="Function")
    group: str | None = OutputField(column_name="Group")


class GroupMembersSummary(ActionOutput):
    requested_user_records: int | None = None
    found_user_records: int | None = None


def _resolve_members_and_groups(
    helper, params: GroupMembersParams
) -> tuple[list[str], list[str], GroupMembersSummary | None]:
    members = [i.strip() for i in params.members.split(";")]
    groups = [i.strip() for i in params.groups.split(";")]

    if not params.use_samaccountname:
        return members, groups, None

    member_map = helper.sam_to_dn([i.lower() for i in members])
    group_map = helper.sam_to_dn([i.lower() for i in groups])

    member_nf = [k for k, v in member_map.items() if v is False]
    group_nf = [k for k, v in group_map.items() if v is False]
    if member_nf or group_nf:
        unresolved = []
        if member_nf:
            unresolved.append(f"members: {', '.join(member_nf)}")
        if group_nf:
            unresolved.append(f"groups: {', '.join(group_nf)}")
        raise ValueError(
            f"Unable to resolve all requested directory objects ({'; '.join(unresolved)})"
        )

    resolved_members = list(member_map.values())
    resolved_groups = list(group_map.values())
    if not resolved_members or not resolved_groups:
        raise ValueError("Not enough groups or members")

    summary = GroupMembersSummary(
        requested_user_records=len(members), found_user_records=len(resolved_members)
    )
    return resolved_members, resolved_groups, summary


def _modify_group_members(
    params: GroupMembersParams, soar: SOARClient, asset: Asset, add: bool
) -> list[GroupMemberOutput]:
    helper = LdapHelper(asset)
    members, groups, summary = _resolve_members_and_groups(helper, params)

    helper.modify_group_members(members, groups, add=add)

    function = "added" if add else "removed"
    if summary is not None:
        soar.set_summary(summary)
    soar.set_message(f"{function} member(s) {'to' if add else 'from'} group(s)")
    return [
        GroupMemberOutput(member=m, function=function, group=g)
        for m in members
        for g in groups
    ]


@app.action(
    description="Adds one or more Active Directory objects to one or more groups",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=GroupMembersSummary,
)
def add_group_members(
    params: GroupMembersParams, soar: SOARClient, asset: Asset
) -> list[GroupMemberOutput]:
    return _modify_group_members(params, soar, asset, add=True)
