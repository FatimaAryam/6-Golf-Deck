import random

class CardGameLogic:
    def __init__(self):
        self.suits = ['C', 'D', 'H', 'S']
        self.ranks = [str(n) for n in range(2, 11)] + ['J', 'Q', 'K', 'A']
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.player1_cards = []
        self.player2_cards = []
        self.deal_cards()

    def create_deck(self):
        return [f"{rank}{suit}" for suit in self.suits for rank in self.ranks]

    def deal_cards(self):
        self.player1_cards = random.sample(self.deck, 6)
        self.player2_cards = random.sample(self.deck, 6)

    def calculate_score(self, cards):
        score = 0
        for card in cards:
            rank = card[:-1]  # Get the rank (e.g., '2' from '2H')
            if rank in '23456789':
                score += int(rank)  # Number cards
            elif rank in ['J', 'Q', 'K']:
                score += 10  # Face cards
            elif rank == 'A':
                score += 1  # Ace
        return score

    def get_scores(self):
        player1_score = self.calculate_score(self.player1_cards)
        player2_score = self.calculate_score(self.player2_cards)
        return player1_score, player2_score
