import re
import typing
import uuid

import httpx
from authlib.common.security import generate_token
from authlib.integrations.httpx_client import OAuth2Client
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
    oauth2_client = OAuth2Client(
        client_id="mobile",
        # Client secrets seem to be arbitrary UUIDs 🤷. See authorization header
        # in request to https://auth.selfwealth.com.au/connect/token
        client_secret=str(uuid.uuid4()).upper(),
        scope="mobileAPI offline_access",
        redirect_uri="au.com.selfwealth://callback",
        code_challenge_method="S256",
    )
    # SelfWealth state, code and nonce tokens are 43 characters long.
    state, code_verifier, nonce = (
        generate_token(43),
        generate_token(43),
        generate_token(43),
    )
    authorization_url, _ = oauth2_client.create_authorization_url(
        "https://auth.selfwealth.com.au/connect/authorize",
        state=state,
        code_verifier=code_verifier,
        login_hint=email,
        nonce=nonce,
        prompt="login",
    )

    with httpx.Client() as http_client:
        # Authorization URL redirects to SelfWealth login page.
        response = http_client.get(authorization_url, follow_redirects=True)

        # Parse XSRF token and return URL from login page.
        xsrf_token = re.search(
            r'<input name="__aft" type="hidden" value="(.+?)" />', response.text
        ).group(1)
        return_url = re.search(r"ReturnUrl: '(.+?)',", response.text).group(1)

        # This might check if a captcha needs to be completed. It is not strictly
        # necessary, but we do it to run asserts in order to notice if things change.
        response = http_client.get(
            "https://auth.selfwealth.com.au/api/auth/GetCaptchaStatus",
            params={"key": "Login"},
        )
        assert response.json() is False

        # Authenticate with username and password.
        response = http_client.post(
            "https://auth.selfwealth.com.au/api/login",
            json={
                "email": email,
                "password": password,
                "recaptchaResponseKey": None,
                "isCancel": False,
                "returnUrl": return_url,
            },
            # boot.min.js sets these headers.
            headers={"X-Requested-With": "XMLHttpRequest", "X-XSRF-TOKEN": xsrf_token},
        )
        assert response.json()["Result"] == 6

        # Authenticate with second factor.
        response = http_client.post(
            "https://auth.selfwealth.com.au/api/loginTwoFactor",
            json={
                "TwoFactorCode": otp,
                "ReturnUrl": return_url,
                "MfaType": 1,
            },
            # boot.min.js sets these headers.
            headers={"X-Requested-With": "XMLHttpRequest", "X-XSRF-TOKEN": xsrf_token},
        )
        assert response.json()["Result"] == 13

        # Request callback URL.
        response = http_client.get(f"https://auth.selfwealth.com.au{return_url}")
        # This should result in a redirect to the redirect URI.
        assert response.next_request

    # Finally, we can get the token! Setting the token here allows us to make
    # authenticated requests using the OAuth2 client.
    oauth2_client.token = oauth2_client.fetch_token(
        url="https://auth.selfwealth.com.au/connect/token",
        state=state,
        # The code is contained in the query parameters of the redirect URI.
        authorization_response=str(response.next_request.url),
        code_verifier=code_verifier,
    )

    # Get portfolio ID (ignoring "virtual" portfolios).
    # See https://apitest.selfwealth.com.au/swagger/index.html?urls.primaryName=SelfWealth%20Mobile%20API%20V4#operations-Mobile-get_api_v4_Mobile_portfolios
    portfolio_id = next(
        portfolio["portfolioId"]
        for portfolio in oauth2_client.get(
            "https://api.selfwealth.com.au/api/v4/Mobile/portfolios"
        ).json()["data"]["portfolios"]
        if portfolio["tradingStatusId"]
    )

    # /api/v3.3/Mobile/GetHoldings endpoint returns an object like the following.
    # See https://apitest.selfwealth.com.au/swagger/index.html?urls.primaryName=SelfWealth%20Mobile%20API%20V3.3#operations-Mobile-get_api_v3_3_Mobile_GetHoldings
    # [
    #   ...,
    #   {
    #     "Id": 0,
    #     "ProductId": 0,
    #     "Code": "CASH",
    #     "TRCode": null,
    #     "ShortName": "Cash",
    #     "AvailableUnits": 0,
    #     "TotalUnits": 0,
    #     "Price": 1,
    #     "Value": 0,
    #     "NetChange": 0,
    #     "PercentageChange": 0,
    #     "AveragePrice": null,
    #     "Weight": 0,
    #     "IsCash": true,
    #     "ProfitLoss": null,
    #     "ProfitLossPercentage": null,
    #     "ProductMarketGroupId": 1,
    #     "SectorId": 0,
    #     "Sector": null,
    #     "GICSId": 0,
    #     "Trend": null,
    #     "Name": null
    #   },
    #   ...
    # ]
    now = queensland_now()
    balances = []
    for holding in oauth2_client.get(
        "https://api.selfwealth.com.au/api/v3.3/Mobile/GetHoldings",
        params={"PortfolioId": portfolio_id},
    ).json():
        # Make it so each holding's code is either a currency code or stock symbol.
        code = holding["Code"]
        if code == "CASH":
            code = "AUD"
        elif code == "US CASH":
            code = "USD"
        balances.append(
            Balance(
                meta={},
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
    oauth2_client.close()
    return balances
