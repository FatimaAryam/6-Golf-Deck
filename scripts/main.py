import tkinter as tk
from PIL import Image, ImageTk
from game_logic import SixCardGolfGame  # Correct import from game_logic.py

# Function to load card images
def load_card_images(folder):
    card_images = {}
    size = (80, 112)  # Set smaller size to fit more cards
    suits = ['C', 'D', 'H', 'S']  # Clubs, Diamonds, Hearts, Spades
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    for suit in suits:
        for rank in ranks:
            card_name = rank + suit
            image_path = f"{folder}/{card_name}.png"
            card_image = Image.open(image_path)
            card_image = card_image.resize(size, Image.LANCZOS)
            card_images[card_name] = ImageTk.PhotoImage(card_image)
    
    # Load back of card image
    back_image = Image.open(f"{folder}/red_back.png")
    back_image = back_image.resize(size, Image.LANCZOS)
    card_images['back'] = ImageTk.PhotoImage(back_image)
    
    return card_images

# CardGame class for the GUI
class CardGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Six Card Golf")
        
        # Initialize game logic
        self.game_logic = SixCardGolfGame()
        
        # Load card images
        self.card_images = load_card_images(r"D:\Dell\Data\Fiverr\6_Golf_Card\6-Golf-Deck\images")
        
        # Create the GUI layout
        self.create_card_labels(self.game_logic.player1_cards, 1)
        self.create_card_labels(self.game_logic.player2_cards, 2)
        
        # Buttons for game actions
        draw_button = tk.Button(self.master, text="Draw Card", command=self.draw_card)
        draw_button.pack()
        
        discard_button = tk.Button(self.master, text="Discard Card", command=self.discard_card)
        discard_button.pack()
        
        end_turn_button = tk.Button(self.master, text="End Turn", command=self.end_turn)
        end_turn_button.pack()

    # Create card labels to show on the GUI for players
    def create_card_labels(self, cards, player_number):
        frame = tk.Frame(self.master)
        frame.pack()
        label_text = f"Player {player_number}'s Cards:"
        tk.Label(frame, text=label_text).pack(side=tk.TOP)
        
        for card in cards:
            card_image = self.card_images[card]
            card_label = tk.Label(frame, image=card_image)
            card_label.image = card_image  # Keep a reference
            card_label.pack(side=tk.LEFT)

    # Handle the draw card action
    def draw_card(self):
        card = self.game_logic.draw_card()
        if card:
            print(f"Player {self.game_logic.current_player} drew {card}")
            self.update_gui()
        else:
            print("No more cards to draw!")

    # Handle the discard card action (For demo, discarding first card in hand)
    def discard_card(self):
        if self.game_logic.current_player == 1:
            card_to_discard = self.game_logic.player1_cards[0]
            self.game_logic.discard_card(self.game_logic.player1_cards, card_to_discard)
        else:
            card_to_discard = self.game_logic.player2_cards[0]
            self.game_logic.discard_card(self.game_logic.player2_cards, card_to_discard)
        
        print(f"Player {self.game_logic.current_player} discarded {card_to_discard}")
        self.update_gui()

    # Handle end turn action
    def end_turn(self):
        self.game_logic.end_turn()
        print(f"Player {self.game_logic.current_player}'s turn!")
        self.update_gui()

    # Update GUI after each action
    def update_gui(self):
        # Clear and recreate card labels based on the updated hand
        for widget in self.master.winfo_children():
            widget.destroy()
        
        self.create_card_labels(self.game_logic.player1_cards, 1)
        self.create_card_labels(self.game_logic.player2_cards, 2)
        
        # Recreate buttons after refreshing the GUI
        draw_button = tk.Button(self.master, text="Draw Card", command=self.draw_card)
        draw_button.pack()
        
        discard_button = tk.Button(self.master, text="Discard Card", command=self.discard_card)
        discard_button.pack()
        
        end_turn_button = tk.Button(self.master, text="End Turn", command=self.end_turn)
        end_turn_button.pack()

# Main function to start the game
if __name__ == "__main__":
    root = tk.Tk()
    game = CardGame(root)
    root.mainloop()
