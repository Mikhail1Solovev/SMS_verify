from smsaero import SmsAero, SmsAeroException
from django.conf import settings

def send_sms(phone: str, message: str) -> dict:
    """
    Sends an SMS message

    Parameters:
    phone (str): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.

    Returns:
    dict: A dictionary containing the response from the SmsAero API.
    """
    api = SmsAero(settings.SMSAERO_EMAIL, settings.SMSAERO_API_KEY)
    try:
        response = api.send_sms(phone, message)
        return response
    except SmsAeroException as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}
