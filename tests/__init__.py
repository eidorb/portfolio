class SecretString(str):
    """Obfuscates string in __repr__."""

    def __repr__(self) -> str:
        return repr("*****")


class SecretDict(dict):
    """Obfuscates string in __repr__."""

    def __repr__(self) -> str:
        return repr({"***": "***"})
