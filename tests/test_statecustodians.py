import pytest

from portfolio import secrets, statecustodians

from tests import SecretString


@pytest.fixture
def customer_id():
    return SecretString(secrets.statecustodians.customer_id)


@pytest.fixture
def password():
    return SecretString(secrets.statecustodians.password)


def test_get_balances(customer_id, password):
    """Tests Balance directive is returned with expected portions."""
    balances = statecustodians.get_balances(customer_id, password)
    portions = [balance.account.split(":")[-1] for balance in balances]
    assert "A" in portions
    assert "O" in portions
    for balance in balances:
        if balance.account.startswith("Assets"):
            # Asset accounts should be positive.
            assert balance.amount.number > 0
        else:
            # Liability accounts should be negative.
            assert balance.amount.number < 0
