import tkinter as tk
from PIL import Image, ImageTk
from game_logic import SixCardGolfGame

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

class CardGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Six Card Golf")
        self.game_logic = SixCardGolfGame()
        self.card_images = load_card_images(r"D:\Dell\Data\Fiverr\6_Golf_Card\6-Golf-Deck\images")
        self.create_interface()
    
    def create_interface(self):
        self.player1_frame = tk.Frame(self.master)
        self.player1_frame.pack()
        self.player2_frame = tk.Frame(self.master)
        self.player2_frame.pack()
        
        self.create_card_labels(self.game_logic.player1_cards, 1, self.player1_frame)
        self.create_card_labels(self.game_logic.player2_cards, 2, self.player2_frame)
        
        self.action_frame = tk.Frame(self.master)
        self.action_frame.pack()
        
        self.draw_button = tk.Button(self.action_frame, text="Draw Card", command=self.draw_card)
        self.draw_button.pack(side=tk.LEFT)
        
        self.discard_button = tk.Button(self.action_frame, text="Discard Card", command=self.discard_card)
        self.discard_button.pack(side=tk.LEFT)
        
        self.end_turn_button = tk.Button(self.action_frame, text="End Turn", command=self.end_turn)
        self.end_turn_button.pack(side=tk.LEFT)
        
        self.update_discard_pile()

    def create_card_labels(self, cards, player_number, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        
        label_text = f"Player {player_number}'s Cards:"
        tk.Label(frame, text=label_text).pack()
        
        self.card_labels = []
        for card in cards:
            card_image = self.card_images[card]
            card_label = tk.Label(frame, image=card_image)
            card_label.image = card_image  # Keep reference
            card_label.pack(side=tk.LEFT)
            self.card_labels.append(card_label)
    
    def draw_card(self):
        card = self.game_logic.draw_card()
        if card:
            print(f"Player {self.game_logic.current_player} drew {card}")
            # Insert logic to replace one of the player's face-down cards with the drawn card
            self.update_gui()
        else:
            print("No more cards to draw!")

    def discard_card(self):
        current_player_cards = self.game_logic.player1_cards if self.game_logic.current_player == 1 else self.game_logic.player2_cards
        card_index = 0  # Replace the first card as an example
        discarded_card = self.game_logic.discard_card(current_player_cards, card_index)
        print(f"Player {self.game_logic.current_player} discarded {discarded_card}")
        self.update_gui()

    def end_turn(self):
        self.game_logic.end_turn()
        print(f"Player {self.game_logic.current_player}'s turn!")
        self.update_gui()

    def update_gui(self):
        self.create_card_labels(self.game_logic.player1_cards, 1, self.player1_frame)
        self.create_card_labels(self.game_logic.player2_cards, 2, self.player2_frame)
        self.update_discard_pile()
    
    def update_discard_pile(self):
        top_card = self.game_logic.get_top_discard_card()
        if top_card:
            top_card_image = self.card_images[top_card]
            self.discard_pile_label = tk.Label(self.master, image=top_card_image)
            self.discard_pile_label.image = top_card_image
            self.discard_pile_label.pack()

if __name__ == "__main__":
    root = tk.Tk()
    game = CardGame(root)
    root.mainloop()
