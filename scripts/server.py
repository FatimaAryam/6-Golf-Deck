import socket
import threading
import pickle
from game_logic import SixCardGolfGame

class GameServer:
    def __init__(self, host='192.168.1.165', port=7500):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Server started on {host}:{port}")

        self.clients = {}
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

                # Other command handling...

            except Exception as e:
                print(f"Error handling client message: {e}")
                client_socket.close()
                break

    def register_player(self, player_name, ipv4, t_port, p_port):
        if len(player_name) > 15 or not player_name.isalpha():
            return {"status": "FAILURE", "reason": "Invalid player name."}
        if not (7501 <= t_port < 7999 and 7501 <= p_port < 7999):
            return {"status": "FAILURE", "reason": "Ports must be in the range [7500, 7999]."}
        if player_name in self.players:
            return {"status": "FAILURE", "reason": "Player already registered."}

        self.players[player_name] = (ipv4, t_port, p_port)
        print(f"Player {player_name} registered with IP {ipv4}, T-port {t_port}, P-port {p_port}.")
        return {"status": "SUCCESS"}

# Main execution
if __name__ == "__main__":
    GameServer()