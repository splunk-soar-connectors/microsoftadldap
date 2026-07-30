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

import json

from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..app import Asset, app


_READ_ONLY_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}


class AdLdapMakeRequestParams(MakeRequestParams):
    http_method: str = Param(
        description=(
            "The HTTP method for Universal API compatibility. Only the read-only "
            "methods GET, HEAD, and OPTIONS are supported; LDAP is queried via a "
            "search. Write methods are rejected."
        ),
        required=True,
        value_list=["GET", "HEAD", "OPTIONS"],
    )
    endpoint: str = Param(
        description=(
            "LDAP search filter in LDAP syntax. Examples: '(objectClass=user)' or "
            "'(sAMAccountName=jdoe)'."
        ),
        required=True,
    )
    query_parameters: str = Param(
        description=(
            "Semi-colon separated list of attributes to return (e.g. "
            "'sAMAccountName;mail'). Defaults to 'sAMAccountName' if not provided."
        ),
        required=False,
    )
    body: str = Param(
        description=(
            "Optional search base in distinguishedName format. If not provided, the "
            "'defaultNamingContext' is used."
        ),
        required=False,
    )
    headers: str = Param(
        description="Not used for LDAP requests. Providing headers will fail the action.",
        required=False,
    )
    verify_ssl: bool | None = Param(
        description=(
            "Not used for LDAP requests; SSL usage is controlled by the asset's "
            "'Force SSL' and 'Validate SSL Cert' settings."
        ),
        required=False,
        default=None,
    )


class AdLdapMakeRequestOutput(ActionOutput):
    status_code: int = OutputField(example_values=[200])
    response_body: str = OutputField(example_values=['{"entries": []}'])


@app.make_request()
def make_request(
    params: AdLdapMakeRequestParams, asset: Asset
) -> AdLdapMakeRequestOutput:
    from ..helper import LdapHelper

    if params.headers:
        raise ActionFailure(
            "headers are not supported for LDAP requests; remove the headers parameter."
        )

    if params.http_method.upper() not in _READ_ONLY_HTTP_METHODS:
        raise ActionFailure(
            f"Unsupported method '{params.http_method}'. LDAP requests are read-only; "
            "use GET, HEAD, or OPTIONS."
        )

    attributes = (
        params.query_parameters.strip() if params.query_parameters else "sAMAccountName"
    )
    search_base = params.body.strip() if params.body else None

    helper = LdapHelper(asset)
    try:
        resp = helper.query(params.endpoint, attributes, search_base=search_base)
    except Exception as e:
        raise ActionFailure(f"Request failed: {e}") from e

    return AdLdapMakeRequestOutput(status_code=200, response_body=json.dumps(resp))
