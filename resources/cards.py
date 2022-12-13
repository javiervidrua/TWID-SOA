from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625
import json
from copy import deepcopy

class Cards(metaclass=MultipleMeta):
    def __init__(self):
        # Load all the data from the json file
        with open('cards.json', 'r') as file:
            self.cards = json.load(file)

    def __repr__(self):
        return str([
            {'name': 'deck'},
            {'name': 'playing'},
            {'name': 'player'}
        ])

    def cards_get(self, id):
        return next(filter(lambda x: x['id'] == id, self.cards['cards']), {})
    
    def cards_deck_get(self):
        return [{"type": "main"}, {"type": "discarded"}, {"type": "removed"}]
    
    def cards_deck_get(self, deck: str): # Method overloading possible via MultipleMeta inheritance
        if deck in ['main', 'discarded', 'removed']:
            return deepcopy(self.cards['decks'][deck])
        return []
    
    def cards_deck_add(self, deck, id):
        if deck in ['main', 'discarded', 'removed'] and len([card for card in self.cards['decks'][deck] if card==id])==0:
            self.cards['decks'][deck].append(id)
            return True
        return False
    
    def cards_deck_remove(self, deck, id):
        if deck in ['main', 'discarded', 'removed'] and len([card for card in self.cards['decks'][deck] if card==id])==1:
            self.cards['decks'][deck].remove(id)
            return True
        return False
