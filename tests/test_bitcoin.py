import pytest

from portfolio import bitcoin, secrets
from tests import SecretString


@pytest.fixture
def api_key():
    """Gets Blockonomics API key from environment variable."""
    return SecretString(secrets.blockonomics.api_key)


def test_get_balance(api_key):
    """Tests total balance of confirmed transactions."""
    assert (
        str(
            bitcoin.get_balance(
                api_key=api_key,
                addresses="1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp 1dice97ECuByXAvqXpaYzSaQuPVvrtmz6",
                account="Bitcoin",
            ).amount.number
        )
        == "0.13888486"
    )
