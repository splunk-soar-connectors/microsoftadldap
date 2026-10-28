# Copyright (c) 2026 Splunk Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

"""Exercise password handling through the released SDK without contacting LDAP."""

import json

import pytest

from src.app import app


USER_DN = "cn=lab user,dc=example,dc=com"
PLAINTEXT = "test-password"
PASSWORD_ENVELOPE = "test-envelope-password"  # pragma: allowlist secret
CONFIRM_ENVELOPE = "test-envelope-confirmation"
ASSET_ENVELOPE = "test-envelope-asset"
DEC_KEY = "test-decryption-key"


def make_input(password, confirmation, encryption=True):
    payload = {
        "asset_id": "1",
        "action": "set password",
        "identifier": "set_password",
        "dec_key": DEC_KEY,
        "config": {
            "app_version": "3.0.2",
            "directory": ".",
            "main_module": "src.app:app",
            "server": "ad.example.invalid",
            "username": "lab-only",
            "password": ASSET_ENVELOPE,
        },
        "parameters": [
            {
                "user": USER_DN,
                "password": password,
                "confirm_password": confirmation,
            }
        ],
    }
    if encryption is not None:
        payload["enable_action_parameter_encryption"] = encryption
    return json.dumps(payload)


def run_action(payload):
    previous = len(app.actions_manager.get_action_results())
    app.handle(payload)
    results = app.actions_manager.get_action_results()
    assert len(results) == previous + 1
    return results[-1]


@pytest.fixture
def dependencies(mocker):
    # Both SDK paths use the same platform backend object. Mock only its I/O;
    # leave SDK parsing, dispatch, parameter decryption, and the action intact.
    values = {
        ASSET_ENVELOPE: "lab-bind-password",
        PASSWORD_ENVELOPE: PLAINTEXT,
        CONFIRM_ENVELOPE: PLAINTEXT,
    }
    decrypt = mocker.patch(
        "soar_sdk.app.platform_encryption_backend.decrypt",
        side_effect=lambda value, key: values[value],
    )
    helper = mocker.patch("src.actions.set_password.LdapHelper")
    helper.return_value.set_password.return_value = True
    return values, decrypt, helper


def test_equal_encrypted_passwords_reach_ldap_as_plaintext(dependencies):
    _, decrypt, helper = dependencies
    result = run_action(make_input(PASSWORD_ENVELOPE, CONFIRM_ENVELOPE))

    assert result.get_status()
    helper.return_value.set_password.assert_called_once_with(USER_DN, PLAINTEXT)
    decrypt.assert_any_call(PASSWORD_ENVELOPE, DEC_KEY)
    decrypt.assert_any_call(CONFIRM_ENVELOPE, DEC_KEY)
    decrypt.assert_any_call(ASSET_ENVELOPE, DEC_KEY)
    assert decrypt.call_count == 3


def test_unequal_decrypted_passwords_are_rejected(dependencies):
    values, decrypt, helper = dependencies
    values[CONFIRM_ENVELOPE] = "different-test-password"
    result = run_action(make_input(PASSWORD_ENVELOPE, CONFIRM_ENVELOPE))

    assert not result.get_status()
    assert "Passwords do not match" in result.get_message()
    helper.assert_not_called()
    decrypt.assert_any_call(CONFIRM_ENVELOPE, DEC_KEY)


@pytest.mark.parametrize("encryption", [False, None], ids=["disabled", "omitted"])
def test_plaintext_passwords_work_without_encryption_flag(dependencies, encryption):
    _, decrypt, helper = dependencies
    result = run_action(make_input(PLAINTEXT, PLAINTEXT, encryption))

    assert result.get_status()
    helper.return_value.set_password.assert_called_once_with(USER_DN, PLAINTEXT)
    decrypt.assert_called_once_with(ASSET_ENVELOPE, DEC_KEY)


def test_encrypted_passwords_with_disabled_flag_reproduce_original_failure(
    dependencies,
):
    _, decrypt, helper = dependencies
    result = run_action(make_input(PASSWORD_ENVELOPE, CONFIRM_ENVELOPE, False))

    assert not result.get_status()
    assert "Passwords do not match" in result.get_message()
    helper.assert_not_called()
    decrypt.assert_called_once_with(ASSET_ENVELOPE, DEC_KEY)
