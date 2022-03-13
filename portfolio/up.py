import datetime

from beancount.core.data import Amount, Balance, Entries, D
import requests


def ping(token) -> requests.Response:
    """Returns response of ping to Up API."""
    return requests.get(
        url="https://api.up.com.au/api/v1/util/ping",
        headers={"Authorization": f"Bearer {token}"},
    )


def accounts(token) -> Entries:
    """Returns response of call to Up API /accounts endpoint.

    See https://developer.up.com.au/#accounts."""
    response = requests.get(
        url="https://api.up.com.au/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    return [
        Balance(
            meta=dict(),
            date=datetime.date.today(),
            account=f"Up:{account['attributes']['displayName']}",
            amount=Amount(
                D(account["attributes"]["balance"]["value"]),
                account["attributes"]["balance"]["currencyCode"],
            ),
            tolerance=None,
            diff_amount=None,
        )
        for account in response.json()["data"]
    ]


def statement(response) -> Beancount:
    """Turns an accounts response into a beancount transaction object."""
