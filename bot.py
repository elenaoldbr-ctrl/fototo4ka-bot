# bot.py
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from config import Config
import logging
import time
import re

logger = logging.getLogger(__name__)

class FotoTochkaBot:
    def __init__(self):
        logger.info("Инициализация бота ФотоТочка...")
        self.vk_session = vk_api.VkApi(token=Config.VK_GROUP_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk_session, Config.VK_GROUP_ID)
        self.vk = self.vk_session.get_api()
        self.user_sessions = {}
        logger.info("Бот ФотоТочка инициализирован успешно")
    
    def send_message(self, user_id, message):
        try:
            if len(message) > 4096:
                chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
                for chunk in chunks:
                    self.vk.messages.send(
                        user_id=user_id,
                        message=chunk,
                        random_id=get_random_id()
                    )
                    time.sleep(Config.BOT_SETTINGS["typing_delay"])
            else:
                self.vk.messages.send(
                    user_id=user_id,
                    message=message,
                    random_id=get_random_id()
                )
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    def get_user_session(self, user_id):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'history': [],
                'message_count': 0,
                'last_questions': []
            }
        return self.user_sessions[user_id]
    
    def find_best_answer(self, text):
        text_lower = text.lower().strip()
        clean_text = re.sub(r'[^\w\s]', '', text_lower)
        
        command_map = {
            '/start': 'start',
            'start': 'start',
            'начать': 'start',
            '/help': 'help', 
            'help': 'help',
            'помощь': 'help',
            '/clear': 'clear',
            'clear': 'clear',
            'очистить': 'clear',
            '/services': 'услуг',
            'services': 'услуг',
            'услуги': 'услуг',
            '/price': 'цена',
            'price': 'цена',
            'цены': 'цена',
            '/photobook': 'фотокниг',
            'photobook': 'фотокниг',
            'фотокниг': 'фотокниг',
            '/canvas': 'холст',
            'canvas': 'холст',
            'холст': 'холст',
            '/contacts': 'контакт',
            'contacts': 'контакт',
            'контакты': 'контакт',
            '/address': 'адрес',
            'address': 'адрес',
            'адрес': 'адрес',
            '/schedule': 'график',
            'schedule': 'график',
            'график': 'график',
            '/delivery': 'доставк',
            'delivery': 'доставк',
            'доставк': 'доставк',
            '/payment': 'оплат',
            'payment': 'оплат',
            'оплат': 'оплат'
        }
        
        if text_lower in command_map:
            return Config.KNOWLEDGE_BASE[command_map[text_lower]]
        
        keywords_priority = [
            ['фотопечат', 'распечат', 'печат', 'снимк', 'фотограф'],
            ['10×15', '15×21', 'а4', 'а3', 'формат'],
            ['фотокниг', 'фотоальбом', 'альбом', 'книг'],
            ['холст', 'картин', 'полотно', 'сувенир', 'кружк', 'магнит'],
            ['сколько стоит', 'цена', 'стоимость', 'прайс', 'ценник'],
            ['контакт', 'телефон', 'email', 'позвонить', 'связаться'],
            ['адрес', 'где находитесь', 'метро', 'проезд', 'локация'],
            ['график', 'время работы', 'работаете', 'когда', 'воскресенье', 'суббот'],
            ['услуг', 'предлагаете', 'делаете', 'изготовлени'],
            ['доставк', 'курьер', 'самовывоз', 'забрать', 'привезти'],
            ['оплат', 'рассчет', 'картой', 'наличными', 'безнал'],
            ['привет', 'здравствуйте', 'добрый', 'доброе'],
            ['спасибо', 'благодарю']
        ]
        
        for keyword_group in keywords_priority:
            for keyword in keyword_group:
                if keyword in clean_text:
                    for kb_key, answer in Config.KNOWLEDGE_BASE.items():
                        if kb_key in keyword_group:
                            logger.info(f"Найден ответ по ключевому слову: {keyword}")
                            return answer
        
        return Config.KNOWLEDGE_BASE['непонятно']
    
    def update_user_history(self, user_id, user_message, bot_response):
        user_session = self.get_user_session(user_id)
        user_session['history'].append({
            'user': user_message,
            'bot': bot_response
        })
        user_session['last_questions'].append(user_message.lower())
        if len(user_session['last_questions']) > 5:
            user_session['last_questions'].pop(0)
        user_session['message_count'] += 1
        max_history = Config.BOT_SETTINGS["max_history"]
        if len(user_session['history']) > max_history:
            user_session['history'] = user_session['history'][-max_history:]
    
    def is_repeated_question(self, user_id, current_message):
        user_session = self.get_user_session(user_id)
        current_lower = current_message.lower()
        for prev_question in user_session['last_questions']:
            words_current = set(current_lower.split())
            words_prev = set(prev_question.split())
            common_words = words_current.intersection(words_prev)
            if len(common_words) >= 2:
                return True
        return False
    
    def get_contextual_response(self, user_id, current_message):
        user_session = self.get_user_session(user_id)
        if self.is_repeated_question(user_id, current_message):
            return "📞 Вы уже спрашивали об этом! Уточните вопрос или позвоните нам: +7 (999) 123-45-67"
        if user_session['message_count'] == 0 and any(word in current_message.lower() for word in ['привет', 'здравствуй', 'start']):
            return Config.KNOWLEDGE_BASE['start']
        return self.find_best_answer(current_message)
    
    def run(self):
        logger.info("Бот ФотоТочка начал прослушивание сообщений...")
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        message = event.object.message
                        user_id = message['from_id']
                        text = message['text'].strip()
                        if not text:
                            continue
                        logger.info(f"Сообщение от {user_id}: {text}")
                        try:
                            self.vk.messages.setActivity(
                                user_id=user_id,
                                type='typing'
                            )
                        except:
                            pass
                        response = self.get_contextual_response(user_id, text)
                        self.update_user_history(user_id, text, response)
                        self.send_message(user_id, response)
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(10)