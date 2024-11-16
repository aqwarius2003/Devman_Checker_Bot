import requests
from telegram import Bot
from dotenv import load_dotenv
from time import sleep
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, chat_id, message):
    bot.send_message(chat_id=chat_id, text=message)


def main():

    load_dotenv()
    devmn_token = os.getenv('DEVMN_API_TOKEN')
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')

    if not all([devmn_token, tg_bot_token, tg_chat_id]):
        logger.error("Не удалось загрузить все необходимые переменные окружения? Проверьте файл .env")
        return

    bot = Bot(token=tg_bot_token)

    while True:
        try:
            url = 'https://dvmn.org/api/long_polling/'

            headers = {
                'Authorization': f'Token {devmn_token}'
            }
            params = {}
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    timeout=90)
            response.raise_for_status()
            result_check = response.json()

            if result_check['status'] == 'found':
                params['timestamp'] = result_check['last_attempt_timestamp']
                for result in result_check['new_attempts']:
                    message = (
                        f'Проверена работа: {result["lesson_title"]}. '
                        f'{"Есть ошибки. Приступите к исправлению: " if result["is_negative"] else ""}'
                        f'{result["lesson_url"]} '
                        f'{"Все хорошо, открыт новый урок" if not result["is_negative"] else ""}'
                    )
                    send_message(bot, tg_chat_id, message)
            elif result_check['status'] == 'timeout':
                logger.exception(f'Timeout {result_check["timestamp_to_request"]}')
                params['timestamp'] = result_check['timestamp_to_request']
        except requests.exceptions.ReadTimeout:
            logger.warning('ReadTimeout occurred, retrying in 5 seconds...')
            sleep(5)
        except requests.exceptions.ConnectionError as e:
            logger.error(f'ConnectionError: {e}, retrying in 5 seconds...')
            sleep(5)
        except Exception as err:
            logger.exception(f'Unexpected error: {err}')


if __name__ == '__main__':
    main()
