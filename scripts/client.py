import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk
import pickle

def load_card_images(folder):
    card_images = {}
    size = (80, 112)
    suits = ['C', 'D', 'H', 'S']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    for suit in suits:
        for rank in ranks:
            card_name = rank + suit
            image_path = f"{folder}/{card_name}.png"
            try:
                card_image = Image.open(image_path).resize(size, Image.LANCZOS)
                card_images[card_name] = ImageTk.PhotoImage(card_image)
            except Exception as e:
                print(f"Error loading image {card_name}: {e}")
    
    back_image = Image.open(f"{folder}/red_back.png").resize(size, Image.LANCZOS)
    card_images['back'] = ImageTk.PhotoImage(back_image)
    
    return card_images

class CardGameClient:
    def __init__(self, host='127.0.0.1', port=7777):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

        self.root = tk.Tk()
        self.root.title("Six Card Golf - Client")

        # Load the card images (update the folder path to your images directory)
        self.card_images = load_card_images(r"D:\Dell\Data\Fiverr\6_Golf_Card\6-Golf-Deck\images")

        self.player_name = ""
        self.player_number = None
        self.game_state = None
        self.create_registration_interface()

        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.root.mainloop()

    def create_registration_interface(self):
        self.registration_frame = tk.Frame(self.root)
        self.registration_frame.pack()

        tk.Label(self.registration_frame, text="Enter your name:").pack()
        self.name_entry = tk.Entry(self.registration_frame)
        self.name_entry.pack()
        tk.Button(self.registration_frame, text="Register", command=self.register_player).pack()

    def register_player(self):
        self.player_name = self.name_entry.get()
        self.client_socket.send(pickle.dumps({"type": "register", "name": self.player_name}))
        self.registration_frame.destroy()

    def create_game_interface(self):
        self.player_frame = tk.Frame(self.root)
        self.player_frame.pack()
        self.info_label = tk.Label(self.root, text="Waiting for other players...")
        self.info_label.pack()

        self.draw_button = tk.Button(self.root, text="Draw Card", command=self.draw_card)
        self.draw_button.pack()
        self.discard_button = tk.Button(self.root, text="Discard Card", command=self.discard_card)
        self.discard_button.pack()

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(4096)
                if data:
                    message = pickle.loads(data)
                    print(f"Received message: {message}")  # Debug statement
                    
                    if message.get("type") == "register":
                        self.create_game_interface()
                    elif message.get("type") == "assign_id":
                        self.player_number = message['player_id']
                        print(f"Assigned player ID: {self.player_number}")
                    elif message.get("type") == "start":
                        self.info_label.config(text=message["message"])
                    elif message.get("type") == "game_state":
                        self.game_state = message
                        self.update_interface(message)
                    elif message.get("type") == "game_over":
                        self.info_label.config(text=message["message"])
                        self.draw_button.config(state=tk.DISABLED)
                        self.discard_button.config(state=tk.DISABLED)
            except ConnectionResetError:
                print("Server disconnected")
                break

    def update_interface(self, game_state):
        if not game_state:
            return

        self.info_label.config(text=f"Player {game_state['current_player']}'s turn")

        # Display player's cards and update other elements
        player_cards = game_state['player_cards'].get(self.player_number)
        if player_cards:
            self.display_player_cards(player_cards)

    def display_player_cards(self, player_cards):
        for widget in self.player_frame.winfo_children():
            widget.destroy()
        
        for card in player_cards:
            if card in self.card_images:
                card_image = self.card_images[card]
                label = tk.Label(self.player_frame, image=card_image)
                label.image = card_image
                label.pack(side=tk.LEFT)
            else:
                print(f"Card image not found for {card}")

    def draw_card(self):
        if self.game_state['current_player'] == self.player_number:
            action = {'type': 'draw_card'}
            self.client_socket.send(pickle.dumps(action))
            self.info_label.config(text="You drew a card, waiting for server update...")
        else:
            self.info_label.config(text="It's not your turn to draw a card!")

    def discard_card(self):
        if self.game_state['current_player'] == self.player_number:
            player_cards = self.game_state.get('player_cards', {}).get(self.player_number, [])
            
            if player_cards:
                card_index = 0  # For simplicity, discard the first card
                discarded_card = player_cards[card_index]
                action = {'type': 'discard_card', 'card': discarded_card}
                self.client_socket.send(pickle.dumps(action))

                self.info_label.config(text="Card discarded, waiting for server update...")
                self.update_interface(self.game_state)
        else:
            self.info_label.config(text="It's not your turn to discard a card!")

if __name__ == "__main__":
    CardGameClient()
