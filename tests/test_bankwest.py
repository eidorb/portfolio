import pytest

from portfolio import secrets, bankwest

from tests import SecretString


@pytest.fixture
def pan():
    return SecretString(secrets.bankwest.pan)


@pytest.fixture
def password():
    return SecretString(secrets.bankwest.password)


def test_get_balance(pan, password):
    """Tests Balance directive is returned with expected accounts."""
    balance = bankwest.get_balance(pan, password)
    assert balance.account.endswith("m")
