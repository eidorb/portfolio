import typing
from datetime import datetime

from beancount.core.data import Amount, Balance, D
from playwright.sync_api import sync_playwright

from .common import queensland_now


class Portion(typing.NamedTuple):
    id: str
    balance: str


def parse_content(text: str) -> tuple[Portion, ...]:
    """Returns values parsed from page text content."""
    stripped_lines = (line.strip() for line in text.splitlines())
    non_empty_lines = [line for line in stripped_lines if line]
    # Drop the first two lines ('Home loan' and loan number).
    lines = non_empty_lines[2:]
    # Group into chunks of 7. e.g., ('Portion O', 'BSB: 123456 ACC: 111111111',
    # 'BSB: 123456 ACC: 111111111', 'Available redraw', '$1.11', 'Account balance',
    # '$2,222.22')
    portions = zip(*([iter(lines)] * 7))
    return tuple(
        Portion(
            # 'Portion O' -> 'O'.
            id=portion[0].split()[1],
            # Account balance.
            balance=portion[6],
        )
        for portion in portions
    )


def convert_portions(
    portions: typing.Iterable[Portion], datetime: datetime
) -> list[typing.NamedTuple]:
    """Converts portions to Beancount balance directives."""
    balances = []
    for portion in portions:
        if portion.id == "O":
            account = "Assets:StateCustodians:O"
        else:
            account = f"Liabilities:StateCustodians:{portion.id}"
        balance = Balance(  # type: ignore
            meta=dict(time=datetime.isoformat()),
            date=datetime.date(),
            account=account,
            amount=Amount(
                # Remove dollar sign from balance string.
                D(portion.balance.replace("$", "")),
                "AUD",
            ),
            tolerance=None,
            diff_amount=None,
        )
        balances.append(balance)
    return balances


def get_balances(user_id: str, password: str) -> list[typing.NamedTuple]:
    """Returns State Custodians loan portion balances.

    Loan portions are liabilities (Liabilities:), offset portions are assets
    (Assets:).

    :param user_id: State Custodians customer ID.
    :param password: State Custodians password.

    :return: List of Beancount Balance directives.
    """

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch()

    # Sign in.
    page = browser.new_page()
    page.goto("https://loanaccess.com.au/loanaccess")
    page.locator("#originalU").get_by_role("textbox").click()
    page.locator("#input-6").get_by_role("textbox").fill(user_id)
    page.locator("#originalP").get_by_role("textbox").click()
    page.locator("#input-7").get_by_role("textbox").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    # Click to expand all loan portions.
    page.get_by_role("cell", name="Home loan").click()

    # Extract loan portion text content from page.
    text_content = page.locator("#counterparty-0").text_content()

    browser.close()
    playwright.stop()

    portions = parse_content(text_content)
    balances = convert_portions(portions, queensland_now())
    return balances
