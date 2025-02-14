import io

from ubank import Passkey

from portfolio import secrets
from portfolio.ubank import get_balances


def test_get_balances():
    """Tests Balance directive is returned with expected accounts."""
    passkey = Passkey.load(io.BytesIO(secrets.ubank.passkey))

    balances = get_balances(passkey)
    accounts = [balance.account.split(":")[-1] for balance in balances]
    assert "USave" in accounts
    assert "USpend" in accounts
