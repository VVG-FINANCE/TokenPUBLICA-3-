import pandas as pd
import numpy as np
import yfinance as yf
import requests

class AuraxisEngine:
    def __init__(self, alfa=0.25):
        self.alfa = alfa
        self.preco_suavizado = None
        self.OFF_SET = 0.0300 # Ajuste de 300 pips

    def get_price_redundancy(self):
        try:
            res = requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2).json()
            return float(res['rates']['USD']), "FRANKFURTER"
        except:
            try:
                res = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2).json()
                return float(res['rates']['USD']), "ER-API"
            except:
                ticker = yf.Ticker("EURUSD=X")
                data = ticker.history(period="1d")
                return float(data['Close'].iloc[-1]), "YFINANCE"

    def get_data_v10(self, ticker="EURUSD=X"):
        try:
            data = yf.download(ticker, period="2d", interval="15m", progress=False)
            if data.empty: return pd.DataFrame(), 0.0, 0.0, "OFFLINE"
            
            p_bruto, fonte = self.get_price_redundancy()
            
            if self.preco_suavizado is None:
                self.preco_suavizado = p_bruto
            else:
                self.preco_suavizado = (p_bruto * self.alfa) + (self.preco_suavizado * (1 - self.alfa))
            
            p_ontem = yf.download(ticker, period="2d", interval="1d", progress=False)['Close'].iloc[-2]
            pips_diff = (self.preco_suavizado - p_ontem) * 10000
            
            df = data[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['open', 'high', 'low', 'close']
            return df, float(pips_diff), self.preco_suavizado, fonte
        except:
            return pd.DataFrame(), 0.0, 0.0, "ERRO"

    def calculate_radar(self, df, mode="DAY", trend_direction=0, p_refinado=None):
        p_calculo = (p_refinado - self.OFF_SET) if p_refinado else (float(df['close'].iloc[-1]) - self.OFF_SET)
        
        params = {
            "SCALPER": {"p": 10, "m": 1.5},
            "DAY": {"p": 24, "m": 2.2},
            "SWING": {"p": 50, "m": 3.8},
            "POSITION": {"p": 120, "m": 5.5}
        }
        p, m = params[mode]["p"], params[mode]["m"]
        
        ma = (df['close'] - self.OFF_SET).rolling(p).mean().iloc[-1]
        std = df['close'].rolling(p).std().iloc[-1] + 1e-9
        z_score = (p_calculo - ma) / std
        
        if mode != "POSITION" and trend_direction != 0:
            if (trend_direction > 0 and z_score < 0) or (trend_direction < 0 and z_score > 0):
                return None

        atr = (df['high'] - df['low']).rolling(p).mean().iloc[-1]
        z_inf, z_sup = p_calculo - (atr * 0.4), p_calculo + (atr * 0.4)

        if z_score > 1.3:
            return {"tipo": "COMPRA", "z_inf": z_inf, "z_sup": z_sup, "tp": [p_calculo + (atr * m), p_calculo + (atr * m * 1.3)], "sl": [p_calculo - (atr * m * 0.7), p_calculo - (atr * m)], "prob": min(65 + (z_score * 4), 98.8), "z": z_score}
        elif z_score < -1.3:
            return {"tipo": "VENDA", "z_inf": z_inf, "z_sup": z_sup, "tp": [p_calculo - (atr * m), p_calculo - (atr * m * 1.3)], "sl": [p_calculo + (atr * m * 0.7), p_calculo + (atr * m)], "prob": min(65 + (abs(z_score) * 4), 98.8), "z": z_score}
        return None
