# backend/auraxis_engine_v10_fully_integrated.py
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from collections import deque
import streamlit as st
import time
from datetime import datetime

# -------------------------------------------------------
# Motor de preço integrado (API + ajustes internos)
# -------------------------------------------------------
ALPHA_API = 0.2          # Suavização interna da API
OFFSET_API = -0.00190     # Ajuste interno da API
OFF_SET_ENGINE = 0.0300   # Ajuste do AuraxisEngine (pips fixos)

class APIManager:
    def __init__(self):
        self.stream = deque([1.15]*500, maxlen=500)
        self.current_tick = 1.15

    def get_price(self):
        """
        Coleta preço de múltiplas fontes, aplica median + OFFSET_API + suavização ALPHA_API
        """
        prices = []
        try:
            prices.append(float(yf.Ticker("EURUSD=X").fast_info['last_price']))
            prices.append(float(requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2).json()['rates']['USD']))
            prices.append(float(requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2).json()['rates']['USD']))
        except: pass

        if prices:
            median_price = np.median(prices) + OFFSET_API
            self.current_tick = (ALPHA_API * median_price) + ((1 - ALPHA_API) * self.current_tick)

        self.stream.append(self.current_tick)
        return self.current_tick

# -------------------------------------------------------
# Motor AuraxisEngine totalmente integrado
# -------------------------------------------------------
class AuraxisEngine:
    def __init__(self, alfa=0.25):
        self.alfa = alfa
        self.preco_suavizado = None
        self.OFF_SET = OFF_SET_ENGINE
        self.api_manager = APIManager()

    def get_price_integrated(self):
        """
        Preço refinado totalmente interno.
        Combina APIManager + suavização AuraxisEngine.
        """
        try:
            raw_price = self.api_manager.get_price()
            if self.preco_suavizado is None:
                self.preco_suavizado = raw_price
            else:
                self.preco_suavizado = (raw_price * self.alfa) + (self.preco_suavizado * (1 - self.alfa))
            return self.preco_suavizado, "API_TOTAL"
        except:
            return 0.0, "ERRO"

    def get_data_v10(self, ticker="EURUSD=X"):
        try:
            data = yf.download(ticker, period="1mo", interval="15m", progress=False)
            if data.empty: return pd.DataFrame(), 0.0, 0.0, "OFFLINE"

            p_refinado, fonte = self.get_price_integrated()
            p_ontem = yf.download(ticker, period="2d", interval="1d", progress=False)['Close'].iloc[-2]
            pips_diff = (p_refinado - p_ontem) * 10000

            df = data[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['open', 'high', 'low', 'close']

            return df, float(pips_diff), p_refinado, fonte

        except:
            return pd.DataFrame(), 0.0, 0.0, "ERRO"

    def calculate_radar(self, df, mode="DAY", trend_direction=0, p_refinado=None):
        p_atual = p_refinado if p_refinado else float(df['close'].iloc[-1])
        p_calc = p_atual - self.OFF_SET

        params = {
            "SCALPER": {"p": 10, "m": 1.5},
            "DAY": {"p": 24, "m": 2.2},
            "SWING": {"p": 50, "m": 3.8},
            "POSITION": {"p": 120, "m": 5.5}
        }
        p, m = params[mode]["p"], params[mode]["m"]

        ma = df['close'].rolling(p).mean().iloc[-1]
        std = df['close'].rolling(p).std().iloc[-1] + 1e-9
        z_score = (p_calc - ma) / std

        if mode != "POSITION" and trend_direction != 0:
            if (trend_direction > 0 and z_score < 0) or (trend_direction < 0 and z_score > 0):
                return None

        atr = (df['high'] - df['low']).rolling(p).mean().iloc[-1]
        z_inf, z_sup = p_calc - (atr * 0.4), p_calc + (atr * 0.4)

        if z_score > 1.3:
            return {
                "tipo": "COMPRA",
                "z_inf": z_inf,
                "z_sup": z_sup,
                "tp": [p_calc + (atr * m), p_calc + (atr * m * 1.3)],
                "sl": [p_calc - (atr * m * 0.7), p_calc - (atr * m)],
                "prob": min(65 + (z_score * 4), 98.8),
                "z": z_score
            }
        elif z_score < -1.3:
            return {
                "tipo": "VENDA",
                "z_inf": z_inf,
                "z_sup": z_sup,
                "tp": [p_calc - (atr * m), p_calc - (atr * m * 1.3)],
                "sl": [p_calc + (atr * m * 0.7), p_calc + (atr * m)],
                "prob": min(65 + (abs(z_score) * 4), 98.8),
                "z": z_score
            }
        return None

# -------------------------------------------------------
# Interface Streamlit
# -------------------------------------------------------
def apply_ui_v10():
    st.markdown("""
        <style>
        .stApp { background-color: #040508; color: #ffffff; }
        .header-radar { background: linear-gradient(90deg, #0d1117 0%, #161b22 100%); padding: 25px; border-radius: 15px; border-bottom: 2px solid #30363d; text-align: center; }
        .card-radar { background: #0d1117; border: 1px solid #21262d; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
        .tag-buy { color: #3fb950; font-weight: bold; background: rgba(63, 185, 80, 0.1); padding: 2px 8px; border-radius: 4px; }
        .tag-sell { color: #f85149; font-weight: bold; background: rgba(248, 81, 73, 0.1); padding: 2px 8px; border-radius: 4px; }
        .zone-label { color: #8b949e; font-size: 0.7rem; letter-spacing: 1px; }
        </style>
    """, unsafe_allow_html=True)

def render_radar_block(title, data):
    with st.container():
        if data:
            tag = "tag-buy" if data['tipo'] == "COMPRA" else "tag-sell"
            st.markdown(f"""
                <div class='card-radar'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-weight:bold;'>{title}</span>
                        <span class='{tag}'>{data['tipo']}</span>
                    </div>
                    <div style='margin-top:10px;'><span class='zone-label'>ZONA DE ENTRADA ATIVA</span><br>
                    <code style='color:#58a6ff;'>{data['z_inf']:.5f} — {data['z_sup']:.5f}</code></div>
                    <div style='display:flex; gap:10px; margin-top:10px;'>
                        <div style='flex:1;'><span class='zone-label' style='color:#3fb950;'>ALVOS (TP)</span><br><b>{data['tp'][0]:.5f}</b><br><b>{data['tp'][1]:.5f}</b></div>
                        <div style='flex:1;'><span class='zone-label' style='color:#f85149;'>RISCO (SL)</span><br><b>{data['sl'][0]:.5f}</b><br><b>{data['sl'][1]:.5f}</b></div>
                    </div>
                    <div style='margin-top:10px; font-size:0.75rem; color:#8b949e;'>CONFIANÇA: <b>{data['prob']:.1f}%</b></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='card-radar' style='opacity:0.3;'><b>{title}</b><br><span class='zone-label'>AGUARDANDO ALINHAMENTO...</span></div>", unsafe_allow_html=True)

# -------------------------------------------------------
# Loop principal Streamlit
# -------------------------------------------------------
st.set_page_config(page_title="AURAXIS V10 RADAR", layout="wide")
apply_ui_v10()

if 'engine' not in st.session_state:
    st.session_state.engine = AuraxisEngine()

placeholder = st.empty()
while True:
    with placeholder.container():
        df, pips, p_refinado, fonte = st.session_state.engine.get_data_v10()
        if not df.empty:
            pos = st.session_state.engine.calculate_radar(df, "POSITION", 0, p_refinado)
            trend = 1 if pos and pos['tipo'] == "COMPRA" else (-1 if pos else 0)
            cor = "#3fb950" if pips >= 0 else "#f85149"

            st.markdown(f"""
                <div class='header-radar'>
                    <div style='font-size: 0.8rem;'>FONTE: {fonte} | AJUSTE: -300 pips</div>
                    <h1 style='margin:0; font-size: 3.5rem;'>{p_refinado:.5f}</h1>
                    <span style='color:{cor}; font-weight:bold;'>{"+" if pips>=0 else ""}{pips:.1f} PIPS HOJE</span>
                </div>
            """ , unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1: render_radar_block("SCALPER (1M/5M)", st.session_state.engine.calculate_radar(df, "SCALPER", trend, p_refinado))
            with c2: render_radar_block("DAY TRADE (15M/1H)", st.session_state.engine.calculate_radar(df, "DAY", trend, p_refinado))
            with c3: render_radar_block("SWING (4H/DIÁRIO)", st.session_state.engine.calculate_radar(df, "SWING", trend, p_refinado))
            with c4: render_radar_block("POSITION (SEMANAL)", pos)

            st.caption(f"Radar V10 em Operação | Sincronia: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("📡 Conectando aos Satélites de Dados...")
    time.sleep(2)
