from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analyzer import CryptoAnalyzer
from config import logger
from telegram.error import TelegramError

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "👋 Привет! Анализ крипто по контракту.\n\n"
            "/analyze <адрес> [chain] или /analyze <адрес> (кнопки).\n"
            "/help — помощь."
        )
    except TelegramError as e:
        logger.error(f"Start error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "🆘 **Помощь:**\n"
            "- Адрес: 0x... (ETH/BSC/Poly), So... (Solana).\n"
            "- Chain: ethereum, solana, bsc, polygon.\n"
            "- Время: ~10 сек."
        )
    except TelegramError as e:
        logger.error(f"Help error: {e}")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("❌ Укажи адрес! /analyze 0x...")
            return

        contract = context.args[0]
        if len(context.args) > 1:
            chain = context.args[1].lower()
            await update.message.reply_text(f"🔄 Анализ {contract} на {chain}...")
            analyzer = CryptoAnalyzer(contract, chain)
            text, graph_buf = analyzer.analyze()
            await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
            if graph_buf:
                await update.message.reply_photo(photo=graph_buf, caption="📈 График")
        else:
            keyboard = [
                [InlineKeyboardButton("🟢 Ethereum", callback_data=f"analyze_eth_{contract}"),
                 InlineKeyboardButton("☀️ Solana", callback_data=f"analyze_sol_{contract}")],
                [InlineKeyboardButton("🔶 BSC", callback_data=f"analyze_bsc_{contract}"),
                 InlineKeyboardButton("🔷 Polygon", callback_data=f"analyze_poly_{contract}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🌐 Выбери chain для {contract}:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        await update.message.reply_text("❌ Ошибка. /start.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.data.startswith('analyze_'):
            parts = query.data.split('_', 2)
            chain_map = {'eth': 'ethereum', 'sol': 'solana', 'bsc': 'bsc', 'poly': 'polygon'}
            chain = chain_map.get(parts[1], 'ethereum')
            contract = parts[2]

            await query.edit_message_text(f"🔄 Анализ {contract} на {chain}...")
            analyzer = CryptoAnalyzer(contract, chain)
            text, graph_buf = analyzer.analyze()
            await query.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
            if graph_buf:
                await query.message.reply_photo(photo=graph_buf, caption="📈 График")
    except Exception as e:
        logger.error(f"Button error: {e}")
        await query.edit_message_text("❌ Ошибка. /start.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Global error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Сбой. /start.")