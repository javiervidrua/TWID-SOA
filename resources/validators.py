from pydantic import BaseModel

# Models used to validate the request body
# https://fastapi.tiangolo.com/tutorial/body/
class BodyBoardScorePlayer(BaseModel):
    score: int