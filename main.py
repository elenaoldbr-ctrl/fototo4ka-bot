# main.py
from bot import FotoTochkaBot
import os
import logging
import threading
from flask import Flask

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 ФотоТочка Бот работает!"

@app.route('/health')
def health():
    return "OK"

@app.route('/status')
def status():
    return {
        "status": "running", 
        "service": "ФотоТочка Бот",
        "version": "2.0"
    }

def run_bot():
    try:
        logging.info("Запуск бота ФотоТочка...")
        bot = FotoTochkaBot()
        bot.run()
    except Exception as e:
        logging.error(f"Ошибка бота: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)