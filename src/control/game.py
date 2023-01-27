import logging
import config
import requests
import random
from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625


# Define the logger
logger = logging.getLogger('control_logger')


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
        self.isPostHeaderPhase = False
        self.destabilization = None
        self.isFinished = False

    def __init__(self, id: str):
        self.id = id
        self.players = {'US': None, 'EU': None, 'Russia': None, 'China': None}
        self.playingOrder = []
        self.playingOrderCurrent = []
        self.isStarted = False
        self.isHeaderPhase = False
        self.isPostHeaderPhase = False
        self.destabilization = None
        self.isFinished = False

    def __repr__(self):
        return self.id
    
    def __del__(self):
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}')

    #
    # Getters
    def get_players(self):
        return self.players
    
    def get_playingOrder(self):
        return self.playingOrder
    
    def get_playingOrderCurrent(self):
        return self.playingOrderCurrent
    
    def get_isStarted(self):
        return self.isStarted
    
    def get_isHeaderPhase(self):
        return self.isHeaderPhase

    def get_isPostHeaderPhase(self):
        return self.isPostHeaderPhase

    def get_destabilization(self):
        return self.destabilization

    def get_isFinished(self):
        return self.isFinished

    #
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
        if len(self.players) not in [2, 3, 4]: return False

        # Get the number of cards that each player will have (depends on the number of players)
        self.cardsPerPlayer = {2:7, 3:5, 4:4}[len(self.players)]

        # Give each player as many cards as he needs
        for player in self.players:
            self.deal_cards_player(player)

        # Start the game (in the header phase)
        self.isHeaderPhase = True
        self.isStarted = True

        return True

    def finish(self):
        self.isFinished = True
    
    #
    # Helper functions
    def deal_cards_player(self, player):
        cards = []

        # Get the current number of cards of the player
        cardsPlayer = len(requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}').json())

        # If the main deck has less than self.cardsPerPlayer-cardsPlayer cards, put the discarded cards back into the main deck
        if len(requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()) < self.cardsPerPlayer - cardsPlayer:
            logger.debug(f'There are not enough cards in the main deck to be able to deal to player {player}, shuffleling discarded deck into the main deck')
            for card in requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded').json():
                requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/' + str(card['id']))
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/' + str(card['id']))

        # If the current round is round 5 and there are no cards of the post era in the main deck, add them to it
        mainDeckCards = [card['id'] for card in requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main').json()]
        postEraCards = [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 100]
        if not any (card in postEraCards for card in mainDeckCards) and requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] == 5:
            logger.debug(f'Round 5, shuffleing post era cards into the main deck')
            for card in postEraCards:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/{card}')

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
    
    def is_players_turn(self, player):
        if len(self.playingOrderCurrent) > 0 and self.playingOrderCurrent[0] == player:
            return True
        return False
    
    def is_player_with_edge(self, player, country):
        if country['influence'] == {}:
            return False
        else:
            # Get the influence of the player
            influence = country['influence'].get(player, {'influence': 0})['influence']

            # Check if another player has more or the same influence
            for anotherPlayer in [eachPlayer for eachPlayer in country['influence'] if eachPlayer != player]:
                if country['influence'][anotherPlayer]['influence'] >= influence:
                    return False
            
            return True

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
    
    def increment_player_score(self, player, increment):
        score = self.board_score_get()

        # Increment the score
        if increment !=0:
            for eachPlayer in score:
                if eachPlayer['name'] == player:
                    eachPlayer['score'] += increment

                    # If score is negative, share the VP among the rest of the players, starting from the player of his block if any
                    if eachPlayer['score'] < 0:
                        rest = eachPlayer['score'] * -1
                        eachPlayer['score'] = 0

                        # Sort the players from lowest to highest score
                        score = sorted(score, key=lambda x: x['score'])

                        # Start from your block if any
                        for key, val in {'US': 'EU', 'EU': 'US', 'China': 'Russia', 'Russia': 'China'}.items():
                            if player == key and val in self.playingOrder:
                                startingPlayer = next(filter(lambda x: x['name'] == val, score))
                                score = list(filter(lambda x: x['name'] != val, score))
                                score.insert(0, startingPlayer) # https://stackoverflow.com/questions/17911091/append-integer-to-beginning-of-list-in-python

                        # Add the points
                        while rest > 0:
                            for eachPlayer in range(0, len(score)):
                                score[eachPlayer]['score'] += 1
                                rest -= 1
                                if rest < 1: break
                        
                        # Update the scores
                        for eachUpdatedPlayer in score:
                            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/' + eachUpdatedPlayer['name'], json={'score': eachUpdatedPlayer['score']})
                    else:
                        # Update the score of the player
                        requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}', json={'score': eachPlayer['score']})

    def handle_players_card(self, player, card):
        id = card['id']
        # Remove the card from the player's hand
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/{id}')
        
        # Remove the card from the player's header (if header == card)
        if self.cards_player_get(player)[player]['header'] == id:
            requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header')

        # If the card has to be kept on the board, send it to playing
        if card['inPlay'] == True:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/{id}')
        else:
            # If card['remove'] == true, send card to the removed deck, otherwise send to the discarded deck
            if card['remove'] == True:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/removed/{id}')
            else:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/{id}')

    def handle_players_play(self, player):
        logger.debug(f'handle_players_play(): ' + f'Called with player={player}')
        # If postHeaderPhase
        if self.isPostHeaderPhase == True:
            logger.debug(f'handle_players_play(): ' + 'Is post header phase')
            # If players left, pass the turn
            if len(self.playingOrderCurrent) > 0:
                logger.debug(f'handle_players_play(): ' + 'There are players left, passing the turn to the next one')
                self.playingOrderCurrent.pop(0)
        # If not postHeaderPhase
        else:
            logger.debug(f'handle_players_play(): ' + 'Is NOT post header phase')
            # If players left and the actual player has only 1 card in his hand, pass the turn
            if len(self.playingOrderCurrent) > 0:
                logger.debug(f'handle_players_play(): ' + 'There are players left')
                logger.debug(f'handle_players_play(): Cards of the player {player}: ' + str(self.cards_player_get(player)[player]))
                if len(self.cards_player_get(player)[player]['hand']) == 1:
                    logger.debug(f'handle_players_play(): ' + 'the current player has only 1 card left in his hand, passing the turn to the next one')
                    self.playingOrderCurrent.pop(0)
        
        # If there are no players left to play in this turn
        logger.debug(f'handle_players_play(): Playing order current: ' + str(self.playingOrderCurrent))
        if len(self.playingOrderCurrent) == 0:
            logger.debug(f'handle_players_play(): ' + 'There are no players left to play')
            # If not in the postHeaderPhase
            if self.isPostHeaderPhase == False:
                
                # If round == 8, finish the game
                if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] >= 8:
                    logger.debug(f'handle_players_play(): Finishing the game')
                    return self.finish()
                
                logger.debug(f'handle_players_play(): ' + 'Starting a new round')
                # New round must begin
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round')

                # Deal each player as many cards as he needs
                for eachPlayer in self.players:
                    logger.debug(f'handle_players_play(): ' + f'Dealing cards to player {eachPlayer}')
                    self.deal_cards_player(eachPlayer)
                
                # Start the next round in the header phase
                logger.debug(f'handle_players_play(): Setting the header phase')
                self.isHeaderPhase = True
            
            # If post header phase, end it
            else:
                logger.debug(f'handle_players_play(): Unsetting the post header phase')
                self.isPostHeaderPhase = False

            # Always reconstruct the playing order
            logger.debug(f'handle_players_play(): ' + 'Reconstructing the playing order')
            if len(self.playingOrderCurrent) == 0:
                self.playingOrderCurrent = [eachPlayer for eachPlayer in self.playingOrder]
                logger.debug(f'handle_players_play(): ' + f'New playing order: {str(self.playingOrderCurrent)}')

    #
    # Logic functions
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

        # Remove cards if we are not in the header phase and if everyone has header=null
        if self.get_isHeaderPhase() == True or len([player for player in cards if cards[player]['header'] == None]) == len(self.playingOrder):
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
    
    def cards_playing_header_set(self, player, id):
        requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header/{id}')

        # Check if all the players have their header cards set
        count = len(self.players)
        for player in self.players:
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id'] != None:
                count -= 1

        # If so,
        if count == 0:
            # End the header phase and start the postheader phase
            self.isHeaderPhase = False
            self.isPostHeaderPhase = True

            # Set the playing order
            order = []
            self.playingOrder = []
            self.playingOrderCurrent = []
            for player in self.players:
                header = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id']
                header = self.card_get(header)['points']
                order.append({'player': player, 'points': header})

            for card in sorted(order, key=lambda x: x['points'])[::-1]:
                self.playingOrder.append(card['player'])
                self.playingOrderCurrent.append(card['player'])
                # self.playingOrder and self.playingOrderCurrent will look something like ['US', 'Russia'...]

    def cards_play_influence(self, player, id, body, validate=False):
        # If not the player's turn
        if self.is_players_turn(player) == False: return False

        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False

        # Get all the countries of the map
        countriesAll = self.board_map_get()['countries']
        
        #
        # Count all the points that the user wants to use
        pointCount = 0
        for target in body['targets']:
            # Get the name and the object of the country
            targetName = next(iter(target['target'])) # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
            targetObject = next(filter(lambda x: x['name'] == targetName, countriesAll))

            # Check if the country that the player wants to influence already has player influence or is adjacent to one that is
            isCountryAdjacentOrWithInfluence = False
            if player not in targetObject['influence']:
                # If no influence in this country, check the adjacent countries
                for eachCountry in targetObject['adjacent']:
                    country = next(filter(lambda x: x['name'] == eachCountry, countriesAll))
                    if player in country['influence'] and country['influence'][player]['influence'] > 0:
                        isCountryAdjacentOrWithInfluence = True
            else:
                isCountryAdjacentOrWithInfluence = True

            # Return if player has no influence in this or in the adjacent countries
            if isCountryAdjacentOrWithInfluence == False: return False

            # Count the influence points + stability of the country
            pointCount += target['target'][targetName]
            pointCount += targetObject['stability']

            # If extra target was specified, count those points too
            if target['targetExtra'] != None:
                for extraTarget in target['targetExtra']:
                    # A player cannot have extra influence on himself
                    if extraTarget == player: return False

                    pointCount += target['targetExtra'][extraTarget]
            
            # Count if another player has the edge (more influence than the actual player)
            if len([eachPlayer for eachPlayer in targetObject['influence'] if eachPlayer != player and targetObject['influence'].get(eachPlayer, {'influence': 0})['influence'] > targetObject['influence'].get(player, {'influence': 0})['influence']]) > 0:
                pointCount += 1

        #
        # Apply modifications to each country (if there are no prohibitions)
        countries = {}
        for target in body['targets']:
            targetName = next(iter(target['target']))
            targetObject = next(filter(lambda x: x['name'] == targetName, countriesAll))
            
            # Add the country to the list of countries
            countries[targetName] = targetObject

            # Initialize the country if empty
            if countries[targetName]['influence'].get(player, None) == None:
                countries[targetName]['influence'][player] = {'influence': 0, 'extra': {}}

            influencePointsToSum = target['target'][targetName]
            
            # Check if there is another player with extra influence over this player. If one slot is occupied, can only occupy the other. If both slots are occupied, cannot play influence or destabilization ops at all
            influencePointsUsed = 0
            for eachPlayer, eachInfluence in countries[targetName]['influence'].items():
                # Sum the extra influence of other players over this player
                if 'extra' in eachInfluence:
                    if player in eachInfluence['extra']:
                        influencePointsUsed += eachInfluence['extra'][player]
            
            # Check if the current influence + the extra influence from other players + the influence to sum is > 2
            if countries[targetName]['influence'][player]['influence'] + influencePointsUsed + influencePointsToSum > 2: return False

            # Modify the player's influence over the country using the request body
            countries[targetName]['influence'][player]['influence'] += influencePointsToSum

            # Modify the extra influence of the country using the request body
            if target['targetExtra']:
                for extraTarget in target['targetExtra']:
                    # Check if the country has x influence so x+target['targetExtra'][extraTarget] is <=2
                    if countries[targetName]['influence'].get(extraTarget, {'influence': 0, 'extra': {}})['influence'] + target['targetExtra'][extraTarget] > 2: return False

                    # Add the extra influence
                    countries[targetName]['influence'][player]['extra'] = {extraTarget: target['targetExtra'][extraTarget]}

        #
        # If only validate, return here
        if validate == True: return True

        # If all went good, update the countries in the resources service
        for eachCountry in countries:
            region = countries[eachCountry]['region']
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{region}/{eachCountry}', json=countries[eachCountry])
        
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        
        return True

    def cards_play_destabilization(self, player, id, body, validate=False):
        # If not the player's turn
        if self.is_players_turn(player) == False: return False

        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False
        
        # Check that the requested country exists and get its data
        country = body['target']
        countriesAll = self.board_map_get()['countries']
        country = [eachCountry for eachCountry in countriesAll if eachCountry['name'] == country]
        if len(country) < 1: return False
        country = country[0]

        # The target country cannot be a country that belongs to another player
        if country['name'] in ['United States', 'United Kingdom', 'Benelux', 'Denmark', 'Germany', 'France', 'Spain/Portugal', 'Italy', 'Greece', 'Russia', 'China']: return False

        # There has to be influence from another player
        if country['influence'] == {} or len([anotherPlayer for anotherPlayer in country['influence'] if anotherPlayer != player]) == 0: return False

        #
        # If this is the first request
        if self.destabilization == None:
            # Do the dice throw and all the operations
            diceRoll = random.choice([1, 2, 3, 4, 5, 6]) + card['points'] - country['stability'] * 2

            # If the country is conflictive, lose 1 VP
            if country['isConflictive'] == True:
                # newScore = [score for score in self.board_score_get() if score['name'] == player][0]['score'] - 1 # We don't need this
                self.increment_player_score(player, -1)

            # If only validate
            if validate == True:
                print('returning the dice roll')
                return diceRoll

            # If player was lucky
            if diceRoll > 0:
                # Set self.destabilization
                self.destabilization = {'country': country['name'], 'result': diceRoll}

                # Do not remove the player's card or do anything with the turn

                return True
            else:
                # The player lost this card, so we continue with the game
                
                # Handle the player's played card
                self.handle_players_card(player, card)

                # Handle the player's play
                self.handle_players_play(player)

                # Return the result of the dice throw
                return diceRoll

        #
        # If this is the second request
        else:
            if self.destabilization['country'] != body['target']: return False

            # Cannot add influence to contrary block
            west = ['US', 'EU']
            east = ['China', 'Russia']
            if body['add'] == None: body['add'] = []
            if body['remove'] == None: body['remove'] = []
            countriesAddInfluence = [next(iter(target)) for target in body['add']]
            countriesRemoveInfluence = [next(iter(target)) for target in body['remove']]
            if player in west:
                if any (target in east for target in countriesAddInfluence): # https://stackoverflow.com/questions/62115746/can-i-check-if-a-list-contains-any-item-from-another-list
                    return False
                if any (target in west for target in countriesRemoveInfluence):
                    return False
            else:
                if any (target in west for target in countriesAddInfluence):
                    return False
                if any (target in east for target in countriesRemoveInfluence):
                    return False

            #
            #
            pointCount = 0
            # Check the influence to add
            for target in body['add']:
                # Cannot have more than 2 of influence
                if country['influence'].get(next(iter(target)), {'influence': 0})['influence'] + target[next(iter(target))] > 2: return False
                
                # Update the influence
                if country['influence'].get(next(iter(target)), None) == None:
                    country['influence'][next(iter(target))] = {'influence': 0, 'extra': {}}
                newInfluence = country['influence'][next(iter(target))]['influence'] + target[next(iter(target))]
                country['influence'][next(iter(target))]['influence'] = newInfluence

                # Update the point count
                pointCount += target[next(iter(target))]
            
            # Check the influence to remove
            for target in body['remove']:
                # Cannot have less than 0 of influence
                if country['influence'].get(next(iter(target)), {'influence': 0})['influence'] - target[next(iter(target))] < 0: return False
                
                # Update the influence
                if country['influence'].get(next(iter(target)), None) == None:
                    country['influence'][next(iter(target))] = {'influence': 0, 'extra': {}}
                newInfluence = country['influence'][next(iter(target))]['influence'] - target[next(iter(target))]
                country['influence'][next(iter(target))]['influence'] = newInfluence

                # Update the point count
                pointCount += target[next(iter(target))]
            
            # Cannot spend more points than diceRoll
            if pointCount > self.destabilization['result']: return False
            
            #
            # If only validate
            if validate == True: return True

            # Update the country
            countryName = country['name']
            countryRegion = country['region']
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{countryRegion}/{countryName}', json=country)
            
            # Unset the destabilization for the next destabilization play
            self.destabilization = None
            
            # Handle the player's played card
            self.handle_players_card(player, card)

            # Handle the player's play
            self.handle_players_play(player)
        
        return True

    def cards_play_text(self, player, id):
        # If not the player's turn or (header card is set and is trying to play another one), error out
        if self.is_players_turn(player) == False or (self.cards_player_get(player)[player]['header'] != None and self.cards_player_get(player)[player]['header'] != id): return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False

        # Carry out the pertinent operations according to the card
        if card['id'] == 1:
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
            print(f'Modified dice throw: {diceRoll}')
            if diceRoll >= 3:
                # Gain 1 VP
                score = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}').json()
                score['score'] += 1
                requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}', json=score)

                # If there is influence in Angola
                countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola').json()
                if countryInfo['influence'] != {}:
                    # Remove 1 influence from each other player in Angola
                    for anotherPlayer in [eachPlayer for eachPlayer in countryInfo['influence'] if eachPlayer != player]:
                        if countryInfo['influence'][anotherPlayer]['influence'] > 0: countryInfo['influence'][anotherPlayer]['influence'] -= 1
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', json=countryInfo)

                    # Let's be honest, no one is going to have more than 5 influence over the rest of the players
                    for i in range(0, 5):
                        # Check if another player has the edge in Angola
                        countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola').json()
                        
                        # Create the influence object for the player
                        if countryInfo['influence'].get('influence', None) == None:
                            countryInfo['influence'][player] = {'influence': 0, 'extra': {}}
                            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', json=countryInfo)
                        
                        # Add 1 influence to player in Angola
                        if self.is_another_player_with_edge(player, countryInfo):
                            countryInfo['influence'][player]['influence'] += 1
                            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', json=countryInfo)
                        else:
                            break
                    
                    # Add 1 influence to player in Angola, so he now has the edge in the country
                    countryInfo = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola').json()
                    if not self.is_player_with_edge(player, countryInfo):
                        countryInfo['influence'][player]['influence'] += 1
                        requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Africa/Angola', json=countryInfo)
        # TODO: IMPLEMENT LOGIC FOR THE REST OF THE CARDS
        elif card['id'] == 2:
            pass
        elif card['id'] == 3:
            pass
        elif card['id'] == 4:
            pass
        elif card['id'] == 5:
            pass
        elif card['id'] == 6:
            pass
        elif card['id'] == 7:
            pass
        elif card['id'] == 8:
            pass
        elif card['id'] == 9:
            pass
        elif card['id'] == 10:
            pass
        elif card['id'] == 11:
            pass
        elif card['id'] == 12:
            pass
        elif card['id'] == 13:
            pass
        elif card['id'] == 14:
            pass
        elif card['id'] == 15:
            pass
        elif card['id'] == 16:
            pass
        elif card['id'] == 17:
            pass
        elif card['id'] == 18:
            pass
        elif card['id'] == 19:
            pass
        elif card['id'] == 20:
            pass
        elif card['id'] == 21:
            pass
        elif card['id'] == 22:
            pass
        elif card['id'] == 23:
            pass
        elif card['id'] == 24:
            pass
        elif card['id'] == 25:
            pass
        elif card['id'] == 26:
            pass
        elif card['id'] == 27:
            pass
        elif card['id'] == 28:
            pass
        elif card['id'] == 29:
            pass
        elif card['id'] == 30:
            pass
        elif card['id'] == 31:
            pass
        elif card['id'] == 32:
            pass
        elif card['id'] == 33:
            pass
        elif card['id'] == 34:
            pass
        elif card['id'] == 35:
            pass
        elif card['id'] == 36:
            pass
        elif card['id'] == 37:
            pass
        elif card['id'] == 38:
            pass
        elif card['id'] == 39:
            pass
        elif card['id'] == 40:
            pass
        elif card['id'] == 41:
            pass
        elif card['id'] == 42:
            pass
        elif card['id'] == 43:
            pass
        elif card['id'] == 44:
            pass
        elif card['id'] == 45:
            pass
        elif card['id'] == 46:
            pass
        elif card['id'] == 47:
            pass
        elif card['id'] == 48:
            pass
        elif card['id'] == 49:
            pass
        elif card['id'] == 50:
            pass
        elif card['id'] == 51:
            pass
        elif card['id'] == 52:
            pass
        elif card['id'] == 53:
            pass
        elif card['id'] == 54:
            pass
        elif card['id'] == 55:
            pass
        elif card['id'] == 56:
            pass
        elif card['id'] == 57:
            pass
        elif card['id'] == 58:
            pass
        elif card['id'] == 59:
            pass
        elif card['id'] == 60:
            pass
        elif card['id'] == 61:
            pass
        elif card['id'] == 62:
            pass
        elif card['id'] == 63:
            pass
        elif card['id'] == 64:
            pass
        elif card['id'] == 65:
            pass
        elif card['id'] == 66:
            pass
        elif card['id'] == 67:
            pass
        elif card['id'] == 68:
            pass
        elif card['id'] == 69:
            pass
        elif card['id'] == 70:
            pass
        elif card['id'] == 71:
            pass
        elif card['id'] == 72:
            pass
        elif card['id'] == 73:
            pass
        elif card['id'] == 74:
            pass
        elif card['id'] == 75:
            pass
        elif card['id'] == 76:
            pass
        elif card['id'] == 77:
            pass
        elif card['id'] == 78:
            pass
        elif card['id'] == 79:
            pass
        elif card['id'] == 80:
            pass
        elif card['id'] == 81:
            pass
        elif card['id'] == 82:
            pass
        elif card['id'] == 83:
            pass
        elif card['id'] == 84:
            pass
        elif card['id'] == 85:
            pass
        elif card['id'] == 86:
            pass
        elif card['id'] == 87:
            pass
        elif card['id'] == 88:
            pass
        # These next ones do not exist (yet)
        # elif card['id'] == 89:
        #     pass
        # elif card['id'] == 90:
        #     pass
        # elif card['id'] == 91:
        #     pass
        # elif card['id'] == 92:
        #     pass
        # elif card['id'] == 93:
        #     pass
        # elif card['id'] == 94:
        #     pass
        # elif card['id'] == 95:
        #     pass
        # elif card['id'] == 96:
        #     pass
        # elif card['id'] == 97:
        #     pass
        elif card['id'] == 98:
            pass
        elif card['id'] == 99:
            pass
        elif card['id'] == 100:
            pass
        else:
            return False
        
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)

        return True
    
    def cards_play_score(self, player, id, body, validate=False):
        # If not the player's turn
        if self.is_players_turn(player) == False: return False

        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False
        
        # It has to be a punctuation card
        if card['type'] != 'Punctuation': return False

        # Get the board
        board = self.board_map_get()

        # The region has to exist
        if body['region'] not in board['regions']: return False

        # If only validate, return here
        if validate == True: return True
        
        # Get the countries of the specified region
        countries = [country for country in board['countries'] if country['region'] == body['region']]

        #
        # Evaluate presence
        for eachPlayer in self.playingOrder:
            countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]
            if len(countriesEdged) > 0:
                self.increment_player_score(eachPlayer, board['regionScoring'][body['region']]['presence'])

        #
        # Evaluate domination
        domination = {}
        for eachPlayer in self.playingOrder:
            countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]
            
            conflictive = False
            nonConflictive = False

            for country in countriesEdged:
                if country['isConflictive']: conflictive = True
                if not country['isConflictive']: nonConflictive = True
            
            # Store the number of countries that the player has the edge in and if at least one country is conflictive and at least another one is not, from within the countries that he has the edge in
            domination[player] = {'count': len(countriesEdged), 'domination': False}
            if conflictive and nonConflictive: domination[player]['domination': True]

        # If there is a player with more countries edged than any other
        points = [domination[player]['count'] for player in domination]
        if points.count(max(points)) == 1:
            
            for key, val in domination.items():
                
                # Find the player more countries edged than any other
                if val['count'] == max(points):
                    
                    if val['domination'] == True:
                        self.increment_player_score(key, board['regionScoring'][body['region']]['domination'])

        #
        # Evaluate control
        control = {}
        for eachPlayer in self.playingOrder:
            countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]

            nonConflictive = False

            for country in countriesEdged:
                if not country['isConflictive']: nonConflictive = True
            
            # Store the number of countries that the player has the edge in and if at least one country is non conflictive, from within the countries that he has the edge in
            control[player] = {'count': len(countriesEdged), 'control': False}
            if conflictive and nonConflictive: control[player]['control': True]

        # If there is a player with more countries edged than any other
        points = [control[player]['count'] for player in control]
        if points.count(max(points)) == 1:
            
            for key, val in control.items():
                
                # Find the player more countries edged than any other
                if val['count'] == max(points):
                    
                    # If player has edge in non conflictive country and also has edge in all confilctive countries
                    if val['control'] == True and val['count'] >= len([country for country in countries if country['isConflictive']]):
                        self.increment_player_score(key, board['regionScoring'][body['region']]['control'])

        #
        # Evaluate conflictive countries
        for eachPlayer in self.playingOrder:
            conflictiveCountriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country) and country['isConflictive']]
            self.increment_player_score(eachPlayer, len(conflictiveCountriesEdged))

        #
        # Evaluate countries edged by another players that are adjacent to the player's superpower countries. The player also loses 1 VP per each of his superpower countries edged by another player
        for key, val in {'US': ['United States'], 'EU': ['United Kingdom', 'Benelux', 'Denmark', 'Germany', 'France', 'Spain/Portugal', 'Italy', 'Greece'], 'China': ['China'], 'Russia': ['Russia']}.items():
            if key not in self.playingOrder: continue

            pointsToLose = -len([country for country in countries if self.is_another_player_with_edge(key, country) and any(c in country['adjacent'] for c in val)])
            pointsToLose -= len([c for c in val if self.is_another_player_with_edge(key, next(iter([country for country in board['countries'] if country['name'] == c])))])
            if pointsToLose != 0:
                self.increment_player_score(key, pointsToLose)
        
        #
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        
        return True

    def cards_play_nwo(self, player, id, body, validate=False):
        # If not the player's turn
        if self.is_players_turn(player) == False: return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False

        # Get the board
        board = self.board_map_get()

        # The nwo track slot has to exist
        slotsNames = []
        [slotsNames.extend(list(slot.keys())) for slot in list(board['nwo'].values())]
        if body['name'] not in slotsNames: return False

        # Find the track and the slot
        for track in board['nwo']:
            for slot in board['nwo'][track]:
                
                if slot == body['name']:
                    
                    # Check if there is a veto against this player or if there is another player in the ahead field
                    if board['nwo'][track][slot]['veto'] == player or board['nwo'][track][slot]['ahead'] in [anotherPlayer for anotherPlayer in self.playingOrder if anotherPlayer != player]:
                        return False

                    # If only validate, return here
                    if validate == True: return True

                    # Remove the veto and the ahead from the nwo track slot
                    board['nwo'][track][slot]['veto'] = board['nwo'][track][slot]['ahead'] = ''

                    # If there was supremacy, remove it, otherwise, give it to the player
                    if board['nwo'][track][slot]['supremacy'] != '':
                        board['nwo'][track][slot]['supremacy'] = ''
                    else:
                        board['nwo'][track][slot]['supremacy'] = player

                    # Update the track slot
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/{track}/{slot}', json=board['nwo'][track][slot])

        #
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        
        return True
