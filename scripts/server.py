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
        # Ask the server host to specify the number of players
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

        # Accept connections until the number of players is reached
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
            self.clients.append(client_socket)
            print(f"Player {player_id}: {player_name} registered.")

            # Inform the client of their player number
            client_socket.send(pickle.dumps({"type": "assign_id", "player_id": player_id}))

            # If all players are registered, start the game
            if len(self.players) == self.num_players:
                self.game_started = True
                self.start_game()

            # Handle player actions
            while True:
                data = client_socket.recv(4096)
                if data:
                    action = pickle.loads(data)
                    if action['type'] == 'draw_card':
                        self.handle_draw_card(player_id)
                    elif action['type'] == 'discard_card':
                        self.handle_discard_card(player_id, action['card'])
        except Exception as e:
            print(f"Error handling client: {e}")
            client_socket.close()

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
            
            # Check if the player has no more cards left
            if len(self.game_logic.players_cards[player_id]) == 0:
                print(f"Player {player_id} has no more cards left.")
                self.broadcast({"type": "game_over", "message": f"Player {player_id} has finished all cards!"})
            else:
                self.game_logic.end_turn()
                self.broadcast_game_state()

    def broadcast_game_state(self):
        game_state = {
            "type": "game_state",
            "current_player": self.game_logic.current_player,
            "players": self.players,
            "discard_pile": self.game_logic.get_top_discard_card(),
            "player_cards": self.game_logic.players_cards
        }
        print(f"Broadcasting game state: {game_state}")  # Debug statement
        self.broadcast(game_state)

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(pickle.dumps(message))
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                self.clients.remove(client)

if __name__ == "__main__":
    GameServer()
