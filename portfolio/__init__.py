__version__ = "0.1.0"

import logging
import os

from beancount.parser import printer

from . import bitcoin
from . import up

logger = logging.getLogger(__name__)


def update_balances(balances_filename="balances.beancount"):
    """Updates balances ledger with latest account balances."""
    logging.basicConfig(level=logging.INFO)
    # Open ledger file in append mode.
    with open(balances_filename, mode="a") as file:
        up_balances = up.get_balances(token=os.environ["UP_API_TOKEN"])
        logger.info("Retrieved Up account balances.")
        printer.print_entries(up_balances, file=file)
        logger.info("Wrote Up account balances to %s.", file.name)

        bitcoin_balance = bitcoin.get_balance(
            api_key=os.environ["BLOCKONOMICS_API_KEY"],
            addresses=os.environ["BITCOIN_ADDRESSES"],
            account=os.environ["BITCOIN_ACCOUNT"],
        )
        logger.info("Retrieved Bitcoin balance.")
        printer.print_entry(bitcoin_balance, file=file)
        logger.info("Wrote Bitcoin balance to %s.", file.name)
