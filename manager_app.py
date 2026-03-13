# backend/api_manager.py
import numpy as np
import yfinance as yf
import requests
from collections import deque
from datetime import datetime

ALPHA = 0.2
OFFSET = -0.00190
VOLATILITY = 0.0005

class APIManager:
    """
    Fonte agregada confiável para pares Forex.
    Combina múltiplas APIs públicas, aplica mediana e suavização.
    Pode ser usado como fornecedor de dados para outros códigos.
    """
    def __init__(self, symbol="EURUSD"):
        self.symbol = symbol
        self.stream = deque([1.15]*500, maxlen=500)
        self.current_tick = 1.15

    def fetch_sources(self):
        """Coleta dados de múltiplas APIs públicas."""
        prices = []
        try:
            # Yahoo Finance
            prices.append(float(yf.Ticker(f"{self.symbol}=X").fast_info['last_price']))
            # Open Exchange Rates
            if self.symbol.startswith("EUR"):
                prices.append(float(requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2).json()['rates']['USD']))
            # Frankfurter
            if self.symbol.startswith("EUR"):
                prices.append(float(requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2).json()['rates']['USD']))
        except Exception as e:
            print(f"[API Error] {e}")
        return prices

    def get_price(self):
        """Retorna preço confiável agregado e suavizado (OHLC + timestamp)."""
        prices = self.fetch_sources()
        if prices:
            median_value = np.median(prices)
            adjusted = median_value + OFFSET
            self.current_tick = (ALPHA * adjusted) + (1 - ALPHA) * self.current_tick

        self.stream.append(self.current_tick)

        # OHLC simulado com pequena volatilidade
        high = self.current_tick + VOLATILITY
        low = self.current_tick - VOLATILITY

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "open": self.current_tick,
            "high": high,
            "low": low,
            "close": self.current_tick
        }
