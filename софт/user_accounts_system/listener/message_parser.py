"""
Парсер сообщений для извлечения контекста
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re


@dataclass
class MessageContext:
    """Контекст сообщения"""
    chat_id: str
    message_id: int
    user_id: str
    username: Optional[str]
    text: str
    is_reply: bool = False
    reply_to_message_id: Optional[int] = None
    reply_to_user_id: Optional[str] = None
    mentions: List[str] = None  # Упоминания пользователей
    is_direct_mention: bool = False  # Упоминание нашего аккаунта
    is_question: bool = False
    tone: str = "neutral"  # neutral, friendly, argumentative, humorous
    topic_keywords: List[str] = None
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []
        if self.topic_keywords is None:
            self.topic_keywords = []
        if self.raw_data is None:
            self.raw_data = {}


class MessageParser:
    """Парсер для извлечения контекста из сообщений"""

    # Ключевые слова для определения тона
    ARGUMENTATIVE_KEYWORDS = [
        "неправ", "не согласен", "ошибка", "глупо", "бессмысленно",
        "неверно", "не так", "неправильно"
    ]
    
    FRIENDLY_KEYWORDS = [
        "спасибо", "благодарю", "отлично", "класс", "супер",
        "привет", "здравствуй", "добрый"
    ]
    
    HUMOROUS_KEYWORDS = [
        "хаха", "лол", "кек", "смешно", "прикол",
        "шутка", "юмор", "ахаха"
    ]

    # Вопросы
    QUESTION_PATTERNS = [
        r"\?",
        r"как\s+",
        r"что\s+",
        r"почему\s+",
        r"когда\s+",
        r"где\s+",
        r"кто\s+",
        r"зачем\s+",
    ]

    def __init__(self, account_username: Optional[str] = None):
        """
        Args:
            account_username: Username нашего аккаунта для определения прямых упоминаний
        """
        self.account_username = account_username

    def parse(self, message_data: Dict[str, Any]) -> MessageContext:
        """
        Парсит сообщение и извлекает контекст
        
        Args:
            message_data: Данные сообщения от MTProto клиента
            
        Returns:
            MessageContext с извлеченным контекстом
        """
        text = message_data.get("text", "") or message_data.get("message", "")
        chat_id = str(message_data.get("chat_id", ""))
        message_id = message_data.get("id", 0)
        user_id = str(message_data.get("from_id", {}).get("user_id", ""))
        username = message_data.get("from_id", {}).get("username")
        
        # Проверка на reply
        is_reply = False
        reply_to_message_id = None
        reply_to_user_id = None
        if "reply_to" in message_data:
            is_reply = True
            reply_to_message_id = message_data["reply_to"].get("reply_to_msg_id")
            reply_to_user_id = str(message_data["reply_to"].get("from_id", {}).get("user_id", ""))

        # Извлечение упоминаний
        mentions = self._extract_mentions(text)
        is_direct_mention = self._is_direct_mention(text, mentions)

        # Определение тона
        tone = self._detect_tone(text)

        # Проверка на вопрос
        is_question = self._is_question(text)

        # Извлечение ключевых слов темы
        topic_keywords = self._extract_topic_keywords(text)

        return MessageContext(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            username=username,
            text=text,
            is_reply=is_reply,
            reply_to_message_id=reply_to_message_id,
            reply_to_user_id=reply_to_user_id,
            mentions=mentions,
            is_direct_mention=is_direct_mention,
            is_question=is_question,
            tone=tone,
            topic_keywords=topic_keywords,
            raw_data=message_data,
        )

    def _extract_mentions(self, text: str) -> List[str]:
        """Извлечь упоминания из текста"""
        mentions = []
        # Упоминания вида @username
        mention_pattern = r"@(\w+)"
        matches = re.findall(mention_pattern, text)
        mentions.extend(matches)
        return mentions

    def _is_direct_mention(self, text: str, mentions: List[str]) -> bool:
        """Проверить, адресовано ли сообщение нашему аккаунту"""
        if not self.account_username:
            return False
        
        # Проверка упоминания
        if self.account_username.lower() in [m.lower() for m in mentions]:
            return True
        
        # Проверка прямого обращения (если это reply на наше сообщение)
        # Это будет обрабатываться на уровне выше
        
        return False

    def _detect_tone(self, text: str) -> str:
        """Определить тон сообщения"""
        text_lower = text.lower()
        
        # Проверка на аргументативность
        if any(keyword in text_lower for keyword in self.ARGUMENTATIVE_KEYWORDS):
            return "argumentative"
        
        # Проверка на дружелюбность
        if any(keyword in text_lower for keyword in self.FRIENDLY_KEYWORDS):
            return "friendly"
        
        # Проверка на юмор
        if any(keyword in text_lower for keyword in self.HUMOROUS_KEYWORDS):
            return "humorous"
        
        return "neutral"

    def _is_question(self, text: str) -> bool:
        """Проверить, является ли сообщение вопросом"""
        text_lower = text.lower().strip()
        
        # Проверка паттернов вопросов
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False

    def _extract_topic_keywords(self, text: str) -> List[str]:
        """Извлечь ключевые слова темы (упрощенная версия)"""
        # В реальной системе здесь можно использовать NLP для извлечения тем
        # Пока просто возвращаем пустой список
        # Можно добавить простую логику на основе частых слов
        keywords = []
        
        # Удаляем стоп-слова и извлекаем существительные/важные слова
        # Это упрощенная версия, в продакшене нужен полноценный NLP
        words = re.findall(r'\b[а-яё]{4,}\b', text.lower())
        
        # Фильтруем слишком частые слова
        stop_words = {"это", "что", "как", "где", "когда", "почему", "который", "которые"}
        keywords = [w for w in words if w not in stop_words][:5]
        
        return keywords

