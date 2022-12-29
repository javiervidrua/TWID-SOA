import config
import requests
from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625
from shortuuid import ShortUUID


class Game(metaclass=MultipleMeta):
    # Private functions
    def __init__(self):
        response = requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game')
        self.id = response.json()['id']
        self.players = {'US': None, 'EU': None, 'Russia': None, 'China': None}
        self.isStarted = False
        self.isFinished = False

    def __repr__(self):
        return self.id
    
    def __del__(self):
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}')

    # Getters
    def get_isStarted(self):
        return self.isStarted

    def get_isFinished(self):
        return self.isFinished

    def get_players(self):
        return self.players

    # Setters
    def set_player_user(self, player, user):
        if player in self.players:
            self.players[player] = user
            return True
        return False

    def start(self):
        self.isStarted = True

    def finish(self):
        self.isFinished = True
    
    # Common functions
    def card_get(self, id):
        response = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/{id}')
        return response.json()
    
    def cards_player_get(self, requestingPlayer):
        # Prepare the cards object
        cards = {}
        for player in [player for player in self.players if self.players[player]!=None]:
            cards[player] = {'header': None, 'hand': []}

        # Obtain the cards of all players
        for player in cards:
            # Only show the hand of the requesting player
            if player == requestingPlayer:
                hand = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}').json()
                [cards[player]['hand'].append(card['id']) for card in hand]

            # Get all the headers 
            header = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()
            if header['id'] != None:
                cards[player]['header'] = header['id']

        # Only show the header cards if everyone has selected their header card
        if len([player for player in cards if cards[player]['header'] != None]) != len(list(cards.keys())):
            for player in cards:
                if player != requestingPlayer: cards[player]['header'] = None

        return cards
    
    def cards_playing_get(self):
        playing = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
        return [card['id'] for card in playing]

    def board_round_get(self):
        return requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()
    
    def board_score_get(self):
        score = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score').json()
        
        # Only show the score of the players of the game. e.g: IF there are 3 players, do not show 4 scores
        score = [playerScore for playerScore in score if playerScore['name'] in [player for player in self.players if self.players[player] != None]]
        return score
