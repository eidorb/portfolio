import typing

import requests
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_balance(api_key: str, addresses: str, account: str) -> typing.NamedTuple:
    """Returns total balance of Bitcoin addresses.

    :param api_key: Blockonomics API key.
    :param addresses: Space-separated addresses (or master public key).
    :param account: Name of Beancount account.

    :return: Beancount Balance directive.
    """
    now = queensland_now()
    response = requests.post(
        url="https://www.blockonomics.co/api/balance",
        json={"addr": addresses},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return Balance(
        meta=dict(time=now.isoformat()),
        date=now.date(),
        account=account,
        amount=Amount(
            # Sum the confirmed satoshis, and convert to BTC.
            D(sum(balance["confirmed"] for balance in response.json()["response"]))
            / 100000000,
            "BTC",
        ),
        tolerance=None,
        diff_amount=None,
    )  # type: ignore
