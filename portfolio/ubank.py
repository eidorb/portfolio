import typing

import requests
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_balances(
    username: str, password: str, account_prefix="Assets:UBank:"
) -> typing.NamedTuple:
    """Returns UBank account balances as Beancount Balance directives.

    :param username: UBank username.
    :param password: UBank password.
    :param account_prefix: Prefix account names with this string.

    :return: List of Balance directives.
    """
    now = queensland_now()

    session = requests.Session()
    session.headers.update({"x-nab-key": "73189799-4b8e-4215-b6aa-5e39e89bf490"})

    # GET this URL to set session cookies.
    session.get(url="https://www.ubank.com.au/content/dam/ubank/mobile/")

    # Authenticate.
    response = session.post(
        "https://www.ubank.com.au/v1/ubank/oauth/token",
        json={
            "client_id": "6937C7F1-F101-BCF1-9370-3FF02D27689E",
            "scope": "openid ubank:ekyc:manage ubank:statements:manage ubank:letters:manage ubank:payees:manage ubank:payment:manage ubank:account:eligibility cards:pin:create ubank:fraud:events",
            "username": username,
            "password": password,
            "grant_type": "password",
        },
    )

    # Extract access token, x-nab-id and x-nab-csid from response.
    access_token = response.json()["access_token"]
    x_nab_id = response.json()["x-nab-id"]
    x_nab_csid = response.headers["csid"]

    # Get account balances.
    response = session.get(
        "https://www.ubank.com.au/v1/ubank/accounts",
        headers={
            "Authorization": access_token,
            "x-nab-id": x_nab_id,
            "x-nab-csid": x_nab_csid,
        },
    )

    # The JSON accounts response has the following structure:
    # {
    #   "accounts": [
    #     {
    #       "productCode": "xxx",
    #       "accountNumber": "xxx",
    #       "productName": "USave",
    #       "productType": "xxx",
    #       "nickname": "xxx",
    #       "availableBalance": "xxx",
    #       "currentBalance": "xxx",
    #       "ownership": "xxx",
    #       "visible": true,
    #       "status": "xxx",
    #       "isEligibleForBonusRate": true,
    #       "bonusRate": "xxx",
    #       "accountOpeningDate": "xxx",
    #       "id": "xxx",
    #       "entireAccountId": "xxx",
    #       "legacyToken": "xxx"
    #     },
    #     {
    #       "productCode": "xxx",
    #       "accountNumber": "xxx",
    #       "productName": "USpend",
    #       "productType": "xxx",
    #       "nickname": "xxx",
    #       "availableBalance": "xxx",
    #       "currentBalance": "xxx",
    #       "ownership": "xxx",
    #       "visible": true,
    #       "status": "xxx",
    #       "isEligibleForBonusRate": false,
    #       "bonusRate": "xxx",
    #       "accountOpeningDate": "xxx",
    #       "linkedUsaverAccount": {
    #         "accountNumber": "xxx",
    #         "id": "xxx",
    #         "legacyToken": "xxx"
    #       },
    #       "id": "xxx",
    #       "entireAccountId": "xxx",
    #       "legacyToken": "xxx"
    #     }
    #   ]
    # }

    return [
        Balance(
            meta=dict(time=now.isoformat()),
            date=now.date(),
            account=f"{account_prefix}{account['productName']}",
            amount=Amount(D(account["availableBalance"]), "AUD"),
            tolerance=None,
            diff_amount=None,
        )  # type: ignore
        for account in response.json()["accounts"]
    ]
