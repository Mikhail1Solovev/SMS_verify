import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from smsaero import SmsAero, SmsAeroException

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

SMSAERO_EMAIL = os.getenv('SMSAERO_EMAIL')
SMSAERO_API_KEY = os.getenv('SMSAERO_API_KEY')


def send_sms(phone: str, message: str) -> dict:
    """
    Отправляет СМС-сообщение.

    Параметры:
    - phone (str): Номер телефона в виде строки с символом '+' (например, '+79174044144').
    - message (str): Текст СМС-сообщения.

    Возвращает:
    - dict: Словарь с ответом от API SmsAero.
    """
    api = SmsAero(email=SMSAERO_EMAIL, api_key=SMSAERO_API_KEY)
    try:
        response = api.send_sms(phone, message)
        logger.debug(f"SMS отправлено на {phone}: {message}")
        return response
    except SmsAeroException as e:
        logger.error(f"Произошла ошибка при отправке СМС: {e}")
        return {"error": str(e)}
