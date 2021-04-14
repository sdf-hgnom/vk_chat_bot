# use  Python ver 3.7.3
"""Эхо-бот для сайта 'В контакте' vk.com
Для работы этого приложения необходимо
в файле   settings.py прописать константы VK_TOKEN,VK_GROUP_ID
В которых записаны смоответственно секретный токен vk.com и group.id сообщества 'В Контакте' с которым будем работать
"""

import logging.config

from typing import Text

import requests
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotMessageEvent, VkBotEventType
from vk_api.utils import get_random_id

from log_settings import log_config
from process_message import MessageProcess, UserTextInputMessage
from settings import VK_TOKEN, VK_GROUP_ID

logging.config.dictConfig(log_config)
log = logging.getLogger('bot')


class Bot:
    """Основной класс бота 'В контакте'
    Отвечает за прием и отправку сообщений в/из VK-сообщества
    """

    def __init__(self) -> None:
        self.token: Text = VK_TOKEN
        self.group_id: Text = VK_GROUP_ID
        self.vk_section = VkApi(token=self.token)
        self.vk_poller = VkBotLongPoll(self.vk_section, group_id=self.group_id)
        self.massage_processor = MessageProcess(bot=self)
        self.api = self.vk_section.get_api()

    def __repr__(self) -> Text:
        return f'{self.__class__.__name__}( {self.group_id}  )'

    def send_image(self, image, to_whom: int):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        photo_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = photo_data[0]['owner_id']
        media_id = photo_data[0]['id']
        attach_id = f'photo{owner_id}_{media_id}'
        params_for_send = {'message': 'Ваш Билет !!',
                           'attachment': attach_id,
                           'peer_id': to_whom,
                           'random_id': get_random_id(),
                           }
        log.info(f'I send message : Image to user {to_whom}')
        self.api.messages.send(**params_for_send)

    def send_message(self, message: Text, to_whom: int) -> None:
        """
        Послать сообщение
        :param message: текст сообщения
        :param to_whom: id пользователя кому посылаем
        :return:
        """
        params_for_send = {'message': message,
                           'peer_id': to_whom,
                           'random_id': get_random_id(),
                           }

        log.info(f'I send message : {message} to user {to_whom}')

        self.api.messages.send(**params_for_send)

    def on_event(self, event: VkBotMessageEvent) -> None:
        """Обработка входящих сообщений"""
        if event.type == VkBotEventType.MESSAGE_NEW:
            from_user_message = UserTextInputMessage(date=event.message.date,
                                                     from_id=event.message.from_id,
                                                     text=event.message.text,
                                                     )

            log.info(f'New event : {from_user_message}')
            self.massage_processor.process(message=from_user_message)

        elif event.type == VkBotEventType.MESSAGE_REPLY and event.object.from_id == int(self.group_id) * -1:

            print(f'Ответ на сообщение прользователя от меня доставлено')
        elif event.type == VkBotEventType.MESSAGE_TYPING_STATE:
            print('Пользрватель печатает')

        else:
            log.info(f'Получили сообщение с типом {event.type} незнаю что делать')

    def run(self) -> None:
        """Основной цикл ожидания сообщений"""
        log.info('I running')
        print('Start .....')
        for event in self.vk_poller.listen():
            try:
                self.on_event(event)
            except Exception as err:
                log.error(f'Ошибка : {err.args}')
                print(f'error {err.args}')


def main() -> None:
    chat = Bot()
    print(chat)
    chat.run()


if __name__ == '__main__':
    main()
    print('Exit')
