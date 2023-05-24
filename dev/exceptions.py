from discord import app_commands

from dev.enum import CheckInAPI


class AccountNotFound(Exception):
    def __str__(self):
        return "Shenhe account not found"


class ItemNotFound(Exception):
    def __str__(self):
        return "Item not found"


class NoPlayerFound(Exception):
    def __str__(self):
        return "No player found"


class NoCharacterFound(Exception):
    def __str__(self):
        return "No character found"


class CardNotFound(Exception):
    def __str__(self):
        return "Card not found"


class InvalidWeaponCalcInput(Exception):
    def __str__(self):
        return "Invalid weapon calc input"


class InvalidAscensionInput(Exception):
    def __str__(self):
        return "Invalid ascension input"


class DBError(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


class NoUID(app_commands.CheckFailure):
    def __init__(self, current_user: bool):
        self.current_user = current_user


class NoCookie(app_commands.CheckFailure):
    def __init__(self, current_user: bool, current_account: bool):
        self.current_user = current_user
        self.current_account = current_account


class NoWishHistory(app_commands.CheckFailure):
    def __str__(self):
        return "No wish history"


class NumbersOnly(Exception):
    pass


class AutocompleteError(Exception):
    pass


class CardNotReady(Exception):
    pass


class FeatureDisabled(Exception):
    pass


class Maintenance(Exception):
    pass


class CheckInAPIError(Exception):
    def __init__(self, api: CheckInAPI, status: int) -> None:
        self.api = api
        self.status = status

    def __str__(self) -> str:
        return f"{self.api} returned {self.status}"


class InvalidInput(Exception):
    def __init__(self, a: int, b: int) -> None:
        self.a = a
        self.b = b

class AbyssDataNotFound(Exception):
    pass

class WishFileImportError(Exception):
    pass