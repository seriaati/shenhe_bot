class UIDNotFound(Exception):
    def __str__(self):
        return "UID not found"

class ShenheAccountNotFound(Exception):
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