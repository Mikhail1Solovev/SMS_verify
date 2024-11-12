import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_sms(phone, message):
    """
    Отправка SMS через SMSAero API.

    :param phone: Номер телефона в формате E.164 без знака '+'.
    :param message: Текст сообщения.
    :return: Словарь с результатом отправки.
    """
    sms_url = "https://gate.smsaero.ru/v2/sms/send"

    try:
        response = requests.post(
            sms_url,
            auth=(os.getenv("SMSAERO_EMAIL"), os.getenv("SMSAERO_API_KEY")),
            data={
                "number": phone,
                "text": message,
            }
        )
        response.raise_for_status()
        result = response.json()
        logger.debug(f"SMS отправлено успешно: {result}")
        return result
    except requests.RequestException as e:
        logger.error(f"Ошибка при отправке SMS: {e}")
        return {"status": "error", "error": str(e)}
