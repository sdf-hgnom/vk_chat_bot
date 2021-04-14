# use  Python ver 3.7.3
AIRLINES = [
    {'from_city': 'Москва', 'to_city': 'Лондон', 'name': 'SU 0102', 'flight_time': '02:00',
     'regularity': 'ежедневно 1', },
    {'from_city': 'Москва', 'to_city': 'Лондон', 'name': 'BA 0512', 'flight_time': '20:00',
     'regularity': 'ежемесячно 22', },
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

INTENTS = [{'name': 'correct nick',  # Перейти в сценирий корректировки ника
            'tokens': ['nick', 'смен', '/nick', 'ник'],
            'scenario': 'nick_name',
            'answer': None,
            'answer_func': None,
            },
           {'name': 'clear',  # Перейти в сценирий отмены билета
            'tokens': ['/clear', 'отменить'],
            'scenario': 'clear',
            'answer': None,
            'answer_func': None,
            },
           {'name': 'tickets',  # Перейти в сценирий регистрации заказа
            'tokens': ['/ticket', '/билет'],
            'scenario': 'ticket',
            'answer': None,
            'answer_func': None,
            },
           {'name': 'show info',  # Показать  справку по пользователю
            'tokens': ['/info', 'мне'],
            'scenario': None,
            'answer': 'Пользователь {user_id} я вас называю {nick}\n '
                      'Вы находитесь в сценарии {scenario_name} на шаге {step_name}',
            'answer_func': None,
            },
           {'name': 'hello',  # Ответ на приветствие
            'tokens': ['hello', 'привет'],
            'scenario': None,
            'answer': 'Привет {nick} ! Я чат-бот \n готов к работе',
            'answer_func': None,
            },
           {'name': 'about',  # Краткая справка
            'tokens': ['что', 'what', '/about', 'чего', 'чем'],
            'scenario': None,
            'answer': 'Я создан для обработки заказов на билеты Обрабатываются несколько авиарейсов в разные города ',
            'answer_func': None,
            },
           {'name': 'show ticket info',  # Информация о введенных данных
            'tokens': ['/show'],
            'scenario': None,
            'answer': """ К этому времени вы ввели :
                         ФИО : {fio}
                         Дата вылета : {desired_date}
                         Email : {email}
                         Город отправления : {town_from}
                         Город назначения : {town_to}
                         Номер рейса : {flight_number}
                         Колличество мест : {seats_number}
                         Коментарий : {comment}
                         Телефон для связи : {phone}
            """,
            'answer_func': None,
            },

           {'name': 'full_help',  # Полная  справка  +
            'tokens': ['что', 'what', '/help', 'чего', 'чем'],
            'scenario': None,
            'answer': """Я создан для обработки заказов на билеты '
                      Обрабатываются несколько авиарейсов в разные города
                      Вы можете использовать следующие команды:
                      /about     - Коротко осебе
                      /help      - Справка по командам(этот текст)
                      /info      - Информация о пользователе
                      /nick      - Смена псевдонима
                      /clear     - Отмена текущего сценария
                      /ticket    - Переход в сценарий регистрации заказа
                      /show      - Что уже успели ввести в сценарии регистрации заказа 
                      /list      - Просмотр расписания рейсов
                      /town_from - Из каких городов осуществляем перелеты
                      """,
            'answer_func': None,
            },
           {'name': 'schedule',  # Вывод расписания всех рейсов +
            'tokens': ['рассписание', '/list', ],
            'scenario': None,
            'answer': 'Расписание всех рейсов : ',
            'answer_func': 'show_schedule',
            },
           {'name': 'town_from',  # Вывод городов отправления
            'tokens': ['/town_from', ],
            'scenario': None,
            'answer': 'Перечень городов - пунктов отправления : ',
            'answer_func': 'get_town_from',
            },

           ]

SCENARIO = {
    'nick_name': {
        'first_step': 'step_1',
        'steps': {
            'step_1': {
                'text': 'Введите Ваш псевдоним : ',
                'text_func': None,
                'failure_text': 'bad nick',
                'failure_text_func': None,
                'handler': 'handler_nick',
                'next_step': 'step_2',
            },
            'step_2': {
                'text': 'Ваш псевдоним  :{nick}',
                'text_func': None,
                'failure_text': None,
                'failure_text_func': None,
                'handler': None,
                'next_step': None,
                'final_func': None,
                'final_text': 'Ваш псевдоним  {nick}'
            },
        }},
    'ticket': {
        'first_step': 'step_1',
        'steps': {
            'step_1': {
                'text': 'Введите ФИО : ',
                'text_func': None,
                'failure_text': 'ФИО должна быть не более 30 символов\n Повторите ввод : ',
                'failure_text_func': None,
                'handler': 'handler_name',
                'next_step': 'step_2',
            },
            'step_2': {
                'text': 'Введите email : ',
                'text_func': None,
                'failure_text': 'Плохой адрес эл. посчты',
                'failure_text_func': None,
                'handler': 'handler_email',
                'next_step': 'step_3',
            },
            'step_3': {
                'text': 'Введите город отправления : ',
                'text_func': None,
                'failure_text': 'У нас оттуда не летают - Уточните город отправления',
                'failure_text_func': 'get_town_from',
                'handler': 'handler_town_from',
                'next_step': 'step_4',
            },
            'step_4': {
                'text': 'Введите город назначения : ',
                'text_func': None,
                'failure_text': 'У нас туда не летают - Уточните город назначения',
                'failure_text_func': 'get_town_to',
                'handler': 'handler_town_to',
                'next_step': 'step_5',
            },
            'step_5': {
                'text': 'Введите дату отправления : ',
                'text_func': None,
                'failure_text': 'Плохая дата, Уточните в формате dd.mm.20yy (должна быть поздже сегодня)',
                'failure_text_func': None,
                'handler': 'handler_date',
                'next_step': 'step_6',
            },
            'step_6': {
                'text': 'Выберите рейс :',
                'text_func': 'show_available_flight',
                'failure_text': 'Введите номер  выбранного рейса (1-...) : ',
                'failure_text_func': None,
                'handler': 'handler_flight_number',
                'next_step': 'step_7',
            },
            'step_7': {
                'text': 'Введите колличество мест (1-5) : ',
                'text_func': None,
                'failure_text': 'колличество мест должна быть цифра от 1 до 5',
                'failure_text_func': None,
                'handler': 'handler_count',
                'next_step': 'step_8',
            },
            'step_8': {
                'text': 'Введите коментарий : ',
                'text_func': None,
                'failure_text': 'Плохая дата, Уточните в формате dd-mm-20yy ',
                'failure_text_func': None,
                'handler': 'handler_comment',
                'next_step': 'step_9',
            },
            'step_9': {
                'text': 'Все верно ? : ',
                'text_func': 'show_ticket_info',
                'failure_text': 'Введите Да или Нет (Yes/No)',
                'failure_text_func': None,
                'handler': 'handler_confirmation',
                'next_step': 'step_10',
            },
            'step_10': {
                'text': 'Введите номер телефона : ',
                'text_func': None,
                'failure_text': 'Неверный номер. Введите по формату +710цифр номера',
                'failure_text_func': None,
                'handler': 'handler_phone',
                'next_step': 'step_11',
            },
            'step_11': {
                'text': 'Мы с Вами свяжемся',
                'text_func': None,
                'failure_text': None,
                'failure_text_func': None,
                'handler': None,
                'next_step': None,
                'final_func': 'ticket_scenario_finally',
                'final_text': 'Мы с Вами свяжемся по телефону {phone}'
            },
        }},
    'clear': {
        'first_step': 'step_1',
        'steps': {
            'step_1': {
                'text': 'Отчистить все введенные данные по билету (Да/Нет) ?',
                'text_func': None,
                'failure_text': 'Я жду от Вас Да или Нет',
                'failure_text_func': None,
                'handler': 'handler_confirmation',
                'next_step': 'step_2',
                'final_func': 'clear_user_data',
                'final_text': 'Данные по регистрации билета отменены'
            },
            'step_2': {
                'text': 'entered  nick name :{nick}',
                'text_func': None,
                'failure_text': None,
                'failure_text_func': None,
                'handler': None,
                'next_step': None,
                'final_func': 'clear_user_data',
                'final_text': 'Данные по регистрации билета отменены',
            },

        }},
}

IMAGE_TEMPLATE = {'picture_file': 'images/ticket_template.png',
                  'font_file': 'fonts/ofont.ru_Nyasha Sans.ttf',
                  'font_size': 14,
                  'fio_offset': (50, 121),
                  'from_offset': (50, 191),
                  'to_offset': (50, 256),
                  'date_offset': (290, 256),
                  'name_offset': (50, 326),

                  }

DO_NOT_KNOWN = 'Я Вас не понял - используйте /help для справки'
