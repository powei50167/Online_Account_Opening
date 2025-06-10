from .database_connection import DatabaseConnection, engine, SessionLocal
from .database_config import DatabaseConfig

connect_db = DatabaseConnection()

try:
    connect_db.connect(
        host=DatabaseConfig.HOST,
        db=DatabaseConfig.DATABASE,
        account=DatabaseConfig.USER,
        passwd=DatabaseConfig.PASSWORD,
        ssl_ca=DatabaseConfig.ssl_ca,
        ssl_cert=DatabaseConfig.ssl_cert,
        ssl_key=DatabaseConfig.ssl_key,
        port=DatabaseConfig.PORT
    )
    print("Successfully connected to the database")
except Exception as e:
    print(f"Failed to connect to SQL database: {e}")
