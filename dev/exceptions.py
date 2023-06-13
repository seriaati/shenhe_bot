from typing import List

from dev.enum import CheckInAPI, GameType


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
    """When a TCG card in Genshin Impact is not found"""

    def __str__(self):
        return "Card not found"


class InvalidWeaponCalcInput(Exception):
    def __str__(self):
        return "Invalid weapon calc input"


class InvalidAscensionInput(Exception):
    def __str__(self):
        return "Invalid ascension input"


class NoWishHistory(Exception):
    pass


class NumbersOnly(Exception):
    pass


class AutocompleteError(Exception):
    pass


class CardNotReady(Exception):
    """When a profile card design for a character is not ready yet"""


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


class GameNotSupported(Exception):
    def __init__(self, current: GameType, supported: List[GameType]) -> None:
        self.current = current
        self.supported = supported
