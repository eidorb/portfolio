import sys

import pyotp
from beancount.parser import printer

from . import bankwest, secrets, selfwealth, ubank, up


def update(filename="balances.beancount") -> None:
    """Updates ledger with latest account balances."""
    # Iterate over (name, get_balances) tuples. For each tuple, retrieve balances
    # and append to ledger file.
    for name, get_balances in (
        (
            "Up",
            lambda: up.get_balances(token=secrets.up.api_token),
        ),
        (
            "SelfWealth",
            lambda: selfwealth.get_balances(
                email=secrets.selfwealth.email,
                password=secrets.selfwealth.password,
                otp=pyotp.TOTP(secrets.selfwealth.totp_key).now(),
            ),
        ),
        (
            "Bankwest",
            lambda: [
                bankwest.get_balance(
                    pan=secrets.bankwest.pan,
                    password=secrets.bankwest.password,
                )
            ],
        ),
        (
            "ubank",
            lambda: ubank.get_balances(device=ubank.get_device()),
        ),
    ):
        # Open ledger file in append mode.
        with open(filename, mode="a") as file:
            try:
                balances = get_balances()
                print(f"Retrieved {len(balances)} {name} balances.")
                printer.print_entries(balances, file=file)
                print(f"Wrote {name} balances to {file.name}.")
            except Exception:
                print(f"Failed to update {name} balances.")


if __name__ == "__main__":
    update(sys.argv[1])
