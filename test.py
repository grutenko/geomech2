import code  # Стандартный модуль для консоли

from pony.orm import Database, Required, db_session

# Создаем базу данных и модель
db = Database()


class User(db.Entity):
    name = Required(str)
    age = Required(int)


# Подключаем базу данных (для примера используем SQLite)
db.bind(provider="sqlite", filename="database.db", create_db=True)
db.generate_mapping(create_tables=True)


# Функция для запуска консоли с доступом к базе данных только для чтения
def start_readonly_console():
    # Функция для безопасной работы с базой данных (только чтение)
    @db_session
    def readonly_session():
        # Просто возвращаем результат чтения из базы
        users = User.select()
        for user in users:
            print(f"{user.name}, {user.age}")

    # Запрещаем выполнять изменения в базе данных:
    def no_commit(query):
        raise PermissionError("Запрещено выполнять изменения в базе данных!")

    # Открываем консоль и заменяем методы, связанные с записью, на пустые
    console_locals = {"User": User, "db_session": readonly_session, "query": no_commit}  # Перехватываем метод записи

    # Запускаем консоль Python с ограничениями
    banner = "Добро пожаловать в консоль с доступом только для чтения!"
    console = code.InteractiveConsole(console_locals)
    console.interact(banner=banner)


# Запуск консоли
start_readonly_console()
