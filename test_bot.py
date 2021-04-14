# use  Python ver 3.7.3
import datetime
from typing import Text
from unittest import TestCase, main
from unittest.mock import patch, ANY, Mock

from vk_api.bot_longpoll import VkBotMessageEvent

import bot
import process_message
from model import UserInfo, RegisterInfo, psql_db

AIRLINES = [
    {'from_city': 'Москва', 'to_city': 'Лондон', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Москва', 'to_city': 'Лондон', 'name': 'BA 0512', 'flight_time': '20:00',
     'regularity': 'ежедневно 2', },
    {'from_city': 'Москва', 'to_city': 'Лондон', 'name': 'SU 0520', 'flight_time': '02:00',
     'regularity': 'еженедельно 1', },
    {'from_city': 'Москва', 'to_city': 'Омск', 'name': 'SA 0820', 'flight_time': '02:00',
     'regularity': 'еженедельно 1', },
    {'from_city': 'Москва', 'to_city': 'Санкт-Петербург', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'еженедельно 4', },
    {'from_city': 'Москва', 'to_city': 'Ереван', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Ереван', 'to_city': 'Москва', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Омск', 'to_city': 'Москва', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Лондон', 'to_city': 'Москва', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Минск', 'to_city': 'Москва', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
]


def get_request(text: Text):
    """Вернет сообщение в формате VK"""
    ret = {'type': 'message_new',
           'object': {'message': {'date': 1597303687,
                                  'from_id': 609,
                                  'id': 40,
                                  'out': 0,
                                  'peer_id': 609728512,
                                  'text': text,
                                  'conversation_message_id': 39,
                                  'fwd_messages': [], 'important': False,
                                  'random_id': 0,
                                  'attachments': [],
                                  'is_hidden': False},
                      'client_info': {'button_actions': ['text',
                                                         'vkpay',
                                                         'open_app',
                                                         'location',
                                                         'open_link',
                                                         ],
                                      'keyboard': True,
                                      'inline_keyboard': True,
                                      'carousel': False,
                                      'lang_id': 0,
                                      },
                      },
           'group_id': 19779,
           'event_id': 'ba9cbf3a0f59f95060bce600e0bb78f5e633a68c',
           }
    vk_event = VkBotMessageEvent(raw=ret)
    return vk_event


class TestBot(TestCase):
    """Проверки класса Bot"""

    def setUp(self) -> None:
        with patch('bot.VkApi'):
            with patch('bot.VkBotLongPoll'):
                self.t_bot = bot.Bot()

    def test_func_run(self):
        """Проверка ф-ции run"""
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        listen_mock = Mock(return_value=events)
        self.t_bot.vk_poller.listen = listen_mock
        self.t_bot.on_event = Mock()
        self.t_bot.run()
        self.t_bot.on_event.assert_called()
        self.t_bot.on_event.assert_any_call(obj)
        assert self.t_bot.on_event.call_count == count

    def test_func_on_event_call(self):
        """Проверка ф-ции on_event"""
        self.t_bot.massage_processor.process = Mock()
        event = get_request(text='новое')
        self.t_bot.on_event(event)
        self.t_bot.massage_processor.process.assert_called()

    def test_func_send_message(self):
        """Проверка ф-ции send_message"""
        args_for_call_sens_message = {'message': ANY,
                                      'peer_id': 609,
                                      'random_id': ANY,
                                      }

        self.t_bot.api.messages.send = Mock()
        self.t_bot.send_message('test', to_whom=609)
        self.t_bot.api.messages.send.assert_called_once()
        self.t_bot.api.messages.send.assert_called_once_with(**args_for_call_sens_message)


class TestUserClass(TestCase):
    """Проверки класса User"""

    @staticmethod
    def get_date() -> Text:
        """Вернет текущую дату"""
        to_day = datetime.datetime.today()
        delta = datetime.timedelta(days=1)
        day = to_day + delta
        return day.strftime(process_message.DATE_FORMAT_POINT)

    def get_user_db(self):
        if psql_db.is_closed():
            psql_db.connect()
        user_db = UserInfo.get(UserInfo.vk_user_id == 609)
        return user_db

    def setUp(self) -> None:

        with patch('bot.VkApi'):
            with patch('bot.VkBotLongPoll'):
                with patch('bot.requests.get'):
                    self.t_bot = bot.Bot()
                    self.t_bot.send_image = Mock()

    def test_create_user(self):
        """
        Проверка создания нового пользоаптеля при преходе сообщения от него
        + И в Б/Д
        """
        event = get_request(text='новое')
        self.t_bot.on_event(event)
        self.assertEqual(self.t_bot.massage_processor.users[609].nick, 'Незнакомец609', )

        user_db = self.get_user_db()
        self.assertEqual(user_db.user_nick, 'Незнакомец609', )

    def tearDown(self) -> None:
        if psql_db.is_closed():
            psql_db.connect()
        user_db = UserInfo.get(UserInfo.vk_user_id == 609)
        user_db.delete_instance()
        register = RegisterInfo.get_or_none(RegisterInfo.vk_user_id == 609)
        if register is not None:
            register.delete_instance()

    def test_info_intent(self):
        """Проверка команды бота /info (информация о пользователе)"""
        call_args = {'message': 'Незнакомец609 ! : Пользователь 609 я вас называю Незнакомец609\n '
                                'Вы находитесь в сценарии  на шаге ', 'to_whom': 609}
        self.t_bot.send_message = Mock()
        self.t_bot.on_event(get_request(text='/info'))
        self.t_bot.send_message.assert_called_once_with(**call_args)

    def test_nick_scenario(self):
        """
        Сквозная проверка сценария смены псевдонима
        + проверка полей в Б/Д
        """
        event1 = get_request(text='/nick')
        event2 = get_request(text='sdf')
        self.t_bot.on_event(event1)
        self.assertEqual(self.t_bot.massage_processor.users[609].scenario_name, 'nick_name', )
        user_db = self.get_user_db()
        self.assertEqual(user_db.in_scenario, 'nick_name', )
        self.t_bot.on_event(event2)
        self.assertEqual(self.t_bot.massage_processor.users[609].nick, 'sdf', 'Должно быть "sdf"')
        user_db = self.get_user_db()
        self.assertEqual(user_db.user_nick, 'sdf', 'Должно быть "sdf"')

    def test_cancel_scenario(self):
        """Проверка отказа от текущего сценария"""
        event1 = get_request(text='test')
        event2 = get_request(text='/clear')
        event3 = get_request(text='Да')
        self.t_bot.on_event(event1)
        self.t_bot.massage_processor.users[609].town_to = 'town_to'
        self.t_bot.massage_processor.users[609].town_from = 'town_from'
        self.t_bot.on_event(event2)
        self.assertEqual(self.t_bot.massage_processor.users[609].scenario_name, 'clear', )
        self.t_bot.on_event(event3)
        self.assertFalse(self.t_bot.massage_processor.users[609].town_to, 'Должно быть пусто')
        self.assertFalse(self.t_bot.massage_processor.users[609].town_from, 'Должно быть пусто')

    def test_ticket_scenario(self):
        """Сквозная проверка сценария оформления заказа"""
        self.t_bot.on_event(get_request(text='test'))
        user = self.t_bot.massage_processor.users[609]
        self.t_bot.massage_processor._create_image = Mock()
        self.t_bot.on_event(get_request(text='/ticket'))
        self.assertEqual(user.scenario_name, 'ticket', 'Должно быть ticket')
        self.assertEqual(user.step_name, 'step_1', 'Должно быть step_1')
        self.t_bot.on_event(get_request(text='Апостол Царя Небестного 12345654'))
        self.assertEqual(user.step_name, 'step_1', 'Должно быть step_1')
        self.t_bot.on_event(get_request(text='Апостол Царя Небестного'))
        self.assertEqual(user.step_name, 'step_2', 'Должно быть step_2')
        self.t_bot.on_event(get_request(text='1@1'))
        self.assertEqual(user.step_name, 'step_2', 'Должно быть step_2')
        self.t_bot.on_event(get_request(text='tt@mail.ru'))
        self.assertEqual(user.step_name, 'step_3', 'Должно быть step_3')
        self.t_bot.on_event(get_request(text='М'))
        self.assertEqual(user.step_name, 'step_3', 'Должно быть step_3')
        self.t_bot.on_event(get_request(text='Мо'))
        self.assertEqual(user.step_name, 'step_4', 'Должно быть step_4')
        self.t_bot.on_event(get_request(text='Мо'))
        self.assertEqual(user.step_name, 'step_4', 'Должно быть step_4')
        self.t_bot.on_event(get_request(text='г'))
        self.assertEqual(user.step_name, 'step_4', 'Должно быть step_4')
        self.t_bot.on_event(get_request(text='л'))
        self.assertEqual(user.step_name, 'step_5', 'Должно быть step_5')
        date = self.get_date()
        self.t_bot.on_event(get_request(text=date))
        self.assertEqual(user.step_name, 'step_6', 'Должно быть step_6')
        self.t_bot.on_event(get_request(text='1'))
        self.assertEqual(user.step_name, 'step_7', 'Должно быть step_7')
        self.t_bot.on_event(get_request(text='10'))
        self.assertEqual(user.step_name, 'step_7', 'Должно быть step_7')
        self.t_bot.on_event(get_request(text='1'))
        self.assertEqual(user.step_name, 'step_8', 'Должно быть step_8')
        self.t_bot.on_event(get_request(text='просто коментарий'))
        self.assertEqual(user.step_name, 'step_9', 'Должно быть step_9')
        self.t_bot.on_event(get_request(text='просто'))
        self.assertEqual(user.step_name, 'step_9', 'Должно быть step_9')
        self.t_bot.on_event(get_request(text='д'))
        self.assertEqual(user.step_name, 'step_10', 'Должно быть step_10')
        self.t_bot.on_event(get_request(text='ененененен'))
        self.assertEqual(user.step_name, 'step_10', 'Должно быть step_10')
        self.t_bot.on_event(get_request(text='83953562222'))
        self.assertFalse(user.step_name, 'Должно быть пусто')


class TestDistributorCase(TestCase):
    """Проверка класса Distributor"""

    def setUp(self) -> None:
        with patch('bot.VkApi'):
            with patch('bot.VkBotLongPoll'):
                self.t_bot = bot.Bot()
        self.distributor = self.t_bot.massage_processor.dispatcher
        air_to_load = [process_message.AirLine(**i) for i in AIRLINES]
        self.distributor.extend(air_to_load)

    def test_load_schedules(self):
        """Проверка загрузки расписания"""
        self.distributor.clear()
        air_to_load = [process_message.AirLine(**i) for i in AIRLINES]
        self.distributor.extend(air_to_load)

        self.assertEqual(len(self.distributor), 10, 'Должно быть 10')

    def test_get_destination_from(self):
        """Проверка ф-ции взять города отправления"""
        all_lines = self.distributor.get_destinations_from()
        self.assertEqual(len(all_lines), 5, 'Должно быть 5')

    def test_get_destination_to(self):
        """Проверка ф-ции взять города назначения"""
        all_lines = self.distributor.get_destinations_to(from_cite='Москва')
        self.assertEqual(len(all_lines), 4, 'Должно быть 4')

    def test_get_schedules(self):
        """Проверка ф-ции взять расписание """
        all_lines = self.distributor.get_schedules(destination_from='Минск', destination_to='Москва',
                                                   estimated_date='01.01.2021')
        all_lines1 = self.distributor.get_schedules(destination_from='Москва', destination_to='Лондон',
                                                    estimated_date='01.01.2021')
        self.assertEqual(len(all_lines), 4, 'Должно быть 4')
        self.assertEqual(len(all_lines1), 12, 'Должно быть 12')


class TestMessageProcessCase(TestCase):
    """"""

    def setUp(self) -> None:
        with patch('bot.VkApi'):
            with patch('bot.VkBotLongPoll'):
                self.bot = bot.Bot()
        self.user = process_message.User(609)

    def tearDown(self) -> None:
        if psql_db.is_closed():
            psql_db.connect()
        user_db = UserInfo.get(UserInfo.vk_user_id == 609)
        user_db.delete_instance()
        register = RegisterInfo.get_or_none(RegisterInfo.vk_user_id == 609)
        if register is not None:
            register.delete_instance()

    def test_handler_name(self):
        """Проверка ф-ции handler_name """
        names_test = ['test', 'TEST', 'Просто Имя', 'Я Сам Такой Сякой', 'Просто Имя - Собачье',
                      'Просто Имя1212121212121212121212']
        tested_names = [self.bot.massage_processor.handler_name(self.user, text) for text in names_test]
        self.assertTrue(tested_names[0], 'Должен быть True')
        self.assertTrue(tested_names[1], 'Должен быть True')
        self.assertTrue(tested_names[2], 'Должен быть True')
        self.assertTrue(tested_names[3], 'Должен быть True')
        self.assertFalse(tested_names[4], 'Должен быть True')
        self.assertFalse(tested_names[5], 'Должен быть False')
        self.assertEqual(self.user.fio, 'Я Сам Такой Сякой', 'Должен быть "Я Сам Такой Сякой"')

    def test_handler_email(self):
        """Проверка ф-ции handler_email """
        names_test = ['a@r', 'test@com', 'test@mail.ru', 'test.mail.ru', 'test@yandex,ru',
                      'Просто Имя1212121212121212']
        tested_names = [self.bot.massage_processor.handler_email(self.user, text) for text in names_test]
        self.assertFalse(tested_names[0], 'Должен быть False')
        self.assertFalse(tested_names[1], 'Должен быть False')
        self.assertTrue(tested_names[2], 'Должен быть True')
        self.assertFalse(tested_names[3], 'Должен быть False')
        self.assertFalse(tested_names[4], 'Должен быть False')
        self.assertFalse(tested_names[5], 'Должен быть False')
        self.assertEqual(self.user.email, 'test@mail.ru', 'Должен быть False "test@mail.ru"')

    def test_handler_date(self):
        """Проверка ф-ции handler_date """
        names_test = ['01.02.01', '01.02.2021', '01.31.202', '54.01.2020', '01.01.1920',
                      'Просто 01.13.2020']

        tested_names = [self.bot.massage_processor.handler_date(self.user, text) for text in names_test]
        self.assertFalse(tested_names[0], 'Должен быть False')
        self.assertTrue(tested_names[1], 'Должен быть True')
        self.assertFalse(tested_names[2], 'Должен быть False')
        self.assertFalse(tested_names[3], 'Должен быть False')
        self.assertFalse(tested_names[4], 'Должен быть False')
        self.assertFalse(tested_names[5], 'Должен быть False')
        self.assertEqual(self.user.desired_date, '01.02.2021', 'Должен быть False "01.02.2021"')


class TestDateGenerationCase(TestCase):
    """Проверки генираторов дат вылета"""

    def test_every_day_algorithm(self):
        """Алгоритм - ежедневно (период 1 день)"""
        generator = process_message._get_date_every_day(1, '14.09.2020')
        generator1 = process_message._get_date_every_day(1, '14/09/2020')
        received_dates1 = []
        for _ in range(5):
            received_dates1.append(next(generator))
        received_dates2 = []
        for _ in range(5):
            received_dates2.append(next(generator1))
        self.assertEqual(received_dates1[-1], '19.09.2020')
        self.assertEqual(received_dates1[1], '16.09.2020')
        self.assertEqual(received_dates2[-1], '19/09/2020')
        self.assertEqual(received_dates2[1], '16/09/2020')

    def test_every_week_algorithm(self):
        """Алгоритм еженедельно (период по вторникам [2 день недели])"""
        generator = process_message._get_date_every_week(1, '14/09/2020')
        received_dates = []
        for _ in range(5):
            received_dates.append(next(generator))
        self.assertEqual(received_dates[-1], '13/10/2020')
        self.assertEqual(received_dates[0], '15/09/2020')

    def test_every_month_algorithm(self):
        """Алгоритм ежемесячно (14 числа)"""
        generator = process_message._get_date_every_month(14, '14/09/2020')
        received_dates = []

        for _ in range(5):
            received_dates.append(next(generator))
        self.assertEqual(received_dates[0][3:5], '10')
        self.assertEqual(received_dates[-1][3:5], '02')
        self.assertEqual(received_dates[-1][-4:], '2021')

    def test_every_month_algorithm2(self):
        """Алгоритм ежемесячно (31 числа)"""
        generator = process_message._get_date_every_month(31, '14/09/2020')
        received_dates = []
        for _ in range(5):
            received_dates.append(next(generator))
        self.assertEqual(received_dates[0][3:5], '10')
        self.assertEqual(received_dates[-1][3:5], '05')
        self.assertEqual(received_dates[-1][-4:], '2021')


if __name__ == '__main__':
    main()
