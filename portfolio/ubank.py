import typing

from beancount.core.data import Amount, Balance, D
from playwright._impl._api_structures import Cookie
from ubank import UbankClient

from .common import queensland_now


def get_balances(
    username: str, password: str, cookie: Cookie, account_prefix="Assets:UBank:"
) -> typing.NamedTuple:
    """Returns UBank account balances as Beancount Balance directives.

    :param username: UBank username.
    :param password: UBank password.
    :param cookie: UBank trusted cookie.
    :param account_prefix: Prefix account names with this string.

    :return: List of Balance directives.
    """
    now = queensland_now()

    # Get ubank eaccount balances.
    with UbankClient() as ubank_client:
        ubank_client.log_in_with_trusted_cookie(username, password, cookie)
        accounts = ubank_client.get_accounts()

    # The accounts object has the following structure:
    # {
    #     "linkedBanks": [
    #         {
    #             "bankId": 1,
    #             "shortBankName": "ubank",
    #             "accounts": [
    #                 {
    #                     "id": "...",
    #                     "number": "...",
    #                     "bsb": "...",
    #                     "label": "...",
    #                     "nickname": "...",
    #                     "type": "TRANSACTION",
    #                     "balance": {"currency": "AUD", "current": ..., "available": ...},
    #                     "status": "Active",
    #                     "lastBalanceRefresh": "...",
    #                     "openDate": "...",
    #                     "isJointAccount": ...,
    #                     "metadata": {
    #                         "ubankOne": {
    #                             "number": "...",
    #                             "bsb": "...",
    #                             "closedDate": ...,
    #                             "productName": "USpend",
    #                         }
    #                     },
    #                 },
    #                 {
    #                     "id": "...",
    #                     "number": "...",
    #                     "bsb": "...",
    #                     "label": "...",
    #                     "nickname": "...",
    #                     "type": "SAVINGS",
    #                     "balance": {"currency": "AUD", "current": ..., "available": ...},
    #                     "status": "Active",
    #                     "lastBalanceRefresh": "...",
    #                     "openDate": "...",
    #                     "creditInterest": {
    #                         "accountBaseRate": ...,
    #                         "bonusInterestRate": ...,
    #                         "activatedBonusRate": ...,
    #                         "interestAccrued": ...,
    #                         "interestPaidYtd": ...,
    #                         "interestPaidLastYear": ...,
    #                     },
    #                     "isJointAccount": False,
    #                     "metadata": {
    #                         "ubankOne": {
    #                             "number": "...",
    #                             "bsb": "...",
    #                             "closedDate": ...,
    #                             "productName": "USave",
    #                         }
    #                     },
    #                 },
    #             ],
    #         }
    #     ]
    # }

    return [
        Balance(
            meta={},
            date=now.date(),
            account=f"{account_prefix}{account['metadata']['ubankOne']['productName']}",
            amount=Amount(D(account["balance"]["available"]), "AUD"),
            tolerance=None,
            diff_amount=None,
        )  # type: ignore
        for account in accounts["linkedBanks"][0]["accounts"]
    ]
