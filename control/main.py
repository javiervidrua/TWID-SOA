import json
from game import Game
import validators
from datetime import datetime
from uuid import uuid4
# https://fastapi.tiangolo.com/advanced/response-change-status-code/
from fastapi import FastAPI, Request, Response, status
app = FastAPI()


# Custom OpenAPI 3.0 specification file
def custom_openapi():
    with open('openapi.json', 'r') as file:
        app.openapi_schema = json.load(file)
        return app.openapi_schema


# Definitions
app.openapi = custom_openapi
users = {}
usersLogs = {}
# DEFINE VARIABLES AND STUFF
# games = {}
# board = None
# cards = None


# Auth endpoints
@app.post('/auth/signin/guest')
async def auth_signing_guest_post(request: Request, response: Response):
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
        print(f'LOG:      auth/signin/guest: {usersLogs[ip]}')

        # Allow maximum of 10 requests per 24 hours
        if usersLogs[ip]['count'] > 10:
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        # Create a new uuid4 (a new user) # https://stackoverflow.com/questions/534839/how-to-create-a-guid-uuid-in-python
        uuid = str(uuid4())
        users[uuid] = {}

        response.status_code = status.HTTP_200_OK
        return {'access_token': uuid, 'token_type': 'Bearer'}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# # Game endpoints
# @app.get('/game')
# async def game_get(response: Response):
#     try:
#         global games

#         # If there are no games
#         if games == []:
#             response.status_code = status.HTTP_200_OK
#             return []

#         response.status_code = status.HTTP_200_OK
#         return [{'id':gameId} for gameId in list(games.keys())]
#     except Exception as e:
#         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#         return {'Error': e}


# @app.post('/game')
# async def game_post(response: Response):
#     try:
#         global games

#         # Idempotent
#         game = Game()
#         games[repr(game)] = game

#         response.status_code = status.HTTP_200_OK
#         return {'id':repr(game)}
#     except Exception as e:
#         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#         return {'Error': e}


# # Board endpoints
# @app.get('/game/{game}/board')
# async def board_get(game: str, response: Response):
#     try:
#         global games

#         # If there is no game
#         if game not in games.keys():
#             response.status_code = status.HTTP_200_OK
#             return {}
        
#         board = games[game].board

#         response.status_code = status.HTTP_200_OK
#         return repr(board)
#     except Exception as e:
#         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#         return {'Error': e}
