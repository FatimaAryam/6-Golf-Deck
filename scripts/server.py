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
        self.clients = []

        self.game_started = False
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
        while True:
            try:
                message = pickle.loads(client_socket.recv(1024))
                command_type = message.get("type")

                if command_type == "register":
                    player_name = message.get("name")
                    ipv4 = message.get("ipv4")
                    t_port = message.get("t_port")
                    p_port = message.get("p_port")
                    response = self.register_player(player_name, client_socket, ipv4, t_port, p_port)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "draw_card":
                    player = message.get("player")
                    response = self.handle_draw_card(player)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "swap_card":
                    your_card = message.get("your_card")
                    drawn_card = message.get("drawn_card")
                    player = message.get("player")
                    response = self.handle_swap_card(player, your_card, drawn_card)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "discard_card":
                    card = message.get("card")
                    player = message.get("player")
                    response = self.handle_discard_card(player, card)
                    client_socket.send(pickle.dumps(response))
                elif command_type == "query_players":
                    response = self.query_players()
                    client_socket.send(pickle.dumps(response))
                elif command_type == "start_game":
                    print("Starting game...")
                    player = message.get("player")
                    n = message.get("n")
                    holes = message.get("holes", 9)
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
                    response = self.start_game(player,n,holes)
                    client_socket.send(pickle.dumps(response))
                    while len(self.players) < self.num_players:
                        print("Waiting for players to connect...")
                        client_socket, client_address = self.server_socket.accept()
                        print(f"Player connected from {client_address}")
                        threading.Thread(target=self.handle_client, args=(client_socket,)).start()
                    while True:
                        data = client_socket.recv(4096)
                        if data:
                            action = pickle.loads(data)
                        if action['type'] == 'draw_card':
                            self.handle_draw_card(player)
                        elif action['type'] == 'discard_card':
                            self.handle_discard_card(player, action['card'])
                        elif action['type'] == 'de-register':
                            self.handle_de_register(player, client_socket)
                        break
                
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

    def register_player(self, player_name, client_socket, ipv4, t_port, p_port):
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
        self.clients.append((client_socket, player_name))
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
        print(f"Player ({player_name}) has left the game.")
        self.broadcast({"type": "player_left", "message": f"Player {player_name} has left the game."})
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
        print(f"Starting game with player: {player}, n: {n}, holes: {holes}")
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
        selected_players.append(player)  # Add the dealer to the list of players

        print(f"Selected players: {selected_players}")
        
        game_id = self.generate_game_id()
        
        # Update player status
        for p in selected_players:
            self.players[p]["status"] = "in-play"

        self.games[game_id] = {
            "dealer": player,
            "players": selected_players,
            "holes": holes,
            "status": "in-play"
        }
        
        self.game_logic = SixCardGolfGame(len(selected_players))
        self.game_logic.players = selected_players
        
        player_info = [
            {"name": p, "ipv4": self.players[p]["ipv4"], "p_port": self.players[p]["p_port"]}
            for p in selected_players
        ]
        print("Starting the game...")
        self.broadcast({"type": "start", "message": "Game is starting!"})
        self.broadcast_game_state()
        
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
    
    def handle_draw_card(self, player):
        card = self.game_logic.draw_card()
        if card:
            print(f"Player {player} drew a card: {card}")
            self.game_logic.players_cards[player].append(card)
            self.broadcast_game_state()

    def handle_discard_card(self, player, card):
        if self.game_logic.current_player != player:
            return {"status": "FAILURE", "reason": "It's not your turn."}
        
        if card in self.game_logic.players_cards[player]:
            print(f"Player {player} discarded card: {card}")
            self.game_logic.discard_card(player, card)
            
            if len(self.game_logic.players_cards[player]) == 0:
                print(f"Player {player} has no more cards left.")
                self.broadcast({"type": "game_over", "message": f"Player {player} has finished all cards!"})
                
                # Check if all players have finished their cards
                if all(len(cards) == 0 for cards in self.game_logic.players_cards.values()):
                    scores = self.calculate_scores()
                    winner_id = min(scores, key=scores.get)
                    result_message = f"Game Over! Scores: {scores}. Player {winner_id} wins!"
                    self.broadcast({"type": "final_result", "message": result_message})
                    self.end_game(self.generate_game_id(), self.games[self.generate_game_id()]["dealer"])
            else:
                self.game_logic.end_turn()
                self.broadcast_game_state()
            
            return {"status": "SUCCESS"}
        else:
            return {"status": "FAILURE", "reason": "Card not in player's hand."}

    def handle_swap_card(self, player, your_card, drawn_card):
        if self.game_logic.current_player != player:
            return {"status": "FAILURE", "reason": "It's not your turn."}
        
        if your_card in self.game_logic.players_cards[player] and drawn_card in self.game_logic.players_cards[player]:
            self.game_logic.swap_card(player, your_card, drawn_card)
            print(f"Player {player} swapped {your_card} with {drawn_card}")
            self.game_logic.end_turn()
            self.broadcast_game_state()
            return {"status": "SUCCESS"}
        else:
            return {"status": "FAILURE", "reason": "Invalid card swap."}

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
            print(f"Broadcasting message to player {player_id}")
            try:
                client.send(pickle.dumps(message))
            except Exception as e:
                print(f"Error broadcasting message to player {player_id}: {e}")
                self.deregister_player(player_id)

# Main execution
if __name__ == "__main__":
    GameServer()