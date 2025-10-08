import torch
import torch.nn as nn
import numpy as np
from config import logger
import traceback

class LSTMPredictor(nn.Module):
    def __init__(self, input_size: int = 2, hidden_size: int = 50, num_layers: int = 1, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.linear(out[:, -1, :])
        return out

def prepare_sequences(prices: np.ndarray, volumes: np.ndarray, seq_length: int = 60):
    if len(prices) < seq_length + 1:
        raise ValueError(f"Недостаточно данных (минимум {seq_length + 1}).")
    data = np.column_stack((prices, volumes))
    mean, std = np.mean(data, axis=0), np.std(data, axis=0)
    if np.any(std == 0):
        raise ValueError("Данные константны.")
    normalized = (data - mean) / std
    X, y = [], []
    for i in range(len(normalized) - seq_length):
        X.append(normalized[i:i+seq_length])
        y.append(normalized[i+seq_length, 0])
    return np.array(X), np.array(y), mean[0], std[0]

def train_predictor(X: np.ndarray, y: np.ndarray, seq_length: int, epochs: int = 20, lr: float = 0.001):
    try:
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        X_train = torch.from_numpy(X_train).float()
        y_train = torch.from_numpy(y_train).float()
        X_test = torch.from_numpy(X_test).float()
        y_test = torch.from_numpy(y_test).float()

        model = LSTMPredictor(input_size=X.shape[2])
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X_train)
            loss = criterion(outputs.squeeze(), y_train)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            pred = model(X_test).squeeze().numpy()
        return model, pred, y_test.numpy()
    except Exception as e:
        logger.error(f"ML error: {e}\n{traceback.format_exc()}")
        raise RuntimeError(f"Ошибка ML: {e}.")