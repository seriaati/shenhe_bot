from pydantic import BaseModel, Field

from ..enum import AritfactMainStat, ArtifactType


class AritfactObject(BaseModel):
    """Artifact object model."""

    type: ArtifactType
    main_stat: AritfactMainStat = Field(..., alias="mainStatKey")


class AritfactSet(BaseModel):
    """Artifact set model."""

    name: str
    icon: str
    count: int
