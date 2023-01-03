import config
import requests
import random
from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625


class Game(metaclass=MultipleMeta):
    # Private functions
    def __init__(self):
        response = requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game')
        self.id = response.json()['id']
        self.players = {'US': None, 'EU': None, 'Russia': None, 'China': None}
        self.playingOrder = [] # Will store the order in which the players have to play in the current round (defined after the last player plays his header card)
        self.playingOrderCurrent = []
        self.isStarted = False
        self.isHeaderPhase = False
        self.isFinished = False

    def __repr__(self):
        return self.id
    
    def __del__(self):
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}')

    # Getters
    def get_players(self):
        return self.players
    
    def get_playingOrder(self):
        return self.playingOrder
    
    def get_isStarted(self):
        return self.isStarted
    
    def get_isHeaderPhase(self):
        return self.isHeaderPhase

    def get_isFinished(self):
        return self.isFinished

    # Setters
    def set_player_user(self, player, user):
        if player in self.players:
            self.players[player] = user
            return True
        return False

    def start(self):
        # Remove the players that have not been chosen
        [self.players.pop(playerToRemove, None) for playerToRemove in [player for player in self.players if self.players[player] == None]]

        # Only allow 2, 3 and 4 player games
        if len(self.players) not in [2, 3, 4]:
            return False

        # Get the number of cards that each player will have (depends on the number of players)
        self.cardsPerPlayer = {2:7, 3:5, 4:4}[len(self.players)]

        # Give each player as many cards as he needs
        for player in self.players:
            self.cards_deal(player)

        # Start the game (in the header phase)
        self.isHeaderPhase = True
        self.isStarted = True

        return True

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

    def board_map_get(self):
        return requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board').json()
    
    def cards_deal(self, player):
        cards = []

        # Get the current number of cards of the player
        cardsPlayer = len(requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}').json())

        # Call the main deck self.cardsPerPlayer times in random order and get the first card
        for i in range(0, self.cardsPerPlayer - cardsPlayer):
            card = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()[0]['id']

            # Cannot have the same card twice
            while card in cards:
                card = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()[0]['id']
            
            cards.append(card)

        # Remove those cards from the main deck and add them to the player's hand
        for card in cards:
            requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/{card}')
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/{card}')

    def cards_playing_header_set(self, player, id):
        requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header/{id}')

        # Check if all the players have their header cards set
        count = len(self.players)
        for player in self.players:
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id'] != None:
                count -= 1

        # If so,
        if count == 0:
            # End the header phase
            self.isHeaderPhase = False

            # Set the playing order
            order = {}
            for player in self.players:
                header = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id']
                print(header)
                header = self.card_get(header)['points']
                print(header)
                order[header] = player

            for card in sorted(list(order.keys()))[::-1]:
                self.playingOrder.append(order[card])
                self.playingOrderCurrent.append(order[card])
                # self.playingOrder and self.playingOrderCurrent will look something like ['US', 'Russia'...]

    def is_players_turn(self, player):
        if len(self.playingOrderCurrent) > 0 and self.playingOrderCurrent[0] == player:
            return True
        return False
    
    def is_another_player_with_edge(self, player, country):
        if country['influence'] == {}:
            return False
        else:
            # Get the influence of the player
            influence = country['influence'].get(player, {'influence': 0})['influence']

            # Check if another player has more influence
            for anotherPlayer in [eachPlayer for eachPlayer in country['influence'] if eachPlayer != player]:
                if country['influence'][anotherPlayer]['influence'] > influence:
                    return True
            
            return False

    def check_if_next_players_turn_and_if_next_round(self):
        # If there are players left to play his turn
        if len(self.playingOrderCurrent > 0):
            # Pass the turn to the next player
            self.playingOrderCurrent.pop(0)
        # If there are no players left
        else:
            # The round has ended, new round must begin
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round')

            # Deal each player as many cards as he needs
            for eachPlayer in self.players:
                self.cards_deal(eachPlayer)

            # Reconstruct the playing order
            self.playingOrderCurrent = [eachPlayer for eachPlayer in self.playingOrder]

    def cards_play_text(self, player, id):
        # PENDING IMPLEMENTATION
        print(self.playingOrderCurrent)
        # If not the player's turn or (header card is set and is trying to play another one), error out
        if self.is_players_turn(player) == False or (self.cards_player_get(player)[player]['header'] != None and self.cards_player_get(player)[player]['header'] != id):
            return False
        
        # Check that the card exists (status==200 and body=={})
        card = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/{id}')
        if card.status_code != 200 or card.json() == {}:
            return False

        # Carry out the pertinent operations according ot the card
        card = card.json()
        if card.id == 1:
            # Roll a dice
            diceRoll = random.choice([1, 2, 3, 4, 5, 6])

            # Get what we have to subtract
            countriesAdjacentAngola = ['Congo', 'South Africa', 'Botswana']
            subtract = 0
            for country in countriesAdjacentAngola:
                countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/{country}').json()
                if self.is_another_player_with_edge(player, countryInfo): subtract += 1
            
            # Subtract
            diceRoll -= subtract

            # If modified dice throw in 3-6
            if diceRoll >= 3:
                # Gain 1 VP
                score = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}').json()
                score['score'] += 1
                requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}', score)

                # If there is influence in Angola
                countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola').json()
                if countryInfo['influence'] != {}:
                    # Remove 1 influence from each other player in Angola
                    for anotherPlayer in [eachPlayer for eachPlayer in country['influence'] if eachPlayer != player]:
                        if countryInfo['influence'][anotherPlayer]['influence'] > 0: countryInfo['influence'][anotherPlayer]['influence'] -= 1
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', countryInfo)

                    # Let's be honest, no one is going to have more than 5 influence over the rest of the players
                    for i in range(0, 5):
                        # Check if another player has the edge in Angola
                        countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola').json()
                        
                        # Add 1 influence to player in Angola
                        if self.is_another_player_with_edge(player, countryInfo):
                            countryInfo['influence'][player]['influence'] += 1
                            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', countryInfo)
                        else:
                            break
                    
                    # Add 1 influence to player in Angola, so he now has the edge in the country
                    countryInfo['influence'][player]['influence'] += 1
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', countryInfo)
        if card.id == 2:
            pass
        if card.id == 3:
            pass
        if card.id == 4:
            pass
        if card.id == 5:
            pass
        if card.id == 6:
            pass
        if card.id == 7:
            pass
        if card.id == 8:
            pass
        if card.id == 9:
            pass
        if card.id == 10:
            pass
        if card.id == 11:
            pass
        if card.id == 12:
            pass
        if card.id == 13:
            pass
        if card.id == 14:
            pass
        if card.id == 15:
            pass
        if card.id == 16:
            pass
        if card.id == 17:
            pass
        if card.id == 18:
            pass
        if card.id == 19:
            pass
        if card.id == 20:
            pass
        if card.id == 21:
            pass
        if card.id == 22:
            pass
        if card.id == 23:
            pass
        if card.id == 24:
            pass
        if card.id == 25:
            pass
        if card.id == 26:
            pass
        if card.id == 27:
            pass
        if card.id == 28:
            pass
        if card.id == 29:
            pass
        if card.id == 30:
            pass
        if card.id == 31:
            pass
        if card.id == 32:
            pass
        if card.id == 33:
            pass
        if card.id == 34:
            pass
        if card.id == 35:
            pass
        if card.id == 36:
            pass
        if card.id == 37:
            pass
        if card.id == 38:
            pass
        if card.id == 39:
            pass
        if card.id == 40:
            pass
        if card.id == 41:
            pass
        if card.id == 42:
            pass
        if card.id == 43:
            pass
        if card.id == 44:
            pass
        if card.id == 45:
            pass
        if card.id == 46:
            pass
        if card.id == 47:
            pass
        if card.id == 48:
            pass
        if card.id == 49:
            pass
        if card.id == 50:
            pass
        if card.id == 51:
            pass
        if card.id == 52:
            pass
        if card.id == 53:
            pass
        if card.id == 54:
            pass
        if card.id == 55:
            pass
        if card.id == 56:
            pass
        if card.id == 57:
            pass
        if card.id == 58:
            pass
        if card.id == 59:
            pass
        if card.id == 60:
            pass
        if card.id == 61:
            pass
        if card.id == 62:
            pass
        if card.id == 63:
            pass
        if card.id == 64:
            pass
        if card.id == 65:
            pass
        if card.id == 66:
            pass
        if card.id == 67:
            pass
        if card.id == 68:
            pass
        if card.id == 69:
            pass
        if card.id == 70:
            pass
        if card.id == 71:
            pass
        if card.id == 72:
            pass
        if card.id == 73:
            pass
        if card.id == 74:
            pass
        if card.id == 75:
            pass
        if card.id == 76:
            pass
        if card.id == 77:
            pass
        if card.id == 78:
            pass
        if card.id == 79:
            pass
        if card.id == 80:
            pass
        if card.id == 81:
            pass
        if card.id == 82:
            pass
        if card.id == 83:
            pass
        if card.id == 84:
            pass
        if card.id == 85:
            pass
        if card.id == 86:
            pass
        if card.id == 87:
            pass
        if card.id == 88:
            pass
        # These next ones do not exist (yet)
        # if card.id == 89:
        #     pass
        # if card.id == 90:
        #     pass
        # if card.id == 91:
        #     pass
        # if card.id == 92:
        #     pass
        # if card.id == 93:
        #     pass
        # if card.id == 94:
        #     pass
        # if card.id == 95:
        #     pass
        # if card.id == 96:
        #     pass
        # if card.id == 97:
        #     pass
        if card.id == 98:
            pass
        if card.id == 99:
            pass
        if card.id == 100:
            pass
        else:
            return False
        
        # Remove the card from the player's hand
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/{id}')
        
        # Remove the card from the player's header (if header == card)
        isHeader = False
        if self.cards_player_get(player)[player]['header'] == id:
            isHeader = True
            requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header')

        # TODO: Check if the card has to be kept on the board (put this card in play), and if so, add it to /cards/playing and do not send it to any deck
        # TODO: For this, add flag = True in the if section for the cards that have to be kept on the board
        # If card['remove'] == true, send card to the removed deck, otherwise send to the discarded deck
        if card['remove'] == True:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/removed/{id}')
        else:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/{id}')

        # If the header card was played or if the player only has 1 card left
        if isHeader == True or len(self.cards_player_get(player)[player]['hand']) == 1:
            self.check_if_next_players_turn_and_if_next_round()

        return True
            