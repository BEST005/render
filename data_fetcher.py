import pandas as pd
from utils import retry_request, data_cache, validate_address
from config import logger

class DataFetcher:
    def __init__(self, contract_address: str, chain: str = 'ethereum'):
        validate_address(contract_address, chain)
        self.contract = contract_address.lower()
        self.chain = chain
        self.platform_map = {
            'ethereum': 'ethereum',
            'solana': 'solana',
            'bsc': 'binance-smart-chain',
            'polygon': 'polygon-pos'
        }
        self.platform = self.platform_map.get(chain, 'ethereum')
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.coin_id = self._find_coin_id()

    def _find_coin_id(self) -> str:
        cache_key = f"{self.contract}_{self.platform}"
        if cache_key in data_cache:
            return data_cache[cache_key]

        url = f"{self.base_url}/coins/list?include_platform=true"
        response = retry_request(url)
        if response:
            coins = response.json()
            for coin in coins:
                platforms = coin.get('platforms', {})
                if self.contract in str(platforms.get(self.platform, '')):
                    data_cache[cache_key] = coin['id']
                    return coin['id']

        dex_url = f"https://api.dexscreener.com/latest/dex/search?q={self.contract}"
        dex_response = retry_request(dex_url)
        if dex_response and dex_response.json().get('pairs'):
            pair = dex_response.json()['pairs'][0]
            symbol = pair['baseToken']['symbol'].lower()
            data_cache[cache_key] = symbol
            logger.info(f"Fallback DexScreener: {symbol}")
            return symbol

        raise ValueError(f"Монета не найдена. Проверь на DexScreener или CoinGecko.")

    def fetch_historical(self, days: int = 100):
        cache_key = f"{self.coin_id}_historical_{days}"
        if cache_key in data_cache:
            return data_cache[cache_key]

        url = f"{self.base_url}/coins/{self.coin_id}/market_chart?vs_currency=usd&days={days}"
        response = retry_request(url)
        if response:
            data = response.json()
            if 'prices' not in data or len(data['prices']) < 10:
                raise ValueError(f"Недостаточно данных ({len(data.get('prices', []))} точек).")

            prices = pd.DataFrame(data['prices'], columns=['timestamp', 'Price'])
            prices['Date'] = pd.to_datetime(prices['timestamp'], unit='ms')
            prices.set_index('Date', inplace=True)
            volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'Volume'])
            volumes['Date'] = pd.to_datetime(volumes['timestamp'], unit='ms')
            volumes['Volume'] = volumes['Volume'].fillna(method='ffill')
            df = prices.join(volumes.set_index('Date'), how='inner')
            result = df['Price'].values, df['Volume'].values, df
            data_cache[cache_key] = result
            return result

        raise ValueError("Не удалось получить данные.")