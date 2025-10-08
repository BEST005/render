import matplotlib.pyplot as plt
from io import BytesIO
from datetime import timedelta
from data_fetcher import DataFetcher
from ml_predictor import prepare_sequences, train_predictor
from risk_manager import RiskManager
from config import logger
import numpy as np
import torch
import traceback

class CryptoAnalyzer:
    def __init__(self, contract: str, chain: str = 'ethereum'):
        self.fetcher = DataFetcher(contract, chain)

    def analyze(self, days: int = 100):
        text = None
        buf = None
        try:
            prices, volumes, df = self.fetcher.fetch_historical(days)
            seq_length = min(60, len(prices) - 1)

            current_price = prices[-1]
            risk_mgr = RiskManager(prices)
            var_pct = risk_mgr.var() * 100
            sharpe = risk_mgr.sharpe()

            try:
                X, y, price_mean, price_std = prepare_sequences(prices, volumes, seq_length)
                model, test_pred, test_actual = train_predictor(X, y, seq_length)
                rmse = np.sqrt(np.mean((test_pred - test_actual)**2)) * price_std

                last_seq = X[-1].reshape(1, seq_length, X.shape[2])
                future = []
                current_seq = torch.from_numpy(last_seq).float()
                for _ in range(5):
                    with torch.no_grad():
                        next_norm = model(current_seq).item()
                        next_price = next_norm * price_std + price_mean
                        future.append(next_price)
                    new_seq = np.roll(current_seq.numpy().squeeze(), -1, axis=0)
                    new_seq[-1, 0] = next_norm
                    current_seq = torch.from_numpy(new_seq.reshape(1, seq_length, X.shape[2])).float()

                change_pct = (future[0] - current_price) / current_price * 100 if current_price > 0 else 0
                rec = '🟢 Buy' if change_pct > 2 and sharpe > 1 and rmse < current_price*0.05 else '🟡 Hold' if change_pct > -2 else '🔴 Sell'

                buf = BytesIO()
                plt.figure(figsize=(10, 5))
                plt.plot(df.index, prices, label='Historical', color='blue')
                future_dates = [df.index[-1] + timedelta(days=i+1) for i in range(5)]
                plt.plot(future_dates, future, label='Predicted', linestyle='--', color='green')
                plt.title(f'{self.fetcher.coin_id.upper()} ({self.fetcher.chain.upper()})')
                plt.xlabel('Date')
                plt.ylabel('Price (USD)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                plt.close()

                text = f"""🚀 **Анализ {self.fetcher.coin_id.upper()} на {self.fetcher.chain.upper()}**

💰 Цена: ${current_price:,.2f} USD
📊 RMSE: ${rmse:,.2f} ({(rmse / current_price * 100):.1f}%)
🔮 Предсказания (5 дней): ${', '.join([f'{p:,.2f}' for p in future])}
📈 Изменение: {change_pct:+.2f}%
⚠️ VaR 95%: {var_pct:.2f}%
📉 Sharpe: {sharpe:.2f}
💡 **Рекомендация:** {rec}

*Не финансовый совет!*
"""
            except Exception as ml_e:
                logger.warning(f"ML fallback: {ml_e}")
                text = f"""🚀 **Базовый анализ {self.fetcher.coin_id.upper()}**

💰 Цена: ${current_price:,.2f} USD
⚠️ VaR 95%: {var_pct:.2f}%
📉 Sharpe: {sharpe:.2f}
💡 **Рекомендация:** 🟡 Hold (ML недоступен)

*Не финансовый совет!*
"""

            return text, buf

        except Exception as e:
            logger.error(f"Analyzer error: {e}\n{traceback.format_exc()}")
            return f"❌ Ошибка: {str(e)}\nПопробуй /help.", None