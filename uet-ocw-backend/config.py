import os

from dotenv import load_dotenv

load_dotenv()
DB_SSL_CA = os.getenv("DB_SSL_CA")

if DB_SSL_CA and not os.path.isabs(DB_SSL_CA):
    DB_SSL_CA = os.path.join(os.path.dirname(__file__), DB_SSL_CA)

class Config:
     SQLALCHEMY_ENGINE_OPTIONS = (
    {"connect_args": {"ssl": {"ca": DB_SSL_CA}}}
    if DB_SSL_CA
    else {}
)
    SECRET_KEY = os.getenv("SECRET_KEY")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-this-jwt-secret"

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST', '127.0.0.1')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME')}"
        f"?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
