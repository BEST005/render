import os
from dotenv import load_dotenv
import logging

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)