import json
from board import Board
from cards import Cards
import validators
# https://fastapi.tiangolo.com/advanced/response-change-status-code/
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


# Board endpoints
@app.get('/board')
async def boardGet(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return repr(board)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/board')
async def boardPost(response: Response):
    try:
        global board

        # Idempotent
        board = Board()

        response.status_code = status.HTTP_200_OK
        return repr(board)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/round')
async def boardRoundGet(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return {'round': board.roundGet()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/board/round')
async def boardRoundPost(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success adding the round
        if board.roundAdd():
            response.status_code = status.HTTP_200_OK
            return {'round': board.roundGet()}

        # If no success adding the round
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/board/round')
async def boardRoundDelete(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # Idempotent
        board.roundReset()

        response.status_code = status.HTTP_200_OK
        return {'round': board.roundGet()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/score')
async def boardScoreGet(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.scoreGet()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/score/{player}')
async def boardScorePLayerGet(player: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return {'score': board.scorePlayerGet(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/score/{player}')
async def boardScorePLayerPut(player: str, body: validators.BodyBoardScorePlayer, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the score
        if score := board.scorePlayerPut(player, body.score):
            response.status_code = status.HTTP_200_OK
            return {'score': score}

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/board/score/{player}')
async def boardScorePLayerDelete(player: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # Idempotent
        board.scorePlayerPut(player, 0)

        response.status_code = status.HTTP_200_OK
        return {'score': board.scorePlayerGet(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/map')
async def boardMapGet(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.mapGet()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/map/{region}')
async def boardMapRegionGet(region: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.mapRegionGet(region)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/map/{region}')
async def boardScorePLayerPut(region: str, body: validators.BodyBoardMapRegion, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the score
        if board.mapRegionPut(region, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.mapRegionGet(region)

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Cards endpoints
@app.get('/cards')
async def cardsGet(response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/cards')
async def cardsPost(response: Response):
    try:
        global cards

        # Idempotent
        cards = Cards()

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}
