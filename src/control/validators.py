from pydantic import BaseModel, validator
from typing import Dict, List, Optional

# Models used to validate the request body
# https://fastapi.tiangolo.com/tutorial/body/
class GameGameCardsPlayingInfluenceTargets(BaseModel):
    target: Dict[str, int]
    targetExtra: Optional[Dict[str, int]]

    def validate_influence(parent, v):
        for field in v:
            if v[field] < 0 or v[field] > 5:
                raise ValueError(f"'{parent}'.'{field}' field must be >= 0 and <= 5")

    # https://github.com/pydantic/pydantic/issues/506
    @validator('target')
    def validate_target(cls, v):
        if len(v.values()) == 0:
            raise ValueError("'target' field cannot be an empty object")
        if len(v.values()) > 1:
            raise ValueError("'target' field can only be one country")
        cls.validate_influence('target', v)
        return v

    @validator('targetExtra')
    def validate_targetExtra(cls, v):
        cls.validate_influence('targetExtra', v)
        return v

class GameGameCardsPlayingInfluence(BaseModel):
    targets: List[GameGameCardsPlayingInfluenceTargets]

    @validator('targets')
    def validate_targets(cls, v):
        if len(v) == 0:
            raise ValueError("'targets' field cannot have 0 length")
        return v

class GameGameCardsPlayingDestabilization(BaseModel):
    target: str
    add: Optional[List[Dict[str, int]]]
    remove: Optional[List[Dict[str, int]]]

class GameGameCardsPlayingScore(BaseModel):
    region: str

class GameGameCardsPlayingNwo(BaseModel):
    name: str