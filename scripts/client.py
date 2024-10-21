import socket
import threading
import pickle
import sys
from game_logic import SixCardGolfGame

class CardGameClient:
    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the specified host and port
        try:
            self.client_socket.connect((host, port))
            print(f"Connected to game server at {host}:{port}")
        except ConnectionRefusedError:
            print(f"Could not connect to server at {host}:{port}. Make sure the server is running and try again.")
            sys.exit(1)

        # Get player's details
        while True:
            self.player_name = input("Enter your name (max 15 chars, alphabetic only): ")
            self.ipv4 = input("Enter your IPv4 address: ")
            self.t_port = int(input("Enter your tracker port (7500-7999): "))
            self.p_port = int(input("Enter your player port (7500-7999): "))

            self.client_socket.send(pickle.dumps({
                "type": "register",
                "name": self.player_name,
                "ipv4": self.ipv4,
                "t_port": self.t_port,
                "p_port": self.p_port
            }))

            response = pickle.loads(self.client_socket.recv(1024))
            if response["status"] == "SUCCESS":
                print("Registration successful!")
                break
            else:
                print(f"Registration failed: {response['reason']}")
                continue

        # Start a thread to listen for server messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # Start the command input loop
        self.run_console_input()

    def run_console_input(self):
        while True:
            command = input("Enter a command (query_players, query_games, deregister <player name>, start_game <player> <n> <holes>, end_game <game-identifer> <dealer>): ").strip()

            if command in ["query_players", "query_games"]:
                self.client_socket.send(pickle.dumps({"type": command}))
            elif command.startswith("deregister"):
                parts = command.split()
                if len(parts) != 2:
                    print("Invalid command format. Use: deregister <player name>")
                    continue

                player_name = parts[1]
                self.client_socket.send(pickle.dumps({"type": "deregister", "name": player_name}))
            elif command.startswith("start_game"):
                parts = command.split()
                if len(parts) != 4:
                    print("Invalid command format. Use: start_game <player> <n> <holes>")
                    continue

                player = parts[1]
                try:
                    n = int(parts[2])
                    holes = int(parts[3])
                    if not (1 <= n <= 3) or not (1 <= holes <= 9):
                        print("Invalid values for n or holes. Ensure 1 ≤ n ≤ 3 and 1 ≤ holes ≤ 9.")
                        continue
                except ValueError:
                    print("Both n and holes must be integers.")
                    continue

                self.client_socket.send(pickle.dumps({
                    "type": "start_game",
                    "player": player,
                    "n": n,
                    "holes": holes
                }))
                
                while True:
                    print(" enter : draw', 'discard <card>', swap <card> <desired card> ,or 'de-register' to leave the game.")
                    command = input("> ").strip().lower()
                    if command == 'draw':
                        self.client_socket.send(pickle.dumps({"type": "draw_card"}))
                    elif command.startswith('discard'):
                        try:
                            card = command.split(" ")[1].upper()
                            self.client_socket.send(pickle.dumps({"type": "discard_card", "card": card}))
                        except IndexError:
                            print("Please specify a card to discard (e.g., discard 5H)")
                    elif command == 'de-register':
                        self.client_socket.send(pickle.dumps({"type": "de-register"}))
                        print("You have left the game. Disconnecting...")
                        self.client_socket.close()
                        break
                    else:
                        print("Invalid command. Use 'draw', 'discard <card>', or 'de-register' to leave the game.")  

            elif command.startswith("end"):
                parts = command.split()
                if len(parts) != 3:
                    print("Invalid command format. Use: end <game-id> <player>")
                    continue

                game_id = parts[1]
                player = parts[2]

                self.client_socket.send(pickle.dumps({
                    "type": "end",
                    "game_id": game_id,
                    "player": player
                }))

            else:
                print("Invalid command. Try again.")
    
    def display_game_state(self, game_state):
        """Display the current game state in the console."""
        current_player = game_state["current_player"]
        print(f"\n--- Current Game State ---")
        print(f"Current Player's Turn: Player {current_player}")
        
        # Display each player's cards
        for player_id, cards in game_state["player_cards"].items():
            card_display = ', '.join(cards) if cards else "No cards left"
            print(f"Player {player_id} ({game_state['players'][player_id]}): {card_display}")
        
        # Show the top card of the discard pile
        top_discard = game_state.get("discard_pile", "Empty")
        print(f"Top card on discard pile: {top_discard}")
        print("------------------------")

    

    def receive_messages(self):
        while True:
            try:
                response = pickle.loads(self.client_socket.recv(1024))
                print(f"Server response: {response}")
                if "type" in response:
                    if response["type"] == "game_state":
                        self.display_game_state(response)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
    else:
        CardGameClient(sys.argv[1], int(sys.argv[2]))