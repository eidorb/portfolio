import pyotp
import pytest

import private
from portfolio import selfwealth

from tests import SecretString


@pytest.fixture
def email():
    return SecretString(private.selfwealth.email)


@pytest.fixture
def password():
    return SecretString(private.selfwealth.password)


@pytest.fixture
def otp():
    """Generates OTP from TOTP key."""
    return SecretString(pyotp.TOTP(private.selfwealth.totp_key).now())


def test_get_balances(email, password, otp):
    """Tests Balance directive is returned with expected currency code."""
    balances = selfwealth.get_balances(email, password, otp)
    currencies = set(balance.amount.currency for balance in balances)
    assert "USD" in currencies
    assert "AUD" in currencies
