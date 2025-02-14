from typing import NamedTuple

from beancount.core.data import Amount, Balance, D
from ubank import Client, Passkey

from .common import queensland_now


def get_balances(passkey: Passkey, account_prefix="Assets:UBank:") -> list[NamedTuple]:
    """Returns a tuple containing ubank account balance directives and trusted cookie.

    :param username: ubank enrolled device
    :param account_prefix: Prefix account names with this string

    :return: List of Balance directives
    """
    now = queensland_now()

    with Client(passkey) as client:
        return [
            Balance(
                meta={},
                date=now.date(),
                account=f"{account_prefix}{account.nickname}",
                amount=Amount(
                    D(str(account.balance.available)), account.balance.currency
                ),
                tolerance=None,
                diff_amount=None,
            )  # type: ignore
            for account in client.get_linked_banks().linkedBanks[0].accounts
        ]
