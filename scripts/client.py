import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk
import pickle  # For sending/receiving objects
import os

# Function to load card images
def load_card_images(folder):
    card_images = {}
    size = (80, 112)
    suits = ['C', 'D', 'H', 'S']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    for suit in suits:
        for rank in ranks:
            card_name = rank + suit
            image_path = f"{folder}/{card_name}.png"
            card_image = Image.open(image_path).resize(size, Image.LANCZOS)
            card_images[card_name] = ImageTk.PhotoImage(card_image)
    
    back_image = Image.open(f"{folder}/red_back.png").resize(size, Image.LANCZOS)
    card_images['back'] = ImageTk.PhotoImage(back_image)
    
    return card_images

class CardGameClient:
    def __init__(self, host='localhost', port=5555):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        
        self.root = tk.Tk()
        self.root.title("Six Card Golf - Client")
        
        self.card_images = load_card_images(r"D:\Dell\Data\Fiverr\6_Golf_Card\6-Golf-Deck\images")
        
        self.card_labels = []
        self.player_number = None
        self.temp_drawn_card = None
        self.create_interface()
        
        # Start a thread to listen for server messages
        threading.Thread(target=self.receive_game_state, daemon=True).start()
        self.root.mainloop()

    def create_interface(self):
        self.player_frame = tk.Frame(self.root)
        self.player_frame.pack()

        self.draw_button = tk.Button(self.root, text="Draw Card", command=self.draw_card)
        self.draw_button.pack()

        self.discard_button = tk.Button(self.root, text="Discard Card", command=self.discard_card)
        self.discard_button.pack()

        self.info_label = tk.Label(self.root, text="Waiting for other players...")
        self.info_label.pack()

    def update_interface(self, game_state):
        if game_state.get('game_over', False):
            self.info_label.config(text=f"Game Over! {game_state['winner']}\nPlayer 1 score: {game_state['player1_score']}, Player 2 score: {game_state['player2_score']}")
            self.draw_button.config(state=tk.DISABLED)
            self.discard_button.config(state=tk.DISABLED)
            return

        if 'current_player' in game_state:
            if self.player_number == game_state['current_player']:
                self.info_label.config(text=f"Your turn (Player {self.player_number})")
            else:
                self.info_label.config(text=f"Waiting for Player {game_state['current_player']}'s turn")
        else:
            self.info_label.config(text="Waiting for the next update from the server...")

        for label in self.card_labels:
            label.destroy()
        self.card_labels = []

        player_cards = game_state.get('player1_cards', []) if self.player_number == 1 else game_state.get('player2_cards', [])
        
        for idx, card in enumerate(player_cards):
            card_image = self.card_images[card] if card != "back" else self.card_images['back']
            label = tk.Label(self.player_frame, image=card_image)
            label.image = card_image
            
            if self.player_number == game_state['current_player'] and self.temp_drawn_card and card == "back":
                label.bind("<Button-1>", lambda event, index=idx: self.place_drawn_card(index))
            
            label.pack(side=tk.LEFT)
            self.card_labels.append(label)

    def draw_card(self):
        action = {'type': 'draw_card'}
        self.client_socket.send(pickle.dumps(action))
        self.info_label.config(text="Card drawn, waiting for server update...")

    def discard_card(self):
        action = {'type': 'discard_card', 'card_index': 0}
        self.client_socket.send(pickle.dumps(action))
        self.info_label.config(text="Card discarded, waiting for server update...")

    def place_drawn_card(self, index):
        action = {'type': 'place_card', 'card': self.temp_drawn_card, 'index': index}
        self.client_socket.send(pickle.dumps(action))
        self.temp_drawn_card = None
        self.info_label.config(text="Placed card, waiting for server update...")
        
    def receive_game_state(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if data:
                    game_state = pickle.loads(data)
                    
                    if game_state.get('type') == 'card_drawn':
                        self.temp_drawn_card = game_state['card']
                        self.info_label.config(text=f"You drew: {self.temp_drawn_card}. Click an empty slot to place it.")
                        continue
                    
                    if 'player_number' in game_state:
                        self.player_number = game_state['player_number']
                    
                    self.update_interface(game_state)
            except ConnectionResetError:
                print("Server disconnected")
                break

if __name__ == "__main__":
    CardGameClient()
