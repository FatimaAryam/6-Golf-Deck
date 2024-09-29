import random

class SixCardGolfGame:
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.players_cards = {i: self.deal_cards() for i in range(1, num_players + 1)}
        self.current_player = 1  # Player 1 starts
        self.discard_pile = [self.deck.pop()]  # Start the discard pile with one card

    def create_deck(self):
        """Create a deck of cards."""
        suits = ['C', 'D', 'H', 'S']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [rank + suit for suit in suits for rank in ranks]
        return deck

    def deal_cards(self):
        """Deal six cards to a player."""
        return [self.deck.pop() for _ in range(6)]

    def draw_card(self):
        """Draw a card from the deck."""
        if self.deck:
            return self.deck.pop()
        return None  # Deck is empty

    def discard_card(self, player_id, card):
        """Discard a card from the player's hand."""
        if card in self.players_cards[player_id]:
            self.players_cards[player_id].remove(card)
            self.discard_pile.append(card)

    def end_turn(self):
        """Switch to the next player."""
        self.current_player = (self.current_player % self.num_players) + 1

    def get_top_discard_card(self):
        """Return the top card from the discard pile."""
        return self.discard_pile[-1] if self.discard_pile else None
