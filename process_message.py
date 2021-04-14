# use  Python ver 3.7.3
import re
import collections
import datetime
import copy

import calendar
from io import BytesIO
from typing import Text, List, Dict, Tuple, Optional

import bot_config
from log_settings import log_config
import logging.config

from model import RegisterInfo, UserInfo, psql_run_transaction, prepare_db
from PIL import Image, ImageDraw, ImageFont, ImageColor

logging.config.dictConfig(log_config)
log = logging.getLogger('bot')

DATE_FORMAT_POINT = '%d.%m.%Y'
DATE_FORMAT_HEY = '%d/%m/%Y'


def _create_date(text: Text) -> Tuple[datetime.datetime, Text]:
    """
    Преобразует  дату из текста в  datetime
    :param text: дата в тексте по формату - через . или /

    :rtype: дату в формате datetime, форматную строку
    """
    if text[2] == '.':
        format_string = DATE_FORMAT_POINT
    else:
        format_string = DATE_FORMAT_HEY
    return datetime.datetime.strptime(text, format_string), format_string


def _get_date_every_day(day_period: int, start_date: Text) -> Text:
    """
    Даты вылета по алгоритму ежедневно начиная с start_date
    :param day_period: период в днях
    :param start_date: начальная дата
    :return: следующую подходящую дату
    """
    input_date, format_string = _create_date(text=start_date)
    delta = datetime.timedelta(days=day_period)
    while True:
        input_date = input_date + delta
        yield input_date.strftime(format_string)


def _get_date_every_week(day_in_week: int, start_date: Text) -> Text:
    """
    Даты вылета по алгоритму еженедельно начиная с start_date
    :param day_in_week: день недели расчета
    :param start_date: начальная дата
    :return: следующую подходящую дату
    """
    input_date, format_string = _create_date(text=start_date)
    current_day_in_week = input_date.isoweekday() - 1

    correct = datetime.timedelta(days=current_day_in_week)
    input_date -= correct
    if current_day_in_week < day_in_week:
        delta = datetime.timedelta(days=day_in_week)
        input_date += delta
        yield input_date.strftime(format_string)
    while True:
        delta = datetime.timedelta(days=7)
        input_date = input_date + delta
        yield input_date.strftime(format_string)


def _get_date_every_month(day_in_month: int, start_date: Text) -> Text:
    """
    Даты вылета по алгоритму ежемесячно начиная с start_date
    :param day_in_month: день недели расчета
    :param start_date: начальная дата
    :return: следующую подходящую дату
    """
    input_date, format_string = _create_date(text=start_date)
    day_in_current_month = calendar.monthrange(year=input_date.year, month=input_date.month)[1]
    if input_date.day + 1 < day_in_month < day_in_current_month:
        delta = datetime.timedelta(days=day_in_month - input_date.day)
        input_date += delta
        yield input_date.strftime(format_string)
    while True:
        next_month = None
        next_year = None
        while True:
            if next_month:
                next_year, next_month = calendar.nextmonth(year=next_year, month=next_month)
            else:
                next_year, next_month = calendar.nextmonth(year=input_date.year, month=input_date.month)
            try:
                input_date = datetime.datetime(year=next_year, month=next_month, day=day_in_month)
                break
            except ValueError:
                continue
        yield input_date.strftime(format_string)


class AirLine:
    """Рейс"""

    def __init__(self, name, from_city, to_city, flight_time, regularity):
        """
        Создание
        :param name: Номер рейса
        :param from_city: Откуда летим
        :param to_city: Куда летим
        :param flight_time: Время вылета
        :param regularity: переодичность полетов
        """
        self.name = name
        self.from_city = from_city
        self.to_city = to_city
        self.flight_time = flight_time
        self.regularity = regularity
        self.date_generator = None
        self.date = ''

    def __repr__(self) -> Text:
        return f'{self.__class__.__name__}()'

    def __str__(self) -> Text:
        return f'Рейс {self.name} из {self.from_city} ' \
               f'в город {self.to_city} вылет в {self.flight_time} летает {self.regularity}'


class Distributor(collections.UserList):
    """класс распростронителя билетов
    содержит расписание рейсов
    """
    COUNT_DATE_FOR_LINE = 2

    def __repr__(self) -> Text:
        return f'{self.__class__.__name__}() with {len(self.data)} items'

    def get_destinations_from(self) -> List:
        """
        Откуда можно долететь
        :return: список городов лтправки рейсов
        """

        all_towns = {item.from_city for item in self.data}

        return list(all_towns)

    def get_destinations_to(self, from_cite: Text) -> List:
        """
        Куда можно долететь
        :param from_cite:город отправления
        :return: список городов с назначением рейсов из
        """
        return list({item.to_city for item in self.data if item.from_city == from_cite})

    def get_schedules(self, destination_from: Text, destination_to: Text, estimated_date: Text) -> List:
        """
        вернет расписание рейсов с датами вылета
        :param destination_to: куда летим
        :param destination_from: откуда летим
        :param estimated_date: предполагаемая дата
        :return: список рейсов до города
        """
        flight_to = []
        for flight in self.data:

            if flight.to_city == destination_to and flight.from_city == destination_from:
                frequency, num_in_period = flight.regularity.split()
                num_in_period = int(num_in_period)
                if frequency == 'ежедневно':
                    date_generator = _get_date_every_day(day_period=num_in_period, start_date=estimated_date)
                elif frequency == 'еженедельно':
                    date_generator = _get_date_every_week(day_in_week=num_in_period, start_date=estimated_date)
                elif frequency == 'ежемесячно':
                    date_generator = _get_date_every_month(day_in_month=num_in_period, start_date=estimated_date)
                else:
                    raise ValueError('Bad bot config')
                for _ in range(self.COUNT_DATE_FOR_LINE):
                    current_flight = copy.deepcopy(flight)
                    next_date = next(date_generator)
                    current_flight.date = next_date
                    flight_to.append(current_flight)
        return flight_to


class UserTextInputMessage:
    """Текстовое сообщение от пользователя"""
    TIME_FORMAT: Text = r'%H:%M %d.%m.%g'

    def __init__(self, date: float, from_id: int, text: Text):
        self.date: float = date  # дата сообщения
        self.from_id: int = from_id  # id пользователя от кого пришло сообщение
        self.origin_text: Text = text  # текст сообщения

    @property
    def words(self) -> List:
        """Слова в сообщении"""
        return self.origin_text.lower().split()

    @property
    def visible_time(self) -> Text:
        """Вернет дату сообщения преобразованную по формату UserTextInputMessage.time_format """
        user_datetime = datetime.datetime.utcfromtimestamp(self.date)
        return user_datetime.strftime(UserTextInputMessage.TIME_FORMAT)

    def __repr__(self):
        return f'{self.__class__.__name__}()'

    def __str__(self) -> Text:
        return f'В {self.visible_time} Получено сообщение от пользователя {self.from_id} : {self.origin_text}'


class User:
    """Пользователь в котексте общения с ботом"""

    def __init__(self, user_id: int):
        """
        Создание
        :param user_id: VK id пользователя
        """
        self.user_id: int = user_id
        # Призкак подтверждения (на предыдущем шаге)
        self.flag_confirmation = False
        # текущий сценарий
        self.scenario_name: Text = ''
        # имя шага в сценарии
        self.step_name: Text = ''
        # ник пользователя
        self.nick: Text = f'Незнакомец{self.user_id}'
        # ФИО в заказе
        self.fio: Text = ''
        # мыло
        self.email: Text = ''
        # дата вылета
        self.desired_date: Text = ''
        # откуда
        self.town_from: Text = ''
        # куда
        self.town_to: Text = ''
        # номер рейса
        self.flight_number: Text = ''
        # список авиарейсов для выбранных городов
        self.flight_lines = []
        # кол-во мест в заказе
        self.seats_number = 0
        #  комментарий
        self.comment = ''
        # номер телефона
        self.phone = ''
        self.user_db = UserInfo()
        # self.save_user_to_db()

    def __repr__(self) -> Text:
        return f'{self.__class__.__name__}()'

    def __str__(self):
        ret = f'{self.scenario_name} ' \
              f'{self.step_name} ' \
              f'{self.nick} ' \
              f'{self.fio} ' \
              f'{self.email} ' \
              f'{self.desired_date} ' \
              f'{self.town_from} ' \
              f'{self.town_to} ' \
              f'{self.flight_number} ' \
              f'{self.seats_number} ' \
              f'{self.phone} ' \
              f'{self.comment} '
        return ret

    @property
    def in_scenario(self) -> Text:
        return self.scenario_name

    @property
    def is_confirmation(self) -> bool:
        return self.flag_confirmation

    @property
    def context(self) -> Dict:
        user_context = {'nick': self.nick,
                        'user_id': self.user_id,
                        'fio': self.fio,
                        'desired_date': self.desired_date,
                        'email': self.email,
                        'town_from': self.town_from,
                        'town_to': self.town_to,
                        'flight_number': self.flight_number,
                        'seats_number': self.seats_number,
                        'comment': self.comment,
                        'phone': self.phone,
                        'scenario_name': self.scenario_name,
                        'step_name': self.step_name,

                        }
        return user_context

    @psql_run_transaction
    def save_user_to_db(self):
        self.user_db.in_step = self.step_name
        self.user_db.vk_user_id = self.user_id
        self.user_db.in_scenario = self.scenario_name
        self.user_db.user_nick = self.nick
        self.user_db.register_from_city = self.town_from
        self.user_db.register_to_city = self.town_to
        self.user_db.register_email = self.email
        self.user_db.register_comment = self.comment
        self.user_db.register_fio = self.fio
        self.user_db.register_flight_number = self.flight_number
        self.user_db.register_flay_date = self.desired_date
        self.user_db.register_telephone = self.phone
        self.user_db.register_email = self.email
        self.user_db.flag_confirmation = self.flag_confirmation
        self.user_db.save()

    def clear(self):
        """Отчистить данные заказа"""
        fields = ['fio', 'desired_date', 'email', 'flight_number', 'town_from', 'town_to', 'scenario_name',
                  'step_name', 'phone', 'comment']
        for field in fields:
            setattr(self, field, '')
        self.flag_confirmation = False
        self.seats_number = 0
        self.flight_lines.clear()
        self.save_user_to_db()


class MessageProcess:
    """Класс Обработчик сообщений
    Отвечает за обработку сообщений от пользователя
    Содержит  перечень пользователей сессиии
    """
    RE_NICK = re.compile(r'^[\w\s-]{1,10}$')
    RE_NAME = re.compile(r'^[\w\s\.]{1,30}$')
    RE_EMAIL = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
    RE_DATE = re.compile(r"^(0[1-9]|1[1-9]|2[0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](20\d\d)|(\d\d)$")
    RE_PHONE = re.compile(r"(\s*)?(\+)?([- _():=+]?\d[- _():=+]?){10,14}(\s*)?")
    RESULT_FILE = 'bot_result.txt'

    def __init__(self, bot):
        """
        Создание
        :param bot: Бот - родитель
        """
        self.bot = bot
        # интенты для бота
        self.user_intents: List = bot_config.INTENTS
        # сченарии для бота
        self.user_scenario: Dict = bot_config.SCENARIO
        # пользователи бота
        self.users: Dict[int, User] = {}
        # обработчик заказов
        self.dispatcher = Distributor()
        # список авиарейсов
        air_to_load = [AirLine(**i) for i in bot_config.AIRLINES]
        self.dispatcher.extend(air_to_load)
        prepare_db()
        self.restore_users()

    def __repr__(self) -> Text:
        return f'{self.__class__.__name__}() with {len(self.users)} users'

    @staticmethod
    def _create_image(user: User):
        font_size = bot_config.IMAGE_TEMPLATE['font_size']
        image_to_attach = Image.open(bot_config.IMAGE_TEMPLATE['picture_file'])
        font = ImageFont.truetype(bot_config.IMAGE_TEMPLATE['font_file'], font_size)
        draw = ImageDraw.Draw(image_to_attach)
        color = ImageColor.colormap['black']
        draw.text(bot_config.IMAGE_TEMPLATE['fio_offset'], user.fio, fill=color, font=font)
        draw.text(bot_config.IMAGE_TEMPLATE['from_offset'], user.town_from, fill=color, font=font)
        draw.text(bot_config.IMAGE_TEMPLATE['to_offset'], user.town_to, fill=color, font=font)
        draw.text(bot_config.IMAGE_TEMPLATE['date_offset'], user.desired_date, fill=color, font=font)
        draw.text(bot_config.IMAGE_TEMPLATE['name_offset'], user.flight_number, fill=color, font=font)
        temp_file = BytesIO()
        image_to_attach.save(temp_file, 'png')
        temp_file.seek(0)

        return temp_file

    @psql_run_transaction
    def restore_users(self):
        users = UserInfo.select()
        for user in users:
            from_db = User(user.vk_user_id)
            from_db.nick = user.user_nick
            from_db.flag_confirmation = user.flag_confirmation
            from_db.scenario_name = user.in_scenario
            from_db.step_name = user.in_step
            from_db.fio = user.register_fio
            from_db.email = user.register_email
            from_db.desired_date = user.register_flay_date
            from_db.town_from = user.register_from_city
            from_db.town_to = user.register_to_city
            from_db.seats_number = user.register_numbers_of_seats
            from_db.comment = user.register_comment
            from_db.phone = user.register_telephone
            from_db.user_db = user

            self.users[user.vk_user_id] = from_db

        pass

    @staticmethod
    def _get_match(text: Text, what: List) -> Tuple[bool, Optional[Text]]:
        """
        вернет набольшее совпадение из списка возможных
        (True,совпавщий элемент списка)
        (False,None) если больше 1 или нету
        """
        what_test = [town.lower() for town in what]
        position = 0
        test_str = text.lower()
        while not (position + len(text) == 0):
            if position:
                test_str = text[:position]
            test_re = [re.match(test_str, town) for town in what_test]
            test_full = [item for item in test_re if item]
            if not test_full:
                position -= 1
                continue
            if len(test_full) > 1:
                return False, None
            elif len(test_full) == 1:
                for index in range(0, len(test_re)):
                    if test_re[index]:
                        return True, what[index]
        return False, None

    def show_schedule(self, user: User) -> Text:
        """Вывести расписание авиарейсов"""
        all_data = [str(line) for line in self.dispatcher]
        all_data[0] = '<br>' + all_data[0]

        return '<br>'.join(all_data)

    def send_message(self, message: Text, to_whom: int) -> None:
        """
        Отправить сообщение пользователю VK
        :param message: текст сообщения
        :param to_whom: кому id пользователя VK
        :return:
        """
        user = self.users[to_whom]
        to_vk = f'{user.nick} ! : {message}'
        self.bot.send_message(message=to_vk, to_whom=to_whom)

    def send_image(self, image, to_whom: int):
        self.bot.send_image(image=image, to_whom=to_whom)

    @psql_run_transaction
    def save_register_to_bd(self, user: User):
        register = RegisterInfo()
        register.register_date = datetime.datetime.today()
        register.vk_user_id = user.user_id
        register.from_city = user.town_from
        register.to_city = user.town_to
        register.fio = user.fio
        register.numbers_of_seats = user.seats_number
        register.telephone = user.phone
        register.comment = user.comment
        register.flay_date = user.desired_date
        register.flight_number = user.flight_number
        register.email = user.email
        register.save()

    def ticket_scenario_finally(self, user: User):
        """
        Заваршаем сценарий ticket
        :param user: пользователь
        """
        log.info(f'User {user.user_id}  final scenario ticket ')
        context = user.context

        print('-' * 30)
        print(context)
        print('-' * 30)
        with open(self.RESULT_FILE, 'at', encoding='utf-8') as result_out:
            result_out.write(f'Заказ от {user.user_id} отзывается на {user.nick}\n')
            result_out.write(f'Дата регистрации {datetime.datetime.today().strftime(DATE_FORMAT_POINT)}')
            result_out.write('-' * 40)
            result_out.write('\n')
            for key, value in context.items():
                result_out.write(f'{key} : {value}\n')
            result_out.write('-' * 40)
            result_out.write('\n')
        self.save_register_to_bd(user)
        attach_image = self._create_image(user)
        self.send_image(image=attach_image, to_whom=user.user_id)
        self.clear_user_data(user)

    def get_user(self, message: UserTextInputMessage) -> User:
        """
        Вернет пользователя по id из сообщения  если новый - создаст его
        :param message:
        :return: пользователь
        """
        if message.from_id in self.users:
            current_user: User = self.users.get(message.from_id)
        else:
            current_user: User = User(user_id=message.from_id)
            self.users[message.from_id] = current_user
            current_user.save_user_to_db()
        return current_user

    def process(self, message: UserTextInputMessage):
        """
        Обработка входящего сообщения
        :param message: сообщение
        :return: True - успешная обработка False - сообщение не обработанно
        """
        current_user: User = self.get_user(message)
        if str.startswith(message.origin_text, '/'):
            self.process_message(current_user, message=message)
            return True
        if current_user.in_scenario:
            message_to_vk = self.process_scenario(current_user, message)
            self.send_message(message_to_vk, to_whom=current_user.user_id)
            return True
        else:
            return self.process_message(current_user, message)

    def process_scenario(self, user: User, message: UserTextInputMessage) -> Text:
        """
        Обработка сценария
        :param user: пользователь
        :param message: сообщение
        :return: текст для пользователя по результатам текущего шага
        """
        steps = self.user_scenario[user.scenario_name]['steps']
        handler = getattr(self, steps[user.step_name]['handler'])
        if handler:
            if handler(user, message.origin_text):
                next_step = steps[user.step_name]['next_step']
                user.step_name = next_step
                user.save_user_to_db()
                if steps[next_step]['next_step']:
                    user.step_name = next_step
                    user.save_user_to_db()
                    message_to_vk = self.get_text_for_step(user)
                else:
                    message_to_vk = steps[next_step]['final_text'].format(**user.context)
                    if steps[next_step]['final_func']:
                        final_func = getattr(self, steps[next_step]['final_func'])
                        if final_func:
                            final_func(user)
                        else:
                            raise ValueError('Bad config ')
                    self.cancel_scenario(user)
            else:
                answer_text = steps[user.step_name]['failure_text'].format(**user.context)
                answer_func_text = ''
                answer_func = steps[user.step_name]['failure_text_func']
                if answer_func:
                    handler = getattr(self, answer_func)
                    if handler:
                        answer_func_text = handler(user)
                message_to_vk = f'{answer_text}\n {answer_func_text}'
        else:
            raise ValueError('Bad config ')
        return message_to_vk

    def get_text_for_step(self, user: User) -> Text:
        """
        Вернет текст при переходе на текущий шаг
        :param user: пользователь
        :return:
        """
        steps = self.user_scenario[user.scenario_name]['steps']
        text = steps[user.step_name]['text'].format(**user.context)
        func_sed = ''
        text_func = steps[user.step_name]['text_func']
        if text_func:
            handler = getattr(self, text_func)
            if handler:
                func_sed = handler(user)
            else:
                raise ValueError('Bad config')
        if func_sed:
            message_to_vk = f'{func_sed}\n {text}'
        else:
            message_to_vk = text
        return message_to_vk

    def start_scenario(self, user: User, scenario: Text) -> Text:
        """
        Стартуем сценарий для пользрвателя
        :param user: пользователь
        :param scenario:
        :return:
        """
        user.scenario_name = scenario
        log.info(f'User {user.user_id} start scenario {scenario}')
        user.step_name = self.user_scenario[scenario]['first_step']
        message_to_vk = self.get_text_for_step(user)
        user.save_user_to_db()
        return message_to_vk

    def process_message(self, user: User, message: UserTextInputMessage):
        """Обработка пришедшего сообщения"""
        if self.process_user(user, message):
            return

        self.send_message(message=bot_config.DO_NOT_KNOWN, to_whom=message.from_id)

    def process_user(self, user: User, message: UserTextInputMessage) -> bool:
        """
        Обработка интентов
        :param user: пользователь
        :param message: сообщение
        :return: успех/неудача
        """
        for intent in self.user_intents:
            if any([word in intent['tokens'] for word in message.words]):
                log.info(f'User {user.user_id} enter  {intent["name"]} intent')
                answer_text = intent['answer']
                if answer_text:
                    answer_text = answer_text.format(**user.context)
                    answer_func = ''
                    handler = intent['answer_func']
                    if handler:
                        answer_func = getattr(self, handler)
                        if answer_func:
                            answer_func = answer_func(user)
                    message_to_vk = f'{answer_text}{answer_func}'
                    self.send_message(message_to_vk, message.from_id)
                    break
                elif intent['scenario']:
                    scenario = intent['scenario']
                    message_to_vk = self.start_scenario(user, scenario)
                    self.send_message(message=message_to_vk, to_whom=user.user_id)
                    break
                else:
                    raise ValueError('Bad config')

        else:
            return False
        return True

    @staticmethod
    def cancel_scenario(user: User):
        """
        Прекратить сценарий (полученные данные сохраняются)
        :param user: пользователь
        :return:
        """
        log.info(f'User {user.user_id} stop scenario {user.scenario_name}')
        user.scenario_name = ''
        user.step_name = ''
        user.flag_confirmation = False
        user.save_user_to_db()

    def handler_nick(self, user: User, text: Text) -> bool:
        """
        Проверить/сохранить nick пользователя
        :param user: пользователь
        :param text: текст с новым ником
        :return: подходит/не подходит
        """
        match = re.match(self.RE_NICK, text)
        if not match:
            return False
        log.info(f'User {user.user_id} set nick name to {text}')
        user.nick = text
        user.save_user_to_db()
        return True

    def handler_phone(self, user: User, text: Text) -> bool:
        """
        проверка/сохранение телефона
        :param user: пользователь
        :param text: текст с телефоном
        :return: есть телефон / нету телефона
        """
        for word in text.split():
            match = re.match(self.RE_PHONE, word)
            if match:
                log.info(f'User {user.user_id} set phone to {match.string}')
                user.phone = match.string
                user.save_user_to_db()
                return True
        return False

    @staticmethod
    def handler_count(user: User, text: Text) -> bool:
        """
        Проверка/сохранение количества мест
        :param user: пользователь
        :param text: текст с цифрой количества (1-5)
        :return:
        """
        if text.isdigit():
            number = int(text)
            if 0 < number <= 5:
                log.info(f'User {user.user_id} set seats_number to {number}')
                user.seats_number = number
                user.save_user_to_db()
                return True
        return False

    @staticmethod
    def handler_comment(user: User, text: Text) -> bool:
        """Проверить/сохранить коментарий"""
        log.info(f'User {user.user_id} set comment to {text}')
        user.comment = text
        user.save_user_to_db()
        return True

    def handler_name(self, user: User, text: Text) -> bool:
        """
        Проверить/сохранить ФИО
        :param user: пользрватель
        :param text: текст с ФИО
        :return: подходит/не подходит
        """
        match = re.match(self.RE_NAME, text)
        if match:
            log.info(f'User {user.user_id} set fio to {text}')
            user.fio = text
            user.save_user_to_db()
            return True
        else:
            return False

    def handler_email(self, user: User, email_text: Text) -> bool:
        """
        Проверка/сохранение email
        :param user: пользователь
        :param email_text: емаил
        :return: подходит/не подходит
        """
        matches = re.findall(self.RE_EMAIL, email_text)
        if len(matches) > 0:
            log.info(f'User {user.user_id} set email to {email_text}')
            user.email = matches[0]
            user.save_user_to_db()
            return True
        else:
            return False

    def handler_date(self, user: User, text: Text) -> bool:
        """
        Проверка/сохранение даты
        :param user: пользователь
        :param text: текст с датой
        :return: успех/неудача
        """
        test_text = text.strip()
        match = re.fullmatch(self.RE_DATE, text)
        if match is not None:
            if text[2] == '.':
                format_string = DATE_FORMAT_POINT
            else:
                format_string = DATE_FORMAT_HEY
            try:
                input_date = datetime.datetime.strptime(test_text, format_string)
            except ValueError:
                return False
            to_day = datetime.datetime.today()
            if input_date > to_day:
                log.info(f'User {user.user_id} set desired_date to {text}')
                user.desired_date = text
                user.save_user_to_db()
                return True
        return False

    def get_town_from(self, user: User, ) -> Text:
        """
        Вернет города вылета
        :param user: пользователь (для едентичности вызовов)
        :return: города вылета
        """
        towns = self.dispatcher.get_destinations_from()
        return ','.join(towns)

    def get_town_to(self, user: User, ) -> Text:
        """
        Вернет города назначения
        :param user: пользователь
        :return: куда можно полететь из текущего места отправки
        """
        towns = self.dispatcher.get_destinations_to(from_cite=user.town_from)
        return ','.join(towns)

    def handler_town_from(self, user: User, text: Text) -> bool:
        """добавить город отправления"""
        towns = self.dispatcher.get_destinations_from()
        flag, town = self._get_match(text, what=towns)
        if flag:
            log.info(f'User {user.user_id} set town_from to {town}')
            user.town_from = town
            user.save_user_to_db()
            return True
        else:
            return False

    @staticmethod
    def show_ticket_info(user: User) -> Text:
        """показать инфу по заказу"""
        return f'Заказ на рейс {user.flight_number} вылетающий ' \
               f'{user.desired_date} из {user.town_from} в {user.town_to} в колличестае {user.seats_number}' \
               f' мест коментарий {user.comment}'

    def show_available_flight(self, user: User) -> Text:
        """Показать дотупные рейсы"""
        lines = []

        user.flight_lines = self.dispatcher.get_schedules(destination_from=user.town_from, destination_to=user.town_to,
                                                          estimated_date=user.desired_date)
        for index, flight in enumerate(user.flight_lines, start=1):
            line_description = f'<br>{index} : {flight.date} Рейс {flight.name} из {flight.from_city} ' \
                               f'в {flight.to_city} время вылета {flight.flight_time}'
            lines.append(line_description)
        return '<br>'.join(lines)

    def handler_town_to(self, user: User, text: Text) -> bool:
        """добавить город назначения"""
        towns = self.dispatcher.get_destinations_to(from_cite=user.town_from)
        flag, town = self._get_match(text, what=towns)
        if flag:
            log.info(f'User {user.user_id} set town_to to {town}')
            user.town_to = town
            user.save_user_to_db()
            return True
        else:
            return False

    @staticmethod
    def handler_confirmation(user: User, text: Text) -> bool:
        """
        Сохранить результат подтверждения для дальгейшего анализа
        :param user: пользователь
        :param text: текст должен быть Да/Нет или Yes/No
        :return: ответ был Да/Нет
        """
        text = text.lower()
        if text.startswith('д') or text.startswith('y'):
            log.info(f'User {user.user_id} set flag_confirmation to True')
            user.flag_confirmation = True
            return True
        else:
            user.flag_confirmation = False
            user.save_user_to_db()
            return False

    @staticmethod
    def handler_flight_number(user: User, text: Text) -> bool:
        """
        проверить/сохранить номер рейса и дату вылета
        :param user: пользователь
        :param text: текст с выбранным номером (в пределах списка доступных авиарейсов)
        :return:
        """
        if text.isdigit():

            input_number = int(text) - 1
            if len(user.flight_lines) >= input_number >= 0:
                log.info(f'User {user.user_id} set flight_number to {user.flight_lines[input_number].name}')
                user.flight_number = user.flight_lines[input_number].name
                user.desired_date = user.flight_lines[input_number].date
                user.save_user_to_db()
                return True
        return False

    @staticmethod
    def clear_user_data(user: User) -> bool:
        """
        отчистить информацию по заказу
        :param user: пользователь
        :return:
        """
        if user.flag_confirmation:
            log.info(f'User {user.user_id} clear data for ticket')
            user.clear()
            return True
        return False

