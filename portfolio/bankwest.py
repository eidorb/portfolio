"""Extracts bankwest.com.au account balance.

Run development notebook with

    uvx --with httpx jupyter lab notebooks/bankwest.ipynb
"""

import re
import typing

import httpx
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

    client = httpx.Client(follow_redirects=True)

    # Extract verification token from login page.
    response = client.get("https://ibs.bankwest.com.au/Session/PersonalLogin")
    match = re.search(
        '<input name="__RequestVerificationToken" type="hidden" value="(.+?)" />',
        response.text,
    )
    assert match
    request_verification_token = match.group(1)

    # Initiate authentication.
    response = client.post(
        response.url,
        data={
            "PAN": pan,
            "Password": password,
            "button": "login",
            "targetMedia": "desktop",
            "__RequestVerificationToken": request_verification_token,
            "RememberPan": "false",
        },
    )
    match = re.search("action='(.+?)'", response.text)
    assert match
    action = match.group(1)
    match = re.search("name='code' value='(.+?)'", response.text)
    assert match
    code = match.group(1)
    match = re.search("name='scope' value='(.+?)'", response.text)
    assert match
    scope = match.group(1)
    match = re.search("name='state' value='(.+?)'", response.text)
    assert match
    state = match.group(1)
    match = re.search("name='session_state' value='(.+?)'", response.text)
    assert match
    session_state = match.group(1)

    # Complete authentication.
    response = client.post(
        action,
        data=dict(code=code, scope=scope, state=state, session_state=session_state),
    )

    # Get banking summary.
    response = client.get(
        "https://api.ibs.bankwest.com.au/user/summary",
    )
    client.close()

    account = response.json()["Accounts"][0]

    # Make title case without spaces.
    account_name = "".join(word.title() for word in account["AccountNickName"].split())

    return Balance(
        meta={},
        date=now.date(),
        account=f"{account_prefix}{account_name}",
        amount=Amount(D(str(account["AccountCurrentBalance"])), "AUD"),
        tolerance=None,
        diff_amount=None,
    )  # type: ignore
