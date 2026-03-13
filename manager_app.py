# gui_price_monitor.py
import tkinter as tk
from backend.api_manager import APIManager

# Configuração de pips
PIP_SIZE = 0.0001  # 1 pip para EUR/USD

class PriceMonitor:
    def __init__(self, root, api_manager, pip_range=10):
        self.api = api_manager
        self.pip_range = pip_range
        self.root = root
        self.root.title(f"Preço Atual {self.api.symbol}")

        self.label_price = tk.Label(root, text="", font=("Arial", 24))
        self.label_price.pack(padx=20, pady=20)

        self.label_range = tk.Label(root, text="", font=("Arial", 16))
        self.label_range.pack(padx=20, pady=10)

        # Atualiza a interface a cada 1 segundo
        self.update_price()

    def update_price(self):
        tick = self.api.get_price()
        price = tick["close"]

        # Calcula faixa +- pips
        low = price - (self.pip_range * PIP_SIZE)
        high = price + (self.pip_range * PIP_SIZE)

        self.label_price.config(text=f"Preço: {price:.5f}")
        self.label_range.config(text=f"Faixa: {low:.5f} - {high:.5f} (+-{self.pip_range} pips)")

        # Atualiza a cada 1 segundo
        self.root.after(1000, self.update_price)


if __name__ == "__main__":
    api = APIManager("EURUSD")
    root = tk.Tk()
    monitor = PriceMonitor(root, api_manager=api, pip_range=10)  # +-10 pips
    root.mainloop()
