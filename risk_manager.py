import numpy as np

class RiskManager:
    def __init__(self, prices: np.ndarray):
        if len(prices) < 2:
            raise ValueError("Недостаточно цен для рисков.")
        self.returns = np.diff(np.log(prices + 1e-8))

    def var(self, confidence: float = 0.95) -> float:
        return np.percentile(self.returns, (1 - confidence) * 100)

    def sharpe(self, risk_free: float = 0.02) -> float:
        mean_ret = np.mean(self.returns) * 252
        std_ret = np.std(self.returns) * np.sqrt(252)
        return (mean_ret - risk_free) / std_ret if std_ret > 0 else 0