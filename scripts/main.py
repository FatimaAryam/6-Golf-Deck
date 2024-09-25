import tkinter as tk
from load_images import load_card_images
from game_logic import CardGameLogic

class CardGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Six Card Golf")
        self.master.configure(bg='lightblue')

        # Initialize game logic
        self.game_logic = CardGameLogic()
        self.card_images = load_card_images(r"D:\Dell\Data\Fiverr\6_Golf_Card\images")

        # Store references to card images to prevent garbage collection
        self.card_image_references = {}

        # Display Player 1's cards
        self.player1_label = tk.Label(master, text="Player 1", font=("Arial", 16), bg='lightblue')
        self.player1_label.grid(row=0, column=0, columnspan=6)
        self.create_card_labels(self.game_logic.player1_cards, 1)
        
        # Display Player 2's cards
        self.player2_label = tk.Label(master, text="Player 2", font=("Arial", 16), bg='lightblue')
        self.player2_label.grid(row=2, column=0, columnspan=6)
        self.create_card_labels(self.game_logic.player2_cards, 3)

        # Display scores
        self.show_scores()

    def create_card_labels(self, cards, row):
        for index, card in enumerate(cards):
            card_image = self.card_images[card]
            self.card_image_references[card] = card_image  # Store reference in dictionary
            card_label = tk.Label(self.master, image=card_image)
            card_label.grid(row=row, column=index)
            # Keep a reference to the label
            card_label.image = card_image

    def show_scores(self):
        player1_score, player2_score = self.game_logic.get_scores()
        score_label = tk.Label(self.master, text=f"Scores: Player 1 - {player1_score}, Player 2 - {player2_score}",
                                font=("Arial", 16), bg='lightblue')
        score_label.grid(row=4, column=0, columnspan=6)

if __name__ == "__main__":
    root = tk.Tk()
    game = CardGame(root)
    root.mainloop()
