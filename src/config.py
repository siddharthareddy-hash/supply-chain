import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ["PG_HOST"],
    "port": os.environ["PG_PORT"],
    "dbname": os.environ["PG_DB"],
    "user": os.environ["PG_USER"],
    "password": os.environ["PG_PASSWORD"],
}

def get_connection_string() -> str:
    return (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
