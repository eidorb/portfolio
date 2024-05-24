import json
from typing import NamedTuple

import boto3
import ubank
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_device(parameter_name: str = "/portfolio/ubank-device") -> ubank.Device:
    """Returns ubank enrolled device from AWS Parameter Store."""
    return ubank.Device(
        **json.loads(
            # Retrieve JSON string from decrypted parameter value.
            boto3.client("ssm", region_name="us-east-1").get_parameter(
                Name=parameter_name, WithDecryption=True
            )["Parameter"]["Value"]
        )
    )


def save_device(
    device: ubank.Device, parameter_name: str = "/portfolio/ubank-device"
) -> dict[str, str]:
    """Saves ubank device credentials to AWS Parameter Store."""
    return boto3.client("ssm", region_name="us-east-1").put_parameter(
        Name=parameter_name,
        Value=device.dumps(),
        Type="SecureString",
        Overwrite=True,
    )


def get_balances(
    device: ubank.Device, account_prefix="Assets:UBank:"
) -> list[NamedTuple]:
    """Returns a tuple containing ubank account balance directives and trusted cookie.

    :param username: ubank enrolled device
    :param account_prefix: Prefix account names with this string

    :return: List of Balance directives
    """
    now = queensland_now()

    # Get ubank account balances and trusted cookie.
    with ubank.Client(device) as client:
        # Update stored device credentials.
        save_device(client.device)
        # The accounts/summary object has the following structure:
        # {
        #   "linkedBanks": [
        #     {
        #       "bankId": 1,
        #       "shortBankName": "ubank",
        #       "accounts": [
        #         {
        #           "label": "Spend account",
        #           "type": "TRANSACTION",
        #           "balance": {
        #             "currency": "AUD",
        #             "current": 1000,
        #             "available": 1000
        #           },
        #           "status": "Active",
        #           "id": "695db516-b0e2-4807-baca-77314a6257ce",
        #           "nickname": "Spend account",
        #           "number": "00000000",
        #           "bsb": "000000",
        #           "lastBalanceRefresh": "2024-05-22T06:35:11.374Z",
        #           "openDate": "2023-03-13T17:11:00.000Z",
        #           "isJointAccount": false
        #         },
        #         {
        #           "label": "Save account",
        #           "type": "SAVINGS",
        #           "balance": {
        #             "currency": "AUD",
        #             "current": 1649.44,
        #             "available": 1649.44
        #           },
        #           "status": "Active",
        #           "id": "5bad6edf-247e-4221-9bfc-e7608f5984cb",
        #           "nickname": "Save account",
        #           "number": "00000000",
        #           "bsb": "000000",
        #           "lastBalanceRefresh": "2024-05-22T06:35:11.374Z",
        #           "openDate": "2023-03-13T17:11:00.000Z",
        #           "isJointAccount": false
        #         }
        #       ]
        #     }
        #   ]
        # }

        return [
            Balance(
                meta={},
                date=now.date(),
                account=f"{account_prefix}{account['nickname']}",
                amount=Amount(D(str(account["balance"]["available"])), "AUD"),
                tolerance=None,
                diff_amount=None,
            )  # type: ignore
            for account in client.get("/app/v1/accounts/summary").json()["linkedBanks"][
                0
            ]["accounts"]
        ]
