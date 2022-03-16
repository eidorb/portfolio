import os

import pytest

from portfolio import __version__
from portfolio import up


def test_version():
    assert __version__ == "0.1.0"


@pytest.fixture
def up_api_token():
    return os.environ["UP_API_TOKEN"]


def test_up_api():
    """Pings Up API."""
    assert up.ping(token=up_api_token).json()["meta"]["statusEmoji"] == "⚡️"


def test_up_api_authorization_error():
    """Tests unauthorized response to invalid token."""
    response = up.ping(token="bogus")
    assert response.status_code == 401
    assert response.json()["errors"][0]["status"] == "401"
