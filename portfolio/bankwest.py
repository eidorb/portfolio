import typing

import requests
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_balance(
    pan: str, password: str, account_prefix="Liabilities:Bankwest:"
) -> typing.NamedTuple:
    """Returns Bankwest balance as Beancount Balance.

    :param pan: Bankwest personal access number.
    :param password: Bankwest password.
    :param account_prefix: Prefix account names with this string.

    :return: Balance directive.
    """
    now = queensland_now()

    session = requests.Session()
    session.headers.update({"User-Agent": "BankwestApp/5.6.0-24964 (iPhone; iOS/14.4)"})

    # Authenticate.
    response = session.post(
        "https://api.ibs.bankwest.com.au/login/authenticate",
        json={"Pan": pan, "SecureCode": password, "TransactionData": None},
    )

    # Get banking summary.
    response = session.get(
        "https://api.ibs.bankwest.com.au/user/summary",
    )

    account = response.json()["Accounts"][0]

    # Make title case without spaces.
    account_name = "".join(word.title() for word in account["AccountNickName"].split())

    return Balance(
        meta={},
        date=now.date(),
        account=f"""{account_prefix}{account_name}""",
        amount=Amount(D(str(account["AccountCurrentBalance"])), "AUD"),
        tolerance=None,
        diff_amount=None,
    )  # type: ignore
