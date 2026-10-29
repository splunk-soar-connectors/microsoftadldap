# Copyright (c) 2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

"""Exercise LDAP initialization with the real ldap3 TLS configuration."""

import ssl
from types import SimpleNamespace

import pytest

from src import helper


@pytest.mark.parametrize(
    ("bundle_exists", "verify"),
    [(False, True), (True, True), (False, False)],
    ids=["system-trust", "platform-bundle", "verification-disabled"],
)
def test_bind_selects_available_trust_without_disabling_verification(
    tmp_path, monkeypatch, mocker, bundle_exists, verify
):
    bundle = tmp_path / "cacerts.pem"
    if bundle_exists:
        bundle.write_text("controlled trust bundle")
    monkeypatch.setattr(helper, "CA_CERTS_PEM", str(bundle))
    connection = mocker.patch.object(helper.ldap3, "Connection")
    connection.return_value.bind.return_value = True
    asset = SimpleNamespace(
        server="ad.example.invalid",
        username="fixture-user",
        password="fixture-password",  # pragma: allowlist secret
        force_ssl=True,
        validate_ssl_cert=verify,
        ssl_port=636,
    )

    ldap = helper.LdapHelper(asset)
    ldap.bind()

    tls = ldap._ldap_server.tls
    assert tls.validate == (ssl.CERT_REQUIRED if verify else ssl.CERT_NONE)
    assert tls.ca_certs_file == (str(bundle) if verify and bundle_exists else None)
    connection.return_value.bind.assert_called_once_with()
