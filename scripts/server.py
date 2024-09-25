import socket
import threading
import pickle  # To send/receive objects
from game_logic import SixCardGolfGame  # Import your existing game logic

class SixCardGolfServer:
    def __init__(self, host='localhost', port=5555, max_players=2):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        print(f"Server started on {host}:{port}")
        
        self.clients = []
        self.max_players = max_players
        self.game = None
        self.start_game()

    def start_game(self):
        print("Waiting for players to join...")
        player_number = 1
        while len(self.clients) < self.max_players:
            client_socket, client_address = self.server.accept()
            print(f"Player {player_number} connected from {client_address}")
            self.clients.append((client_socket, player_number))  # Store player number
            threading.Thread(target=self.handle_client, args=(client_socket, player_number)).start()
            player_number += 1

        # Initialize the game once all players have joined
        self.game = SixCardGolfGame()
        self.broadcast_game_state()
        print("Game started!")

    def handle_client(self, client_socket, player_number):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                action = pickle.loads(data)
                self.process_action(client_socket, action, player_number)
            except ConnectionResetError:
                break
        
        print(f"Player {player_number} disconnected")
        self.clients = [(c, n) for c, n in self.clients if c != client_socket]
        client_socket.close()

    def process_action(self, client_socket, action, player_number):
        # Check if it's the current player's turn
        if self.game.current_player != player_number:
            print(f"Player {player_number} tried to act out of turn.")
            response = {'type': 'error', 'message': "It's not your turn!"}
            client_socket.send(pickle.dumps(response))
            return
        
        print(f"Processing action '{action['type']}' for Player {player_number}")
        
        if action['type'] == 'draw_card':
            card = self.game.draw_card()
            if card:
                response = {'type': 'card_drawn', 'card': card}
                client_socket.send(pickle.dumps(response))
            self.broadcast_game_state()  # Ensure the game state is broadcasted
        
        elif action['type'] == 'discard_card':
            player_cards = self.game.player1_cards if player_number == 1 else self.game.player2_cards
            card_index = action['card_index']
            
            # Remove the discarded card from the player's row
            if card_index < len(player_cards):
                del player_cards[card_index]
            
            # End the turn and broadcast the game state
            self.game.end_turn()
            self.broadcast_game_state()
        
        elif action['type'] == 'place_card':
            player_cards = self.game.player1_cards if player_number == 1 else self.game.player2_cards
            card = action['card']
            
            # Add the drawn card to the end of the row
            player_cards.append(card)
            
            # Ensure the turn ends after the card is placed
            self.game.end_turn()
            self.broadcast_game_state()

        print(f"Game state updated. It's now Player {self.game.current_player}'s turn.")
        self.check_game_over()

    def check_game_over(self):
        player1_finished = len(self.game.player1_cards) == 0
        player2_finished = len(self.game.player2_cards) == 0

        # If either player has finished, the game should end
        if player1_finished or player2_finished:
            self.calculate_scores_and_notify()

    def calculate_scores_and_notify(self):
        player1_score = self.calculate_score(self.game.player1_cards)
        player2_score = self.calculate_score(self.game.player2_cards)
        
        if player1_score < player2_score:
            winner = f"Player 1 wins with a score of {player1_score} against Player 2's {player2_score}"
        elif player1_score > player2_score:
            winner = f"Player 2 wins with a score of {player2_score} against Player 1's {player1_score}"
        else:
            winner = f"It's a tie! Both players scored {player1_score}"

        final_state = {
            'game_over': True,
            'winner': winner,
            'player1_score': player1_score,
            'player2_score': player2_score
        }

        # Send the final state to all clients
        for client, _ in self.clients:
            client.send(pickle.dumps(final_state))

        print(winner)  # Also print the result on the server console

    def calculate_score(self, cards):
        """ Calculate the score based on remaining face-up cards """
        score = 0
        for card in cards:
            rank = card[:-1]
            if rank.isdigit():
                score += int(rank)
            elif rank == 'A':
                score += 1
            else:  # J, Q, K
                score += 10
        return score

    def broadcast_game_state(self):
        game_state = {
            'current_player': self.game.current_player,
            'player1_cards': self.game.player1_cards,
            'player2_cards': self.game.player2_cards,
            'discard_pile': self.game.get_top_discard_card(),
            'game_over': False
        }
        
        for client, player_number in self.clients:
            personalized_state = game_state.copy()
            personalized_state['player_number'] = player_number
            client.send(pickle.dumps(personalized_state))

if __name__ == "__main__":
    SixCardGolfServer(max_players=2)
