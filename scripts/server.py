
import socket
import threading
import pickle
from game_logic import SixCardGolfGame

class GameServer:
    def __init__(self, host='192.168.1.160', port=7777):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Server started on {host}:{port}")

        self.clients = []
        self.players = {}
        self.game_started = False
        self.num_players = 0
        self.game_logic = None

        # Start accepting client connections
        self.start_server()

    def start_server(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")

            # Start a new thread to handle the client
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        '''
        Method to handle communication with a connected client.
        '''
        while True:
            try:
                # Receive and process client message
                message = pickle.loads(client_socket.recv(1024))
                command_type = message.get("type")

                if command_type == "register":
                    player_name = message.get("name")
                    self.players[player_name] = client_socket
                    print(f"Player {player_name} registered.")
                    client_socket.send(pickle.dumps({"status": "registered", "name": player_name}))

                
                elif command_type == "deregister":
                    # Check if the player is involved in any ongoing game
                    if self.game_logic.is_player_in_game(player_name):
                        # Player is in an ongoing game, deregistration fails
                        client_socket.send(pickle.dumps({"status": "failure", "reason": "Player is in an ongoing game."}))
                    else:
                        # Remove player from the player list
                        if player_name in self.players:
                            del self.players[player_name]
                            print(f"Player {player_name} deregistered.")
                            client_socket.send(pickle.dumps({"status": "success", "message": "Player deregistered successfully."}))
                        else:
                            client_socket.send(pickle.dumps({"status": "failure", "reason": "Player not found."}))

                elif command_type == "query_players":
                    num_players, player_list = self.query_players()
                    response = {"num_players": num_players, "players": player_list}
                    client_socket.send(pickle.dumps(response))

                elif command_type == "query_games":
                    num_games, game_list = self.query_games()
                    response = {"num_games": num_games, "games": game_list}
                    client_socket.send(pickle.dumps(response))

                else:
                    client_socket.send(pickle.dumps({"error": "Unknown command"}))

            except Exception as e:
                print(f"Error handling client message: {e}")
                client_socket.close()
                break

    def query_players(self):
        '''
        Queries the players currently registered with the tracker.
        '''
        if not self.players:
            return 0, []
        
        player_list = [(player_name, "connected") for player_name in self.players.keys()]
        return len(self.players), player_list

    def query_games(self):
        '''
        Queries the games of Six Card Golf currently ongoing.
        '''
        if not self.game_logic or not self.game_logic.games:
            return 0, []

        game_list = []
        for game_id, game in self.game_logic.games.items():
            dealer_name = game.dealer
            player_names = [player.name for player in game.players if player != dealer_name]
            game_info = (game_id, dealer_name, player_names)
            game_list.append(game_info)

        return len(self.game_logic.games), game_list

if __name__ == "__main__":
    GameServer()
