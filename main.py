import streamlit as st
import time
from datetime import datetime
from engine import AuraxisEngine
from interface import apply_ui_v10, render_radar_block

st.set_page_config(page_title="AURAXIS V10 RADAR", layout="wide")
apply_ui_v10()

if 'engine' not in st.session_state:
    st.session_state.engine = AuraxisEngine(alfa=0.25)

placeholder = st.empty()

while True:
    with placeholder.container():
        df, pips, p_refinado, fonte_ativa = st.session_state.engine.get_data_v10()
        
        if not df.empty:
            pos_signal = st.session_state.engine.calculate_radar(df, "POSITION", 0, p_refinado)
            trend_dir = 1 if pos_signal and pos_signal['tipo'] == "COMPRA" else (-1 if pos_signal else 0)
            
            cor_pips = "#3fb950" if pips >= 0 else "#f85149"
            st.markdown(f"""
                <div class='header-radar'>
                    <div style='font-size: 0.8rem; color: #8b949e;'>FONTE ATIVA: {fonte_ativa}</div>
                    <h1 style='margin:0; font-family:monospace; font-size: 3.5rem;'>{p_refinado:.5f}</h1>
                    <span style='color:{cor_pips}; font-weight:bold;'>{"+" if pips>=0 else ""}{pips:.2f} PIPS HOJE</span>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_radar_block("SCALPER", st.session_state.engine.calculate_radar(df, "SCALPER", trend_dir, p_refinado))
            with c2: render_radar_block("DAY TRADE", st.session_state.engine.calculate_radar(df, "DAY", trend_dir, p_refinado))
            with c3: render_radar_block("SWING", st.session_state.engine.calculate_radar(df, "SWING", trend_dir, p_refinado))
            with c4: render_radar_block("POSITION", pos_signal)
            
            st.caption(f"Sincronia: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("📡 Buscando dados...")
            
    time.sleep(1)
