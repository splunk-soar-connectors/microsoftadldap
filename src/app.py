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
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset

from .helper import LdapHelper


class Asset(BaseAsset):
    server: str = AssetField(
        description="The Active Directory Server hostname, IP, or VIP for binding"
    )
    username: str = AssetField(description="The username with which to bind to LDAP")
    password: str = AssetField(
        description="The password for the binding user", sensitive=True
    )
    force_ssl: bool | None = AssetField(
        description="Force the use of SSL protocol. Note that some actions are not possible without secure binding!",
        default=True,
    )
    validate_ssl_cert: bool | None = AssetField(
        description="Select if you want to validate the LDAP SSL certificate"
    )
    ssl_port: int = AssetField(
        description="The port to bind for SSL (default 636)", default=636
    )


app = App(
    name="AD LDAP",
    app_type="identity management",
    logo="logo_microsoft.svg",
    logo_dark="logo_microsoft_dark.svg",
    product_vendor="Splunk",
    product_name="Active Directory LDAP",
    publisher="Splunk",
    appid="a5730e5d-a396-4695-92c2-35ff391aaf45",
    fips_compliant=True,
    min_phantom_version="8.6.0",
    asset_cls=Asset,
)


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    LdapHelper(asset).bind()


from .actions.get_attributes import get_attributes, render_display_attributes
from .actions.run_query import render_display_attributes as render_run_query
from .actions.run_query import run_query


app.register_action(
    run_query,
    description="Query Active Directory LDAP",
    action_type="investigate",
    verbose="This action flexibly supports querying Active Directory using LDAP syntax.",
    view_handler=render_run_query,
    view_template="display_attributes.html",
    read_only=True,
)

app.register_action(
    get_attributes,
    description="Get attributes of various principals",
    action_type="investigate",
    verbose="This action takes any number of principals (sAMAccountName, distinguishedName, or userprincipalname) "
    "and returns requested attributes. Separate with semi-colon (';').",
    view_handler=render_display_attributes,
    view_template="display_attributes.html",
    read_only=True,
)


if __name__ == "__main__":
    app.cli()
