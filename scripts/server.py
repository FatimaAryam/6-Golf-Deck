import socket
import threading
import pickle
import random
from game_logic import SixCardGolfGame

class GameServer:
    def __init__(self, host='192.168.1.160', port=7500):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.games = {}
        self.server_socket.listen(5)
        print(f"Server started on {host}:{port}")

        self.players = {}
        
        # Start accepting client connections
        self.start_server()

    def start_server(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")

            # Start a new thread to handle the client
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = pickle.loads(client_socket.recv(1024))
                command_type = message.get("type")

                if command_type == "register":
                    player_name = message.get("name")
                    ipv4 = message.get("ipv4")
                    t_port = message.get("t_port")
                    p_port = message.get("p_port")

                    response = self.register_player(player_name, ipv4, t_port, p_port)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "query_players":
                    response = self.query_players()
                    client_socket.send(pickle.dumps(response))
                elif command_type == "start_game":
                    player = message.get("player")
                    n = message.get("n")
                    holes = message.get("holes", 9)
                
                    response = self.start_game(player, n, holes)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "query_games":
                    response = self.query_games()
                    client_socket.send(pickle.dumps(response))
                elif command_type == "end":
                    game_id = message.get("game_id")
                    player = message.get("player")
                    response = self.end_game(game_id, player)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "deregister":
                    player_name = message.get("name")
                    response = self.deregister_player(player_name)
                    client_socket.send(pickle.dumps(response))

            except Exception as e:
                print(f"Error handling client message: {e}")
                client_socket.close()
                break

    def register_player(self, player_name, ipv4, t_port, p_port):
        if len(player_name) > 15 or not player_name.isalpha():
            return {"status": "FAILURE", "reason": "Invalid player name."}
        if not (7501 <= t_port <= 7999 and 7501 <= p_port <= 7999):
            return {"status": "FAILURE", "reason": "Ports must be in the range [7501, 7999]."}
        if player_name in self.players:
            return {"status": "FAILURE", "reason": "Player already registered."}

        self.players[player_name] = {
            "ipv4": ipv4,
            "t_port": t_port,
            "p_port": p_port,
            "status": "free"
        }
        print(f"Player {player_name} registered with IP {ipv4}, T-port {t_port}, P-port {p_port}.")
        return {"status": "SUCCESS"}

    def deregister_player(self, player_name):
        if player_name not in self.players:
            return {"status": "FAILURE", "reason": "Player not registered."}

        # Check if the player is the dealer of any ongoing game
        for game_id, game_info in self.games.items():
            if player_name == game_info["dealer"]:
                return {"status": "FAILURE", "reason": "Player is the dealer of an ongoing game."}
            elif player_name in game_info["players"]:
                return {"status": "FAILURE", "reason": "Player is involved in an ongoing game."}

        # Remove the player
        del self.players[player_name]
        print(f"Player {player_name} deregistered.")
        return {"status": "SUCCESS"}

    def query_players(self):
        player_info = list(self.players.items())
        return {"status": len(player_info), "players": player_info}

    def query_games(self):
        if not self.games:
            return {"status": 0, "games": []}
        
        ongoing_games = []
        for game_id, game_info in self.games.items():
            game_details = {
                "game_id": game_id,
                "dealer": game_info["dealer"],
                "players": game_info["players"]
            }
            ongoing_games.append(game_details)
        
        return {"status": len(ongoing_games), "games": ongoing_games}

    def start_game(self, player, n, holes):
        if player not in self.players:
            return {"status": "FAILURE", "reason": "Player is not registered."}
        
        if not 1 <= n <= 3:
            return {"status": "FAILURE", "reason": "Invalid number of additional players."}
        
        if not 1 <= holes <= 9:
            return {"status": "FAILURE", "reason": "Invalid number of holes."}
        
        free_players = [p for p in self.players if p != player and self.players[p].get("status") == "free"]
        if len(free_players) < n:
            return {"status": "FAILURE", "reason": "Not enough free players available."}
        
        selected_players = random.sample(free_players, n)
        selected_players.append(player)  # Add the dealer to the list
        
        game_id = self.generate_game_id()
        self.games[game_id] = {
            "dealer": player,
            "players": selected_players,
            "holes": holes,
            "status": "in-play"
        }
        
        # Update player status
        for p in selected_players:
            self.players[p]["status"] = "in-play"
        
        player_info = [
            {"name": p, "ipv4": self.players[p]["ipv4"], "p_port": self.players[p]["p_port"]}
            for p in selected_players
        ]
        
        return {
            "status": "SUCCESS",
            "game_id": game_id,
            "players": player_info
        }

    def end_game(self, game_id, player):
        if game_id not in self.games:
            print(f"FAILURE: Game identifier '{game_id}' not found.")
            return {"status": "FAILURE", "reason": "Game identifier not found."}
        
        game_info = self.games[game_id]
        if game_info["dealer"] != player:
            print(f"FAILURE: Player '{player}' is not the dealer for game '{game_id}'.")
            return {"status": "FAILURE", "reason": "Player is not the dealer."}
        
        # Remove the game and update player statuses
        for p in game_info["players"]:
            self.players[p]["status"] = "free"
        del self.games[game_id]
        
        print(f"SUCCESS: Game '{game_id}' ended by dealer '{player}'.")
        return {"status": "SUCCESS"}

    def generate_game_id(self):
        return f"game_{len(self.games) + 1}"

# Main execution
if __name__ == "__main__":
    GameServer()