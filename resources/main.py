import json
from random import shuffle
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
async def board_get(response: Response):
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
async def board_post(response: Response):
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
async def board_round_get(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return {'round': board.round_get()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/board/round')
async def board_round_post(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success adding the round
        if board.round_add():
            response.status_code = status.HTTP_200_OK
            return {'round': board.round_get()}

        # If no success adding the round
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/board/round')
async def board_round_delete(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # Idempotent
        board.round_reset()

        response.status_code = status.HTTP_200_OK
        return {'round': board.round_get()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/score')
async def board_score_get(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.score_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/score/{player}')
async def board_score_player_get(player: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return {'score': board.score_player_get(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/score/{player}')
async def board_score_player_put(player: str, body: validators.BodyBoardScorePlayer, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the score
        if board.score_player_put(player, body.score):
            response.status_code = status.HTTP_200_OK
            return {'score': board.score_player_get(player)}

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/board/score/{player}')
async def board_score_pLayer_delete(player: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # Idempotent
        board.score_player_put(player, 0)

        response.status_code = status.HTTP_200_OK
        return {'score': board.score_player_get(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/map')
async def board_map_get(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.map_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/map/{region}')
async def board_map_region_get(region: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.map_region_get(region)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/map/{region}')
async def board_map_region_put(region: str, body: validators.BodyBoardMapRegion, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the score
        if board.map_region_put(region, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.map_region_get(region)

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/map/{region}/{country}')
async def board_map_region_country_get(region: str, country: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.map_region_country_get(region, country)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/map/{region}/{country}')
async def board_map_region_country_put(region: str, country: str, body: validators.BodyBoardMapRegionCountry, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the country
        if board.map_region_country_put(region, country, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.map_region_country_get(region, country)

        # If no success updating the country
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/nwo')
async def board_nwo_get(response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return [{'name': track} for track in board.nwo_get()]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/nwo/{track}')
async def board_nwo_track_get(track: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return [{'name': slot} for slot in board.nwo_track_get(track)]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_get(track: str, slot: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return board.nwo_track_slot_get(track, slot)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_put(track: str, slot: str, body: validators.BodyBoardNwoTrackSlot, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the track slot
        if board.nwo_track_slot_put(track, slot, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.nwo_track_slot_get(track, slot)

        # If no success updating the track slot
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_delete(track: str, slot: str, response: Response):
    try:
        global board

        # If there is no board
        if board == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # Idempotent
        slotReset = board.nwo_track_slot_get(track, slot)
        slotReset['supremacy'] = ''
        board.nwo_track_slot_put(track, slot, slotReset)

        response.status_code = status.HTTP_200_OK
        return board.nwo_track_slot_get(track, slot)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Cards endpoints
@app.get('/cards')
async def cards_get(response: Response):
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
async def cards_post(response: Response):
    try:
        global cards

        # Idempotent
        cards = Cards()

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.get('/cards/deck')
async def cards_deck_get(response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return cards.cards_deck_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.get('/cards/deck/{type}')
async def cards_deck_type_get(type: str, response: Response, random: bool=False):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        deck = cards.cards_deck_get(type)
        if random == False: return deck

        # If random is True, shuffle the deck
        shuffle(deck)
        return deck

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.post('/cards/deck/{type}/{id}')
async def cards_deck_type_id_post(type: str, id: int, response: Response):
    try:
        global board

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success updating the deck with the new card
        if cards.cards_deck_add(type, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success updating the deck with the new card
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.delete('/cards/deck/{type}/{id}')
async def cards_deck_type_id_delete(type: str, id: int, response: Response):
    try:
        global board

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success deleting the card from the deck
        if cards.cards_deck_remove(type, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success deleting the card from the deck
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.get('/cards/playing')
async def cards_playing_get(response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return cards.cards_playing_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

# Has to be below the /cards/deck and /cards/playing as otherwise FastAPI wouldn't know if /cards/deck or /cards/playing or /cards/{id} was called
@app.get('/cards/{id}')
async def cards_id_get(id: int, response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return cards.cards_get(id)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.get('/cards/player/{player}')
async def cards_player_player_get(player: str, response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        response.status_code = status.HTTP_200_OK
        return [{'id': card} for card in cards.cards_player_get(player)]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.post('/cards/player/{player}/{id}')
async def cards_player_player_id_post(player: str, id: int, response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success adding the card to the player's hand
        if cards.cards_player_add(player, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success adding the card to the player's hand
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.delete('/cards/player/{player}/{id}')
async def cards_player_player_id_delete(player: str, id: int, response: Response):
    try:
        global cards

        # If there are no cards
        if cards == None:
            response.status_code = status.HTTP_200_OK
            return {}

        # If success deleting the card to the player's hand
        if cards.cards_player_remove(player, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success deleting the card to the player's hand
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}
