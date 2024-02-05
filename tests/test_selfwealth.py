import pyotp
import pytest

from portfolio import secrets, selfwealth

from tests import SecretString


@pytest.fixture
def email():
    return SecretString(secrets.selfwealth.email)


@pytest.fixture
def password():
    return SecretString(secrets.selfwealth.password)


@pytest.fixture
def otp():
    """Generates OTP from TOTP key."""
    return SecretString(pyotp.TOTP(secrets.selfwealth.totp_key).now())


def test_get_balances(email, password, otp):
    """Tests Balance directive is returned with expected currency code."""
    balances = selfwealth.get_balances(email, password, otp)
    currencies = set(balance.amount.currency for balance in balances)
    assert "USD" in currencies
    assert "AUD" in currencies
