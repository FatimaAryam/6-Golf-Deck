import socket
import threading
import pickle  # To send/receive objects
from game_logic import SixCardGolfGame  # Import the existing game logic

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

        # Initialize the game once the desired number of players have joined
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
        if action['type'] == 'draw_card':
            card = self.game.draw_card()
            if card:
                # Send the drawn card back to the player who drew it
                response = {'type': 'card_drawn', 'card': card}
                client_socket.send(pickle.dumps(response))
        
        elif action['type'] == 'discard_card':
            player_cards = self.game.player1_cards if player_number == 1 else self.game.player2_cards
            card_index = action['card_index']
            self.game.discard_card(player_cards, player_cards[card_index])
            self.game.end_turn()
            self.broadcast_game_state()

        elif action['type'] == 'place_card':
            player_cards = self.game.player1_cards if player_number == 1 else self.game.player2_cards
            card = action['card']
            index = action['index']
            player_cards[index] = card  # Place the drawn card in the player's hand
            self.broadcast_game_state()

        self.check_game_over()

    def check_game_over(self):
        # Check if all cards are discarded for any player
        player1_finished = all(card == "back" for card in self.game.player1_cards)
        player2_finished = all(card == "back" for card in self.game.player2_cards)

        if player1_finished or player2_finished:
            self.calculate_scores_and_notify()

    def calculate_scores_and_notify(self):
        # Calculate scores for both players
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

    def calculate_score(self, cards):
        """ Calculate the score based on remaining face-up cards """
        score = 0
        for card in cards:
            if card == "back":
                continue  # Ignore face-down cards
            rank = card[:-1]
            if rank.isdigit():
                score += int(rank)
            elif rank == 'A':
                score += 1
            else:  # J, Q, K
                score += 10
        return score

    def broadcast_game_state(self):
        # Make sure that all necessary keys are included in the game state
        game_state = {
            'current_player': self.game.current_player,  # Include the current player's turn
            'player1_cards': self.game.player1_cards,
            'player2_cards': self.game.player2_cards,
            'discard_pile': self.game.get_top_discard_card(),
            'game_over': False  # Default to game not over
        }
        
        # Send the complete game state to all clients, along with their player number
        for client, player_number in self.clients:
            personalized_state = game_state.copy()
            personalized_state['player_number'] = player_number
            client.send(pickle.dumps(personalized_state))

if __name__ == "__main__":
    SixCardGolfServer(max_players=2)  # Adjust max players as needed
