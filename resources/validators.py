from pydantic import BaseModel
from typing import List

# Models used to validate the request body
# https://fastapi.tiangolo.com/tutorial/body/
class BodyBoardScorePlayer(BaseModel):
    score: int

class BoardMapRegion(BaseModel):
    country: str

# https://stackoverflow.com/questions/68650162/fastapi-receive-list-of-objects-in-body-request
# https://stackoverflow.com/questions/60844846/read-a-body-json-list-with-fastapi
def bodyBoardMapRegion(items: List[BoardMapRegion]):
    pass

# https://stackoverflow.com/questions/58068001/python-pydantic-using-a-list-with-json-objects
class BodyBoardMapRegion(BaseModel):
    __root__: List[BoardMapRegion]