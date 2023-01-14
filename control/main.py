import logging
import json
from game import Game
import validators
import config
from datetime import datetime
from uuid import uuid4
# https://fastapi.tiangolo.com/advanced/response-change-status-code/
from fastapi import FastAPI, Request, Response, status, HTTPException, Depends
app = FastAPI()


# Define the logger
logger = logging.getLogger('control_logger')
level = config.ENV_LOGGING_LEVEL
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


# Custom OpenAPI 3.0 specification file
def custom_openapi():
    with open('openapi.json', 'r') as file:
        app.openapi_schema = json.load(file)
        return app.openapi_schema


# Definitions
app.openapi = custom_openapi
users = {}
usersLogs = {}
games = {}

# https://stackoverflow.com/questions/72831952/how-do-i-integrate-custom-exception-handling-with-the-fastapi-exception-handling
# Custom exception and handler
class AuthenticationException(Exception):
    def __init__(self):
        pass

@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)

# # https://stackoverflow.com/questions/64146591/custom-authentication-for-fastapi
# Function to verify that the user has a valid access token
def verify_token(req: Request):
    global users
    global games

    # If ENV_DEBUG is enabled, don't ask for a token if not provided, set the predefined one
    if config.ENV_DEBUG == 'True' and req.headers.get("X-ACCESS-TOKEN", None) == None:
        logger.info('Access token not provided, setting predefined one')
        token = 'development-token-0000-0001'
        users[token] = users.get(token, {'games': []})
        
        return token

    # Get the token from the headers
    token = req.headers.get("X-ACCESS-TOKEN", None)

    # If the token is not valid, raise exception
    if 'Bearer ' not in token or token.split('Bearer ')[1] not in users:
        logger.error(f'Invalid access token {token}')
        raise AuthenticationException()
    return token.split('Bearer ')[1]

# Function to debug the status of the service
def debug(game, player):
    logger.debug('get_players(): ' + str(game.get_players()))
    logger.debug('get_playingOrder(): ' + str(game.get_playingOrder()))
    logger.debug('get_playingOrderCurrent(): ' + str(game.get_playingOrderCurrent()))
    logger.debug('get_isStarted(): ' + str(game.get_isStarted()))
    logger.debug('get_isHeaderPhase(): ' + str(game.get_isHeaderPhase()))
    logger.debug('get_isPostHeaderPhase(): ' + str(game.get_isPostHeaderPhase()))
    logger.debug('get_destabilization(): ' + str(game.get_destabilization()))
    logger.debug('get_isFinished(): ' + str(game.get_isFinished()))
    logger.debug('cards_playing_get(): ' + str(game.cards_playing_get()))
    logger.debug('cards_player_get(): ' + str(game.cards_player_get(player)))
    logger.debug('board_round_get(): ' + str(game.board_round_get()))
    logger.debug('board_score_get(): ' + str(game.board_score_get()))
    # logger.debug('board_map_get(): ' + str(game.board_map_get()))


# Auth endpoints
@app.post('/auth/signin/guest')
async def auth_signing_guest_post(request: Request, response: Response):
    logger.info(f'/auth/signin/guest')
    try:
        global users
        global usersLogs

        # Log the IP of the client # https://stackoverflow.com/questions/60098005/fastapi-starlette-get-client-real-ip
        ip = request.client.host
        usersLogs[ip] = usersLogs.get(ip, {'count': 0, 'date': datetime.now()})

        # If 24h from the first signin from that IP, restart the count # https://stackoverflow.com/questions/39080155/python-check-if-date-is-within-24-hours
        difference = datetime.now() - usersLogs[ip]['date']
        if difference.days != 0:
            usersLogs[ip]['date'] = datetime.now()
            usersLogs[ip]['count'] = 0

        # Increment the count of requests from that IP
        usersLogs[ip]['count'] = usersLogs[ip].get('count', 0) + 1

        # Log
        logger.info(f'Token request by IP {ip}')

        # Allow maximum of 10 requests per 24 hours
        if usersLogs[ip]['count'] > 10:
            logger.info(f'Blocked IP {ip}')
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        # Create a new uuid4 (a new user) # https://stackoverflow.com/questions/534839/how-to-create-a-guid-uuid-in-python
        uuid = str(uuid4())
        users[uuid] = {'games': []}

        response.status_code = status.HTTP_200_OK
        return {'access_token': uuid, 'token_type': 'Bearer'}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/auth/signout')
async def auth_signout_post(request: Request, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/auth/signout')
    try:
        global users
        global usersLogs

        # # Log the IP of the client # https://stackoverflow.com/questions/60098005/fastapi-starlette-get-client-real-ip
        ip = request.client.host

        # Decrement the count of requests from that IP
        usersLogs[ip]['count'] = usersLogs[ip]['count'] - 1

        # Log
        logger.info(f'Token deletion by IP {ip}')

        # Remove the uuid4 (the user id) from the users object (sign the user out)
        users.pop(token, None)

        response.status_code = status.HTTP_200_OK
        return {'access_token': token, 'token_type': 'Bearer'}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Game endpoints
@app.get('/game')
async def game_get(response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game')
    try:
        global users
        global games

        # Get the games of the user, the ones he created and the ones he is part of
        userGames = [gameId for gameId in users[token]['games']]
        [userGames.append(game) for game in games if token in list(games[game].get_players().values())]
        # Remove the duplicates
        userGames = list(set(userGames))

        # If there are no games
        if userGames == []:
            response.status_code = status.HTTP_200_OK
            return []

        response.status_code = status.HTTP_200_OK
        return [{'id': gameId} for gameId in userGames]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game')
async def game_post(response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game')
    try:
        global users
        global games

        # 10 games maximum
        if len(users[token]['games']) > 10:
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        # Idempotent
        game = Game()

        # When a user creates a game, add it to users[user]['games']
        users[token]['games'].append(repr(game))

        # Add the game to the list of games
        games[repr(game)] = game

        response.status_code = status.HTTP_200_OK
        return {'id': repr(game)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}')
async def game_game_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}')
    try:
        global users
        global games

        # If there is no game or if the user is not part of this specific game
        if game not in games and (game not in users[token]['games'] or token not in list(games[game].get_players().values())):
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        response.status_code = status.HTTP_200_OK
        return {
            'isStarted': games[game].get_isStarted(),
            'isFinished': games[game].get_isFinished(),
            'isHeaderPhase': games[game].get_isHeaderPhase(),
            'playingOrder': games[game].get_playingOrderCurrent(),
            'players': [player for player in games[game].get_players() if games[game].get_players()[player] != None]
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}')
async def game_game_post(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}')
    try:
        global users
        global games

        # If there is no game or if the user is not the creator of this specific game or if there are no players assigned
        if game not in games or game not in users[token]['games'] or len([user for user in list(games[game].get_players().values()) if user != None]) == 0:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        if not games[game].start():
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}')
async def game_game_delete(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}')
    try:
        global users
        global games

        # If the user is not the creator of the game or if there is no game
        if game not in users[token]['games'] or game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Remove the game from the user and from the games
        users[token]['games'].remove(game)
        games.pop(game)

        response.status_code = status.HTTP_200_OK
        return {'id': game}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/player/{player}')
async def game_game_player_player_post(game: str, player: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/player/{player}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # If this is the first user to choose a player, he must be the creator of the game
        if len([player for player in list(games[game].get_players().values()) if player != None]) == 0 and game not in users[token]['games']:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # If the player has not been already chosen and this user has not already chosen a player, set the player to the requesting user
        if games[game].get_isStarted() == False and games[game].get_isFinished() == False and games[game].get_players()[player] == None and token not in list(games[game].get_players().values()):
            if games[game].set_player_user(player, token) == True:
                return Response(status_code=status.HTTP_200_OK)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/round')
async def game_game_board_round_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/board/round')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # If the game has not started or if it has ended
        if games[game].get_isStarted() == False or games[game].get_isFinished() == True:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the round
        response.status_code = status.HTTP_200_OK
        return games[game].board_round_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/score')
async def game_game_board_score_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/board/score')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # If the game has not started or if it has ended
        if games[game].get_isStarted() == False or games[game].get_isFinished() == True:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the score
        response.status_code = status.HTTP_200_OK
        return games[game].board_score_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/map')
async def game_game_board_map_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/board/map')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # If the game has not started or if it has ended
        if games[game].get_isStarted() == False or games[game].get_isFinished() == True:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the map
        response.status_code = status.HTTP_200_OK
        return games[game].board_map_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/player')
async def game_game_cards_player_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/cards/player')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # If the game has not started or if it has ended
        if games[game].get_isStarted() == False or games[game].get_isFinished() == True:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Get the cards
        cards = games[game].cards_player_get(player)

        response.status_code = status.HTTP_200_OK
        return cards
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/playing')
async def game_game_cards_playing_get(game: str, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/cards/playing')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # If the game has not started or if it has ended
        if games[game].get_isStarted() == False or games[game].get_isFinished() == True:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the cards that are currently being played
        cards = games[game].cards_playing_get()

        response.status_code = status.HTTP_200_OK
        return cards
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/{id}')
async def game_game_cards_it_get(game: str, id: int, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/cards/{id}')
    try:
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        # Get the card
        response.status_code = status.HTTP_200_OK
        return games[game].card_get(id)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/influence/{id}')
async def game_game_cards_playing_influence_id_post(game: str, id: int, body: validators.GameGameCardsPlayingInfluence, response: Response, token: str = Depends(verify_token), validate: bool=False):
    logger.info(f'/game/{game}/cards/playing/influence/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's not in the header phase, it's not in the postHeader phase and the user belongs to that game, play the specified card by influence
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == False and games[game].get_isPostHeaderPhase() == False and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            if games[game].cards_play_influence(player, id, json.loads(body.json()), validate) == True:
                # Debug
                debug(games[game], player)
                
                return games[game].card_get(id)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/destabilization/{id}')
async def game_game_cards_playing_destabilization_id_post(game: str, id: int, body: validators.GameGameCardsPlayingDestabilization, response: Response, token: str = Depends(verify_token), validate: bool=False):
    logger.info(f'/game/{game}/cards/playing/destabilization/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's not in the header phase, it's not in the postHeader phase and the user belongs to that game, play the specified card by destabilization
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == False and games[game].get_isPostHeaderPhase() == False and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            result = games[game].cards_play_destabilization(player, id, json.loads(body.json()), validate)

            # Debug
            debug(games[game], player)
            
            # If no validate
            if result == True:
                destabilization = games[game].get_destabilization()
                # If second request
                if destabilization == None:
                    return games[game].card_get(id)
                # If first request
                else:
                    return destabilization['result']
            # If validate
            elif type(result) == int:
                return result

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/text/{id}')
async def game_game_cards_playing_text_id_post(game: str, id: int, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/cards/playing/text/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's not in the header phase (we don't care about the postHeader phase) and the user belongs to that game, play the specified card by its text
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == False and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            if games[game].cards_play_text(player, id) == True:
                # Debug
                debug(games[game], player)
                
                return games[game].card_get(id)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/score/{id}')
async def game_game_cards_playing_score_id_post(game: str, id: int, body: validators.GameGameCardsPlayingScore, response: Response, token: str = Depends(verify_token), validate: bool=False):
    logger.info(f'/game/{game}/cards/playing/score/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's not in the header phase, it's in the postHeader phase and the user belongs to that game, play the specified card by its score
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == False and games[game].get_isPostHeaderPhase() == False and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            if games[game].cards_play_score(player, id, json.loads(body.json()), validate) == True:
                # Debug
                debug(games[game], player)

                return games[game].card_get(id)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/nwo/{id}')
async def game_game_cards_playing_nwo_id_post(game: str, id: int, body: validators.GameGameCardsPlayingNwo, response: Response, token: str = Depends(verify_token), validate: bool=False):
    logger.info(f'/game/{game}/cards/playing/nwo/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's not in the header phase, it's in the postHeader phase and the user belongs to that game, play the specified card by its nwo
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == False and games[game].get_isPostHeaderPhase() == False and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            if games[game].cards_play_nwo(player, id, json.loads(body.json()), validate) == True:
                # Debug
                debug(games[game], player)

                return games[game].card_get(id)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/header/{id}')
async def game_game_cards_playing_header_id_post(game: str, id: int, response: Response, token: str = Depends(verify_token)):
    logger.info(f'/game/{game}/cards/playing/header/{id}')
    try:
        global users
        global games

        # If there is no game
        if game not in games:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        
        # Get the player of the user
        player = [player for player in games[game].get_players() if games[game].get_players()[player] == token]
        if len(player) != 1:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
        player = player[0]

        # Debug
        debug(games[game], player)

        # If the game has started and not ended, it's in the header phase and the user belongs to that game, set the specified card as his header card
        if games[game].get_isStarted() == True and games[game].get_isFinished() == False and games[game].get_isHeaderPhase() == True and token in list(games[game].get_players().values()) and id in games[game].cards_player_get(player)[player]['hand']:
            games[game].cards_playing_header_set(player, id)
            
            # Debug
            debug(games[game], player)
            
            return Response(status_code=status.HTTP_200_OK)

        # Otherwise, return bad request
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}
