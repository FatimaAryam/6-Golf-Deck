import socket
import threading
import pickle
from game_logic import SixCardGolfGame

class GameServer:
    def __init__(self, host='0.0.0.0', port=7777):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Server started on {host}:{port}")

        self.clients = []
        self.players = {}
        self.game_started = False
        self.num_players = 0
        self.game_logic = None

        self.start_server()

    def start_server(self):
        while True:
            try:
                self.num_players = int(input("Enter the number of players (2, 3, or 4): "))
                if self.num_players in [2, 3, 4]:
                    break
                else:
                    print("Please select a valid option: 2, 3, or 4")
            except ValueError:
                print("Invalid input. Please enter a number.")

        self.game_logic = SixCardGolfGame(self.num_players)

        while len(self.players) < self.num_players:
            print("Waiting for players to connect...")
            client_socket, client_address = self.server_socket.accept()
            print(f"Player connected from {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            client_socket.send(pickle.dumps({"type": "register"}))
            player_info = pickle.loads(client_socket.recv(1024))
            player_name = player_info['name']
            player_id = len(self.players) + 1

            self.players[player_id] = player_name
            self.clients.append((client_socket, player_id))
            print(f"Player {player_id}: {player_name} registered.")

            client_socket.send(pickle.dumps({"type": "assign_id", "player_id": player_id}))

            if len(self.players) == self.num_players:
                self.game_started = True
                self.start_game()

            while True:
                data = client_socket.recv(4096)
                if data:
                    action = pickle.loads(data)
                    if action['type'] == 'draw_card':
                        self.handle_draw_card(player_id)
                    elif action['type'] == 'discard_card':
                        self.handle_discard_card(player_id, action['card'])
                    elif action['type'] == 'de-register':
                        self.handle_de_register(player_id, client_socket)
                        break
        except Exception as e:
            print(f"Error handling client: {e}")
            self.handle_de_register(player_id, client_socket)

    def handle_de_register(self, player_id, client_socket):
        """Handle a player leaving the game."""
        player_name = self.players.pop(player_id, None)
        self.clients = [(client, pid) for client, pid in self.clients if pid != player_id]
        
        if player_name:
            print(f"Player {player_id} ({player_name}) has left the game.")
            # Notify other players
            self.broadcast({"type": "player_left", "message": f"Player {player_name} has left the game."})
        
        # Close the client socket
        client_socket.close()

        # Check if the remaining players are still active
        if len(self.players) < 2:
            print("Not enough players to continue the game. The game will end.")
            self.broadcast({"type": "final_result", "message": "Game Over! Not enough players remaining."})
            self.server_socket.close()
            exit()

    def start_game(self):
        print("Starting the game...")
        self.broadcast({"type": "start", "message": "Game is starting!"})
        self.broadcast_game_state()

    def handle_draw_card(self, player_id):
        card = self.game_logic.draw_card()
        if card:
            print(f"Player {player_id} drew a card: {card}")
            self.game_logic.players_cards[player_id].append(card)
            self.broadcast_game_state()

    def handle_discard_card(self, player_id, card):
        if card in self.game_logic.players_cards[player_id]:
            print(f"Player {player_id} discarded card: {card}")
            self.game_logic.discard_card(player_id, card)
            
            if len(self.game_logic.players_cards[player_id]) == 0:
                print(f"Player {player_id} has no more cards left.")
                self.broadcast({"type": "game_over", "message": f"Player {player_id} has finished all cards!"})
                
                # Check if all players have finished their cards
                if all(len(cards) == 0 for cards in self.game_logic.players_cards.values()):
                    scores = self.calculate_scores()
                    winner_id = min(scores, key=scores.get)
                    result_message = f"Game Over! Scores: {scores}. Player {winner_id} wins!"
                    self.broadcast({"type": "final_result", "message": result_message})
                    self.server_socket.close()
                    exit()
            else:
                self.game_logic.end_turn()
                self.broadcast_game_state()

    def calculate_scores(self):
        """Calculate the scores for each player based on their remaining cards."""
        score_dict = {}
        for player_id, cards in self.game_logic.players_cards.items():
            score = 0
            for card in cards:
                rank = card[:-1]  # Extract the rank from card, e.g., '2' from '2H'
                if rank in ['J', 'Q', 'K']:  # Jack, Queen, King each score 10 points
                    score += 10
                elif rank == 'A':  # Ace scores 1 point
                    score += 1
                else:
                    score += int(rank)  # All other cards score their numeric value
            score_dict[player_id] = score
        return score_dict

    def broadcast_game_state(self):
        game_state = {
            "type": "game_state",
            "current_player": self.game_logic.current_player,
            "players": self.players,
            "discard_pile": self.game_logic.get_top_discard_card(),
            "player_cards": self.game_logic.players_cards
        }
        print(f"Broadcasting game state: {game_state}")
        self.broadcast(game_state)

    def broadcast(self, message):
        for client, player_id in self.clients:
            try:
                client.send(pickle.dumps(message))
            except Exception as e:
                print(f"Error broadcasting message to player {player_id}: {e}")
                self.handle_de_register(player_id, client)

if __name__ == "__main__":
    GameServer()
