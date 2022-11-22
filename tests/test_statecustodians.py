import pytest
from datetime import datetime

from portfolio import secrets, statecustodians

from tests import SecretString


@pytest.fixture
def user_id():
    return SecretString(secrets.statecustodians.user_id)


@pytest.fixture
def password():
    return SecretString(secrets.statecustodians.password)


def test_parse_content(text_content):
    """Tests parse_content() returns expected values."""
    offset, portion_a, portion_b = statecustodians.parse_content(text_content)
    assert offset.id == "O"
    assert offset.balance == "$2,222.22"
    assert portion_a.id == "A"
    assert portion_a.balance == "-$3,333.33"
    assert portion_b.id == "B"
    assert portion_b.balance == "-$4,444.44"


def test_convert_portions():
    """Tests convert_portions() returns expected values."""
    portions = (
        statecustodians.Portion(id="O", balance="$2,222.22"),
        statecustodians.Portion(id="A", balance="-$3,333.33"),
    )
    balance_o, balance_a = statecustodians.convert_portions(portions, datetime.now())
    # Offset should be an asset.
    assert balance_o.account.startswith("Assets")
    # Others should be liabilities.
    assert balance_a.account.startswith("Liabilities")
    # Asset accounts should be positive.
    assert balance_o.amount.number > 0
    # Liability accounts should be negative.
    assert balance_a.amount.number < 0


def test_get_balances(user_id, password):
    """Tests Balance directive is returned with expected portions."""
    offset, portion_a, portion_b = statecustodians.get_balances(user_id, password)
    # Asset accounts should be positive.
    assert offset.amount.number > 0
    # Liability accounts should be negative.
    assert portion_a.amount.number < 0
    assert portion_b.amount.number < 0


@pytest.fixture
def text_content():
    return """





Home loan


012345-678901
















Portion O


																	BSB: 123456 ACC: 111111111


																	BSB: 123456 ACC: 111111111





																	Available redraw


																	 $1.11


																	Account balance


																	$2,222.22











Portion A


																	BSB: 123456 ACC: 222222222


																	BSB: 123456 ACC: 222222222





																	Available redraw


																	 $1.11


																	Account balance


																	-$3,333.33











Portion B


																	BSB: 123456 ACC: 333333333


																	BSB: 123456 ACC: 333333333





																	Available redraw


																	 $1.11


																	Account balance


																	-$4,444.44






											"""
