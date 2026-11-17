from flask_sqlalchemy import SQLAlchemy
import openai
import dotenv
import logging
import requests
import uuid
import httpx
import os

# Настройка логгирования
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из файла .env
try:
    env = dotenv.dotenv_values(".env")
    GIGACHAT_CREDENTIALS = env["GIGACHAT_CREDENTIALS"]
    GIGACHAT_SCOPE = env.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
except FileNotFoundError:
    raise FileNotFoundError("Файл .env не найден. Убедитесь, что он существует в корневой директории проекта.")
except KeyError as e:
    raise KeyError(f"Переменная окружения {str(e)} не найдена в файле .env. Проверьте его содержимое.")

# Путь к сертификату Минцифры (положите файл рядом с models.py)
CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "russian_trusted_root_ca.pem")

# Инициализируем SQLAlchemy
db = SQLAlchemy()


class ChatHistory(db.Model):
    """
    Модель SQLAlchemy для хранения истории общения пользователя с LLM.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    llm_reply = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


def get_gigachat_token():
    """
    Получение Access Token для GigaChat API через OAuth.
    Возвращает строку токена.
    """
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    payload = f"scope={GIGACHAT_SCOPE}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {GIGACHAT_CREDENTIALS}",
    }
    try:
        # Используем сертификат Минцифры вместо отключения проверки
        response = requests.post(url, data=payload, headers=headers, verify=CERT_PATH)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Ошибка получения токена GigaChat: {e}")
        raise


class LLMService:
    """
    Класс для взаимодействия с GigaChat через OpenAI-совместимый API.
    """
    def __init__(self, prompt_file):
        with open(prompt_file, encoding='utf-8') as f:
            self.sys_prompt = f.read()
        self.model = "GigaChat-2"  # или "GigaChat-2-Pro", "GigaChat-2-Max", "GigaChat-3-Ultra"

    def chat(self, message):
        """
        Отправляет сообщение к GigaChat и возвращает ответ.
        """
        try:
            token = get_gigachat_token()

            # Явно передаём httpx-клиент с сертификатом Минцифры
            http_client = httpx.Client(verify=CERT_PATH)

            client = openai.OpenAI(
                api_key=token,
                base_url="https://api.giga.chat/v1",
                http_client=http_client,
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.sys_prompt},
                    {"role": "user", "content": message},
                ],
                temperature=1.0,
                max_tokens=1024,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Ошибка GigaChat: {str(e)}")
            return f"Произошла ошибка: {str(e)}"


llm_1 = LLMService('prompts/prompt_1.txt')


def chat_with_llm(user_message):
    """
    Чат с использованием сервиса LLM.
    """
    return llm_1.chat(user_message)