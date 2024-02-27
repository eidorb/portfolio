import logging

import pyotp
from beancount.parser import printer

from . import bankwest, bitcoin, secrets, selfwealth, ubank, up

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

    # Handle ubank a little differently to other institutions. The secret is updated
    # if required.
    try:
        # Get cookie when getting balances.
        balances, trusted_cookie = ubank.get_balances_and_cookie(
            username=secrets.ubank.username,
            password=secrets.ubank.password,
            cookie=secrets.ubank.cookie,
        )
        logger.info("Retrieved ubank balances.")
        with open(filename, mode="a") as file:
            printer.print_entries(balances, file=file)
        logger.info("Wrote ubank balances to %s.", file.name)
    except Exception:
        logger.error("Failed to update ubank balances.", exc_info=True)

    # Update trusted cookie if changed.
    if trusted_cookie != secrets.ubank.cookie:
        ubank.change_cookie(trusted_cookie)
        logger.info("Updated ubank trusted cookie")
