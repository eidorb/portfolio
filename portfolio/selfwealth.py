import mechanicalsoup

import typing

from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_balances(
    email: str, password: str, otp: str, account_prefix="Assets:SelfWealth:"
) -> list[typing.NamedTuple]:
    """Returns SelfWealth account balances as Beancount Balance directives.

    SelfWealth assets are represented as separate accounts. That is, one account
    for each security and cash balance.

    :param email: SelfWealth email address.
    :param password: Selfwealth password.
    :param otp: Selfwealth one-time pin.
    :param account_prefix: Prefix account names with this string.

    :return: List of Balance directives.
    """
    browser = mechanicalsoup.StatefulBrowser()
    browser.open("https://secure.selfwealth.com.au/Account/Login")

    # First, authenticate with email and password credentials.
    browser.post(
        "https://secure.selfwealth.com.au/api/login",
        json={
            "Email": email,
            "Password": password,
            "RecaptchaResponseKey": None,
        },
        headers={
            "X-XSRF-TOKEN": browser.page.find("input", attrs=dict(name="__aft"))[
                "value"
            ]
        },
    ).raise_for_status()

    # Then, authenticate with one-time pin.
    browser.post(
        "https://secure.selfwealth.com.au/api/loginTwoFactor",
        json={"TwoFactorCode": otp},
        headers={
            "X-XSRF-TOKEN": browser.page.find("input", attrs=dict(name="__aft"))[
                "value"
            ],
        },
    ).raise_for_status()

    # Open the dashboard to get portfolio ID.
    browser.open("https://secure.selfwealth.com.au").raise_for_status()
    portfolio_id = browser.page.find("body")["data-id"]

    now = queensland_now()
    balances = []

    # The getholdingsfortrading endpoint returns an object like this:
    #
    #     {'Holdings': [
    #       {'Id': 0,
    #        'Code': 'CASH',
    #        'TRCode': None,
    #        'Name': 'Cash',
    #        'ShortName': 'Cash',
    #        'AvailableUnits': 100.00,
    #        'TotalUnits': 100.00,
    #        'Price': 1.0,
    #        'Value': 100.00,
    #        'NetChange': 0.0,
    #        'PercentageChange': 0.0,
    #        'AveragePrice': None,
    #        'Trend': '',
    #        'Messages': 0,
    #        'RecogniaValue': 0.0,
    #        'RecogniaType': -99,
    #        'SectorId': 0,
    #        'Sector': 'Sector Not Applicable',
    #        'Weight': 0.0,
    #        'IsCash': True,
    #        'ProductWeight': 0.0,
    #        'Yield': 0.0,
    #        'PositionByCount': 0,
    #        'PositionByWeight': 0,
    #        'ProductMarketGroupId': 1,
    #        'ULID': None},
    #        ...
    #       ],
    #      'HoldingsCount': 10}
    for holding in browser.get(
        f"https://secure.selfwealth.com.au/api/portfolio/getholdingsfortrading?PortfolioId={portfolio_id}"
    ).json()["Holdings"]:
        # Make it so each holding's code is either a currency code or stock symbol.
        code = holding["Code"]
        if code == "CASH":
            code = "AUD"
        elif code == "US CASH":
            code = "USD"
        balances.append(
            Balance(
                meta=dict(time=now.isoformat()),
                date=now.date(),
                account=f"{account_prefix}{code}",
                amount=Amount(
                    D(str(holding["TotalUnits"])),
                    code,
                ),
                tolerance=None,
                diff_amount=None,
            )
        )

    return balances
