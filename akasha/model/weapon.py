from pydantic import BaseModel, Field, validator


class WeaponInfo(BaseModel):
    """Weapon info model."""

    level: int
    promote_level: int = Field(..., alias="promoteLevel")
    refinement: int = Field(..., alias="refinementLevel")

    @validator("refinement", pre=True, always=True, allow_reuse=True)
    def _validate_refinement(cls, v):
        return v["val"]


class Weapon(BaseModel):
    """Weapon model."""

    info: WeaponInfo = Field(..., alias="weaponInfo")
    icon: str
    name: str
