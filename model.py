# use Python 3.7.3
from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase
import settings

psql_db = PostgresqlExtDatabase(settings.DBNAME,
                                user=settings.DBUSER,
                                password=settings.DBPASS,
                                host=settings.DBHOST,
                                port=settings.DBPORT, autoconnect=False)


class BaseModel(Model):
    class Meta:
        database = psql_db
        legacy_table_names = False


class UserInfo(BaseModel):
    """
    Таблица с информацией о пользователях
    vk_user_id   - идентификатор пользователя в VK
    in_scenario - в каком сценарии
    in_step - на каком шаге
    user_nick - псевдоним пользователя
    flag_confirmation - фоаг подтверждения
    register_from_city - город вылета
    register_to_city - город назначения
    register_flay_date - дата вылета
    register_numbers_of_seats - кол-во мест
    register_flight_number - нолмер рейса
    register_comment - коментарий
    register_telephone - телефон
    register_fio - фамилия
    register_email - мыло

    """
    vk_user_id = IntegerField(null=False,unique=True)
    in_scenario = CharField(null=True)
    in_step = CharField(null=True)
    user_nick = CharField(null=False)
    flag_confirmation = BooleanField(null=True)
    register_from_city = CharField(null=True)
    register_to_city = CharField(null=True)
    register_flay_date = CharField(null=True)
    register_numbers_of_seats = IntegerField(null=True)
    register_flight_number = CharField(null=True)
    register_comment = CharField(null=True)
    register_telephone = CharField(null=True)
    register_fio = CharField(null=True)
    register_email = CharField(null=True)


class RegisterInfo(BaseModel):
    """
    Данные о зарегистрированных билетах
    register_date - Дата регистркции билета
    vk_user_id -   ИД пользователя в VK
    from_city - город вылета
    to_city -   город назначения
    flay_date -  дата вылета
    numbers_of_seats - кол-во мест
    flight_number - номер рейса
    comment - коментарий
    telephone - телнфон
    fio - Фамилия
    email - мыло
    """
    register_date = DateTimeField(null=False)
    vk_user_id = IntegerField(null=False)
    from_city = CharField(null=False)
    to_city = CharField(null=False)
    flay_date = CharField(null=False)
    numbers_of_seats = IntegerField(null=False)
    flight_number = CharField(null=False)
    comment = CharField(null=False)
    telephone = CharField(null=False)
    fio = CharField(null=False)
    email = CharField(null=False)


def psql_run_transaction(func):
    """
    Транзакция в БД
    Используем как декоратор к функциям
    """

    def run_func(*args, **kwargs):
        if psql_db.is_closed():
            psql_db.connect()
        psql_db.begin()
        result_value = func(*args, **kwargs)
        psql_db.commit()
        psql_db.close()
        return result_value

    return run_func


@psql_run_transaction
def prepare_db():
    """Создание таблиц в базе"""
    models = [UserInfo, RegisterInfo]

    psql_db.create_tables(models)


def delete_data_db():
    """Отчистка таблиц"""
    psql_db.connect()
    psql_db.begin()
    RegisterInfo.delete().execute()
    psql_db.commit()
    psql_db.begin()
    UserInfo.delete().execute()
    psql_db.commit()
    psql_db.close()

