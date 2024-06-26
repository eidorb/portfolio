import typing

import requests
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def ping(token: str) -> requests.Response:
    """Pings Up API.

    :param token: Up API token.

    :return: Ping response.
    """
    return requests.get(
        url="https://api.up.com.au/api/v1/util/ping",
        headers={"Authorization": f"Bearer {token}"},
    )


def get_balances(token: str, account_prefix="Assets:Up:") -> list[typing.NamedTuple]:
    """Returns Up account balances as Beancount Balance directives.

    Calls Up API `/accounts` endpoint (see https://developer.up.com.au/#accounts)
    and converts JSON reponse into Beancount `Balance` objects.

    :param token: Up API token.
    :param account_prefix: Up API token.

    :return: List of Balance directives.
    """
    now = queensland_now()
    response = requests.get(
        url="https://api.up.com.au/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    return [
        Balance(
            meta={},
            date=now.date(),
            account=f"{account_prefix}{account['attributes']['displayName']}",
            amount=Amount(
                D(account["attributes"]["balance"]["value"]),
                account["attributes"]["balance"]["currencyCode"],
            ),
            tolerance=None,
            diff_amount=None,
        )  # type: ignore
        for account in response.json()["data"]
        if account["attributes"]["accountType"] == "TRANSACTIONAL"
    ]
