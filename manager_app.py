import streamlit as st
import time
from backend.api_manager import APIManager

# Configuração de pips
PIP_SIZE = 0.0001

st.set_page_config(page_title="Monitor de Preços")

st.title("Monitor de Preços - EUR/USD")

# Inicializa o gerenciador de API
if "api" not in st.session_state:
    st.session_state.api = APIManager("EURUSD")

# Input para ajustar o range de pips
pip_range = st.slider("Faixa de Pips", min_value=1, max_value=50, value=10)

# Container para atualização dinâmica
placeholder = st.empty()

# Loop de atualização
while True:
    tick = st.session_state.api.get_price()
    price = tick["close"]

    # Cálculos
    low = price - (pip_range * PIP_SIZE)
    high = price + (pip_range * PIP_SIZE)

    # Atualiza o conteúdo do container
    with placeholder.container():
        st.metric(label="Preço Atual", value=f"{price:.5f}")
        st.write(f"**Faixa:** {low:.5f} - {high:.5f} (+-{pip_range} pips)")
    
    time.sleep(1)
