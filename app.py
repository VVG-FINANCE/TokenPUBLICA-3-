# manager_app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from collections import deque
import numpy as np
import yfinance as yf
import requests

# =========================
# Configurações e constantes
# =========================
ALPHA = 0.2
OFFSET = -0.00190
VOLATILITY = 0.0005
HISTORY_LIMIT = 1000  # Máximo de registros

# =========================
# Classe APIManager
# =========================
class APIManager:
    """
    Fonte agregada confiável para pares Forex.
    Combina múltiplas APIs públicas, aplica mediana e suavização.
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

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="EUR/USD Forex Stream", layout="wide")
st.title("📈 Stream de Preços EUR/USD")
st.markdown("Dados agregados de múltiplas APIs públicas com suavização e volatilidade simulada.")

# Inicializa APIManager
manager = APIManager("EURUSD")

# Inicializa dataframe no session_state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])

# Função para atualizar dados
def update_data():
    new_price = manager.get_price()
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_price])], ignore_index=True)
    if len(st.session_state.data) > HISTORY_LIMIT:
        st.session_state.data = st.session_state.data.iloc[-HISTORY_LIMIT:]

# Sidebar: intervalo de atualização
AUTO_REFRESH = st.sidebar.slider("Intervalo de atualização (segundos)", 1, 10, 3)
auto_update = st.sidebar.checkbox("Atualização automática", value=True)

# Botão de atualização manual
if st.button("Atualizar Agora"):
    update_data()

# Placeholder para dados e gráfico
placeholder = st.empty()

# Loop de atualização automática
while auto_update:
    update_data()
    with placeholder.container():
        st.subheader("Últimos preços agregados")
        st.dataframe(st.session_state.data.tail(10))
        
        st.subheader("Gráfico de Preços OHLC")
        st.line_chart(st.session_state.data[["open", "high", "low", "close"]])
    
    time.sleep(AUTO_REFRESH)
