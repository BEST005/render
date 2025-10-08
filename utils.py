import re
import time
import requests
from typing import Optional

# Кэш
data_cache = {}

def validate_address(contract: str, chain: str) -> bool:
    if not contract:
        raise ValueError("Адрес контракта пустой.")

    if chain == 'solana':
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', contract):
            raise ValueError("Неверный формат Solana-адреса. Пример: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    else:
        if not re.match(r'^0x[a-fA-F0-9]{40}$', contract):
            raise ValueError("Неверный формат адреса (0x + 40 hex). Пример: 0x2260fac5e5542a773aa44fbcfedf7c193bc2c599")

    return True

def retry_request(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                raise ValueError(f"API error: {response.status_code}")
        except (requests.RequestException, ConnectionError) as e:
            from config import logger
            logger.warning(f"Retry {attempt+1}/{max_retries} for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)
            else:
                raise ConnectionError(f"Сетевой сбой: {e}")
    return None