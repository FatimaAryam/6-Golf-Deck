import socket
import threading
import pickle
import sys  # Import sys to read command-line arguments

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
        
        # Get player's name
        self.player_name = input("Enter your name: ")
        self.client_socket.send(pickle.dumps({"type": "register", "name": self.player_name}))
        
        # Start a thread to listen for server messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # Start the game loop for console input
        self.run_console_game()

    def run_console_game(self):
        """Main loop for handling player commands."""
        while True:
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

    def receive_messages(self):
        """Handle incoming messages from the server."""
        while True:
            try:
                data = self.client_socket.recv(4096)
                if data:
                    message = pickle.loads(data)
                    
                    if message.get("type") == "game_state":
                        self.display_game_state(message)
                    elif message.get("type") == "game_over":
                        print(message["message"])
                    elif message.get("type") == "final_result":
                        print(message["message"])
                    elif message.get("type") == "player_left":
                        print(message["message"])
            except (ConnectionResetError, OSError):
                print("Disconnected from the server.")
                break

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

if __name__ == "__main__":
    # Check if correct number of arguments is provided
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("Invalid port number. Port must be an integer.")
        sys.exit(1)

    # Start the client
    CardGameClient(server_ip, server_port)
