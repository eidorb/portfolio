import ast
import importlib.resources
from tempfile import NamedTemporaryFile

import pytest

from portfolio import secrets, ubank
from portfolio.ubank import CookieTransformer, change_cookie
from tests import SecretDict, SecretString


@pytest.fixture
def username():
    return SecretString(secrets.ubank.username)


@pytest.fixture
def password():
    return SecretString(secrets.ubank.password)


@pytest.fixture
def cookie():
    return SecretDict(secrets.ubank.cookie)


def test_get_balances(username, password, cookie):
    """Tests Balance directive is returned with expected accounts."""
    balances, trusted_cookie = ubank.get_balances_and_cookie(username, password, cookie)
    accounts = [balance.account.split(":")[-1] for balance in balances]
    assert "USave" in accounts
    assert "USpend" in accounts
    assert "name" in cookie


def test_cookie_transformer():
    module = ast.parse(
        """
class Class:
    cookie = {'a': 1, 'b': 2}"""
    )
    assert module.body[0].body[0].value.values[0].value == 1
    assert module.body[0].body[0].value.values[1].value == 2

    cookie = {"c": 3, "d": 4}
    transformed = CookieTransformer(cookie).visit(module)

    # The dict values should be transformed.
    assert transformed.body[0].body[0].value.values[0].value == 3
    assert transformed.body[0].body[0].value.values[1].value == 4

    # The dict should be replaced with cookie.
    assert ast.dump(transformed.body[0].body[0].value) == ast.dump(
        ast.parse(str(cookie), mode="eval").body
    )


def test_change_cookie():
    """Tests cookie dict is replaced in module file."""
    with NamedTemporaryFile("w") as module_file:
        traversable = importlib.resources.files().joinpath(module_file.name)
        module_file.write(
            """
class Class:
    cookie = {"a": 1, "b": 2}"""
        )
        module_file.flush()
        change_cookie({"replacement": "cookie"}, traversable)
        assert traversable.read_text().endswith("{'replacement': 'cookie'}")
