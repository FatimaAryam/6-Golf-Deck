import socket
import threading
import pickle
import sys

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
            command = input("Enter a command (query_players, query_games, deregister, start_game <player> <n> <holes>): ").strip()

            if command in ["query_players", "query_games"]:
                self.client_socket.send(pickle.dumps({"type": command}))
            elif command == "deregister":
                self.client_socket.send(pickle.dumps({"type": "deregister", "name": self.player_name}))
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
            else:
                print("Invalid command. Try again.")

    def receive_messages(self):
        while True:
            try:
                response = pickle.loads(self.client_socket.recv(1024))
                print(f"Server response: {response}")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
    else:
        CardGameClient(sys.argv[1], int(sys.argv[2]))