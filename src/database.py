from pony.orm import Database

db = Database()


def connect(login: str, password: str, host: str, port: int = 5432, database: str = "geomech"):
    global db
    db.bind(provider="postgres", user=login, password=password, host=host, database=database, port=port)
    db.generate_mapping(create_tables=False)
