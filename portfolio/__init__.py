__version__ = "0.1.0"

import logging

from beancount.parser import printer
import pyotp

from . import bitcoin, secrets, selfwealth, statecustodians, up

logger = logging.getLogger(__name__)


def update_balances(balances_filename="balances.beancount"):
    """Updates balances ledger with latest account balances."""
    logging.basicConfig(level=logging.INFO)
    # Open ledger file in append mode.
    with open(balances_filename, mode="a") as file:
        up_balances = up.get_balances(token=secrets.up.api_token)
        logger.info("Retrieved Up account balances.")
        printer.print_entries(up_balances, file=file)
        logger.info("Wrote Up account balances to %s.", file.name)

        bitcoin_balance = bitcoin.get_balance(
            api_key=secrets.blockonomics.api_key,
            addresses=secrets.bitcoin.addresses,
            account=secrets.bitcoin.account,
        )
        logger.info("Retrieved Bitcoin balance.")
        printer.print_entry(bitcoin_balance, file=file)
        logger.info("Wrote Bitcoin balance to %s.", file.name)

        selfwealth_balances = selfwealth.get_balances(
            email=secrets.selfwealth.email,
            password=secrets.selfwealth.password,
            otp=pyotp.TOTP(secrets.selfwealth.totp_key).now(),
        )
        logger.info("Retrieved SelfWealth holdings balances.")
        printer.print_entries(selfwealth_balances, file=file)
        logger.info("Wrote SelfWealth holdings balances to %s.", file.name)

        state_custodians_balances = statecustodians.get_balances(
            customer_id=secrets.statecustodians.customer_id,
            password=secrets.statecustodians.password,
        )
        logger.info("Retrieved State Custodians account balances.")
        printer.print_entries(state_custodians_balances, file=file)
        logger.info("Wrote State Custodians account balances to %s.", file.name)
