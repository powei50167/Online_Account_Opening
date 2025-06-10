from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseConfig:
    HOST = os.getenv('DB_HOST')
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    DATABASE = os.getenv('DB_DATABASE')
    ssl_ca = os.getenv('DB_SSL_CA')
    ssl_cert = os.getenv('DB_SSL_CERT')
    ssl_key = os.getenv('DB_SSL_KEY')
    PORT = int(os.getenv('DB_PORT'))
