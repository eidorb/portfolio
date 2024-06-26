import pytest

from portfolio import secrets, up
from tests import SecretString


@pytest.fixture
def up_api_token():
    """Gets Up API token from environment variable."""
    return SecretString(secrets.up.api_token)


def test_ping(up_api_token):
    """Pings Up API."""
    assert up.ping(token=up_api_token).json()["meta"]["statusEmoji"] == "⚡️"


def test_api_authorization_error():
    """Tests unauthorized response to invalid token."""
    response = up.ping(token="bogus")
    assert response.status_code == 401
    assert response.json()["errors"][0]["status"] == "401"


def test_get_balances(up_api_token):
    """Tests Balance directive is returned with expected currency code."""
    assert up.get_balances(token=up_api_token)[0].amount.currency == "AUD"
