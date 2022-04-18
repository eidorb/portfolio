import pathlib
import typing

import mechanicalsoup
from beancount.core.data import Amount, Balance, D

from .common import queensland_now


def get_balances(customer_id: str, password: str) -> list[typing.NamedTuple]:
    """Returns State Custodians loan portion balances.

    Loan portions are liabilities (Liabilities:), offset portions are assets
    (Assets:).

    :param customer_id: State Custodians customer ID.
    :param password: State Custodians password.

    :return: List of Beancount Balance directives.
    """
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(
        "https://loanenquiry.com.au",
        # Verify with certificate bundle adjacent to this module. This is required
        # because the website does not appear to be sending a certificate bundle
        # as it should.
        # See https://www.sslshopper.com/ssl-checker.html#hostname=loanenquiry.com.au
        verify=str(pathlib.Path(__file__).parent / "loanenquiry.com.au_bundle.pem"),
    ).raise_for_status()

    # Sign in.
    browser.select_form()
    browser.form["CustomerId"] = customer_id
    browser.form["Password"] = password
    browser.submit_selected()

    # Navigate to the loan view page.
    browser.open_relative("/Borrower/PortionDetails")

    now = queensland_now()
    balances = []

    # For each loan portion, select the portion and submit the form.
    for option in browser.page.find_all("option"):
        # nr=1 means the second (0-indexed) form on the page.
        browser.select_form(nr=1)
        browser["Portion"] = option.text
        browser.submit_selected()

        # Liabilities and assets have different signs. So, work out if it is an
        # offset portion or not, and handle accordingly.
        #
        # The first td.cell-info of table#portion-details is the loan amount.
        # If this contains "n/a", it is an offset portion, not a loan.
        if (
            "n/a"
            in browser.page.find("table", id="portion-details")
            .find("td", class_="cell-info")
            .string
        ):
            balances.append(
                Balance(
                    meta=dict(time=now.isoformat()),
                    date=now.date(),
                    # Offset portions means asset account.
                    account=f"Assets:StateCustodians:{option.text}",
                    amount=Amount(
                        D(
                            # The fourth (0-indexed) td element contains the
                            # offset balance. It's surrounded by whitespace and
                            # a leading dollar sign.
                            browser.page.find("table", id="portion-details")
                            .find_all("td")[3]
                            .string.strip()
                            # Remove leading dollar sign.
                            .lstrip("$")
                        ),
                        "AUD",
                    ),
                    tolerance=None,
                    diff_amount=None,
                )
            )
        else:
            balances.append(
                Balance(
                    meta=dict(time=now.isoformat()),
                    date=now.date(),
                    # Loan portion means liability account.
                    account=f"Liabilities:StateCustodians:{option.text}",
                    amount=Amount(
                        D(
                            # Make this liability negative in value.
                            "-"
                            +
                            # The second (0-indexed) td element contains the
                            # loan balance. It's surrounded by whitespace and
                            # a leading dollar sign.
                            browser.page.find("table", id="portion-details")
                            .find_all("td")[1]
                            .string.strip()
                            .lstrip("$")
                        ),
                        "AUD",
                    ),
                    tolerance=None,
                    diff_amount=None,
                )
            )

    return balances
