import json
from board import Board
from cards import Cards
from fastapi import FastAPI, Response, status
app = FastAPI()


# Custom OpenAPI 3.0 specification file
def custom_openapi():
    with open('openapi.json', 'r') as file:
        app.openapi_schema = json.load(file)
        return app.openapi_schema


# Definitions
app.openapi = custom_openapi
board = None
cards = None


# Endpoints
@app.get('/board')
async def boardGet(response: Response):
    try:
        global board

        if board == None:
            raise Exception()

        response.status_code = status.HTTP_200_OK
        return repr(board)
    except:
        return {}


@app.post('/board')
async def boardPost(response: Response):
    try:
        global board

        board = Board()

        response.status_code = status.HTTP_200_OK
        return repr(board)
    except:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {}


@app.get('/cards')
async def cardsGet(response: Response):
    try:
        global cards

        if cards == None:
            raise Exception()

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except:
        return {}


@app.post('/cards')
async def cardsPost(response: Response):
    try:
        global cards

        cards = Cards()

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {}
