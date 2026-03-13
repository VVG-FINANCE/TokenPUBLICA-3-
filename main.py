import streamlit as st
import time
from datetime import datetime
from engine import AuraxisEngine
from interface import apply_ui_v10, render_radar_block

st.set_page_config(page_title="AURAXIS V10", layout="wide")
apply_ui_v10()

if 'engine' not in st.session_state:
    st.session_state.engine = AuraxisEngine(alfa=0.25)

placeholder = st.empty()

while True:
    with placeholder.container():
        df, pips, p_refinado, fonte = st.session_state.engine.get_data_v10()
        if not df.empty:
            pos = st.session_state.engine.calculate_radar(df, "POSITION", 0, p_refinado)
            trend = 1 if pos and pos['tipo'] == "COMPRA" else (-1 if pos else 0)
            
            st.markdown(f"<div class='header-radar'><h1>{p_refinado:.5f}</h1><p>Fonte: {fonte} | Ajuste: -300 pips</p></div>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_radar_block("SCALPER", st.session_state.engine.calculate_radar(df, "SCALPER", trend, p_refinado))
            with c2: render_radar_block("DAY TRADE", st.session_state.engine.calculate_radar(df, "DAY", trend, p_refinado))
            with c3: render_radar_block("SWING", st.session_state.engine.calculate_radar(df, "SWING", trend, p_refinado))
            with c4: render_radar_block("POSITION", pos)
            st.caption(f"Ciclo: 2s | Atualizado: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("📡 Conectando...")
    time.sleep(2)
