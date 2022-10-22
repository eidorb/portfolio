import pytest

from portfolio import secrets, ubank

from tests import SecretString


@pytest.fixture
def username():
    return SecretString(secrets.ubank.username)


@pytest.fixture
def password():
    return SecretString(secrets.ubank.password)


@pytest.mark.skip(reason="UBank access no longer works")
def test_get_balances(username, password):
    """Tests Balance directive is returned with expected accounts."""
    balances = ubank.get_balances(username, password)
    accounts = [balance.account.split(":")[-1] for balance in balances]
    assert "USave" in accounts
    assert "USpend" in accounts
