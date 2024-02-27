import ast
import importlib.resources
from typing import NamedTuple

from beancount.core.data import Amount, Balance, D
from playwright._impl._api_structures import Cookie
from ubank import UbankClient

from .common import queensland_now


def get_balances_and_cookie(
    username: str, password: str, cookie: Cookie, account_prefix="Assets:UBank:"
) -> tuple[list[NamedTuple], Cookie]:
    """Returns a tuple containing ubank account balance directives and trusted cookie.

    :param username: ubank username.
    :param password: ubank password.
    :param cookie: ubank trusted cookie.
    :param account_prefix: Prefix account names with this string.

    :return: List of Balance directives.
    """
    now = queensland_now()

    # Get ubank account balances and trusted cookie.
    with UbankClient() as ubank_client:
        ubank_client.log_in_with_trusted_cookie(username, password, cookie)
        accounts = ubank_client.get_accounts()
        trusted_cookie = ubank_client.get_trusted_cookie()

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

    return (
        [
            Balance(
                meta={},
                date=now.date(),
                account=f"{account_prefix}{account['metadata']['ubankOne']['productName']}",
                amount=Amount(D(account["balance"]["available"]), "AUD"),
                tolerance=None,
                diff_amount=None,
            )  # type: ignore
            for account in accounts["linkedBanks"][0]["accounts"]
        ],
        trusted_cookie,
    )


class CookieTransformer(ast.NodeTransformer):
    """Replaces trusted cookie dictionary in AST."""

    def __init__(self, replacement_cookie: dict) -> None:
        """Initialises this instance with replacement trusted cookie."""
        self.replacement_cookie = replacement_cookie

    def visit_Assign(self, node: ast.Assign):
        """Replaces Assign node's value if node is `cookie` assignment."""
        if isinstance(node.value, ast.Dict) and node.targets[0].id == "cookie":
            node.value = ast.parse(str(self.replacement_cookie), mode="eval").body
        return node


def change_cookie(
    replacement_cookie: dict,
    traversable=importlib.resources.files().joinpath("secrets.py"),
):
    """Overwrites secrets module with replacement ubank cookie."""
    module = ast.parse(traversable.read_text())
    transformed_node = CookieTransformer(replacement_cookie).visit(module)

    with (
        importlib.resources.as_file(traversable) as resource,
        resource.open("w") as file,
    ):
        file.write(ast.unparse(transformed_node))
