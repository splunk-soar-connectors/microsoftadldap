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
from ..helper import LdapHelper


class MoveObjectParams(Params):
    object: str = Param(
        description="Specify the distinguishedName to move",
        required=True,
        column_name="Object",
    )
    destination_ou: str = Param(
        description="The distinguishedName of the OU the specified object will move to",
        required=True,
        column_name="Destination",
    )


class MoveObjectOutput(ActionOutput):
    source_object: str | None = None
    destination_container: str | None = None


class MoveObjectSummary(ActionOutput):
    moved: bool | None = None


@app.action(
    description="Moves an entry in Active Directory",
    action_type="generic",
    read_only=False,
    render_as="table",
    summary_type=MoveObjectSummary,
)
def move_object(
    params: MoveObjectParams, soar: SOARClient, asset: Asset
) -> MoveObjectOutput:
    helper = LdapHelper(asset)
    helper.move_object(params.object, params.destination_ou)

    soar.set_summary(MoveObjectSummary(moved=True))
    soar.set_message("Moved: True")
    return MoveObjectOutput(
        source_object=params.object, destination_container=params.destination_ou
    )
