import logging

from beancount.parser import printer
import pyotp

from . import bankwest, bitcoin, secrets, selfwealth, statecustodians, up

logger = logging.getLogger(__name__)


def update(filename="balances.beancount") -> None:
    """Updates ledger with latest account balances."""
    logging.basicConfig(level=logging.INFO)

    # Iterate over (name, get_balances) tuples. For each tuple, retrieve balances
    # and append to ledger file.
    for name, get_balances in (
        (
            "Up",
            lambda: up.get_balances(token=secrets.up.api_token),
        ),
        (
            "Bitcoin",
            lambda: [
                bitcoin.get_balance(
                    api_key=secrets.blockonomics.api_key,
                    addresses=secrets.bitcoin.addresses,
                    account=secrets.bitcoin.account,
                )
            ],
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
            "State Custodians",
            lambda: statecustodians.get_balances(
                user_id=secrets.statecustodians.user_id,
                password=secrets.statecustodians.password,
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
    ):
        # Open ledger file in append mode.
        with open(filename, mode="a") as file:
            try:
                balances = get_balances()
                logger.info("Retrieved %s balances.", name)
                printer.print_entries(balances, file=file)
                logger.info("Wrote %s balances to %s.", name, file.name)
            except Exception:
                logger.error("Failed to get %s balances.", name, exc_info=True)
