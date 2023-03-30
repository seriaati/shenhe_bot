from pydantic import BaseModel, Field


class Player(BaseModel):
    """Player model."""

    nickname: str
    adventure_rank: int = Field(..., alias="adventureRank")
    profile_picture: int = Field(..., alias="profilePicture")
    name_card: str = Field(..., alias="nameCard")
    region: str
