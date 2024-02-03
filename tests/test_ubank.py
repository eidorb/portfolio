import pytest

from portfolio import secrets, ubank
from tests import SecretDict, SecretString


@pytest.fixture
def username():
    return SecretString(secrets.ubank.username)


@pytest.fixture
def password():
    return SecretString(secrets.ubank.password)


@pytest.fixture
def cookie():
    return SecretDict(secrets.ubank.cookie)


def test_get_balances(username, password, cookie):
    """Tests Balance directive is returned with expected accounts."""
    balances = ubank.get_balances(username, password, cookie)
    accounts = [balance.account.split(":")[-1] for balance in balances]
    assert "USave" in accounts
    assert "USpend" in accounts
