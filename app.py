# app.py
import streamlit as st
import pandas as pd
import time
from backend.api_manager import APIManager

# Configuração da página
st.set_page_config(page_title="EUR/USD Forex Stream", layout="wide")

st.title("📈 Stream de Preços EUR/USD")
st.markdown("Dados agregados de múltiplas APIs públicas com suavização e volatilidade simulada.")

# Inicializa o gerenciador
manager = APIManager(symbol="EURUSD")

# Cria dataframe vazio para o stream
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])

# Função para atualizar o dataframe
def update_data():
    new_price = manager.get_price()
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_price])], ignore_index=True)
    if len(st.session_state.data) > 1000:
        st.session_state.data = st.session_state.data.iloc[-1000:]  # limita a 1000 registros

# Botão para atualizar manualmente
if st.button("Atualizar Agora"):
    update_data()

# Atualização automática a cada X segundos
AUTO_REFRESH = st.sidebar.slider("Intervalo de atualização (segundos)", 1, 10, 3)
auto_update = st.sidebar.checkbox("Atualização automática", value=True)

placeholder = st.empty()

while auto_update:
    update_data()
    with placeholder.container():
        st.subheader("Últimos preços agregados")
        st.dataframe(st.session_state.data.tail(10))

        st.subheader("Gráfico de Preços")
        st.line_chart(st.session_state.data[["open", "high", "low", "close"]])

    time.sleep(AUTO_REFRESH)
