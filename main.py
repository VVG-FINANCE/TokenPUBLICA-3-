import streamlit as st
import time
from datetime import datetime
from engine import AuraxisEngine
from interface import apply_ui_v10, render_radar_block

st.set_page_config(page_title="AURAXIS V10 RADAR", layout="wide")
apply_ui_v10()

if 'engine' not in st.session_state: st.session_state.engine = AuraxisEngine()

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
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_radar_block("SCALPER (1M/5M)", st.session_state.engine.calculate_radar(df, "SCALPER", trend, p_refinado))
            with c2: render_radar_block("DAY TRADE (15M/1H)", st.session_state.engine.calculate_radar(df, "DAY", trend, p_refinado))
            with c3: render_radar_block("SWING (4H/DIÁRIO)", st.session_state.engine.calculate_radar(df, "SWING", trend, p_refinado))
            with c4: render_radar_block("POSITION (SEMANAL)", pos)
            st.caption(f"Radar V10 em Operação | Sincronia: {datetime.now().strftime('%H:%M:%S')}")
        else: st.warning("📡 Conectando aos Satélites de Dados...")
    time.sleep(2)
