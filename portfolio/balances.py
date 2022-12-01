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
            "State Custodians",
            lambda: statecustodians.get_balances(
                user_id=secrets.statecustodians.user_id,
                password=secrets.statecustodians.password,
            ),
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

    # Open ledger file in append mode.
    with open(filename, mode="a") as file:
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
        printer.print_entries([bitcoin_balance], file=file)
        logger.info("Wrote Bitcoin balance to %s.", file.name)

        try:
            selfwealth_balances = selfwealth.get_balances(
                email=secrets.selfwealth.email,
                password=secrets.selfwealth.password,
                otp=pyotp.TOTP(secrets.selfwealth.totp_key).now(),
            )
            logger.info("Retrieved SelfWealth holdings balances.")
            printer.print_entries(selfwealth_balances, file=file)
            logger.info("Wrote SelfWealth holdings balances to %s.", file.name)
        # .get_balances() started raising this exception, but only from within GitHub
        # Actions workflows. Catch it so that other balances can still be retrieved.
        except TypeError:
            logger.error("Failed to get SelfWealth holdings balances.", exc_info=True)

        bankwest_balance = bankwest.get_balance(
            pan=secrets.bankwest.pan,
            password=secrets.bankwest.password,
        )
        logger.info("Retrieved Bankwest account balance.")
        printer.print_entries([bankwest_balance], file=file)
        logger.info("Wrote Bankwest account balance to %s.", file.name)
