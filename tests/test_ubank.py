import ubank

from portfolio.ubank import get_balances, get_device, save_device

# Patch Device.__repr__ to hide secrets.
ubank.Device.__repr__ = lambda self: "Device(hardware_id='***', ...)"


def test_get_balances():
    """Tests Balance directive is returned with expected accounts."""
    balances = get_balances(get_device())
    accounts = [balance.account.split(":")[-1] for balance in balances]
    assert "USave" in accounts
    assert "USpend" in accounts


def test_get_device():
    """Tests restoring enrolled ubank device from Parameter Store."""
    assert get_device().device_meta[0] == "{"


def test_save_device():
    """Tests saving enrolled ubank device to Parameter Store."""
    assert save_device(get_device())["Version"]
