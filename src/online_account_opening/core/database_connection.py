import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database_config import DatabaseConfig
from .logger_module import LoggerManager

from sqlalchemy.orm import declarative_base
Base = declarative_base()

class DatabaseConnection:
    def __init__(self):
        self.logger = LoggerManager(log_name='DatabaseConnection', log_file='db.log')
        self.connection = None

    def connect(self, host=None, db=None, account=None, passwd=None,
                ssl_ca=None, ssl_cert=None, ssl_key=None, port=None):
        try:
            self.connection = pymysql.connect(
                host=host,
                user=account,
                password=passwd,
                db=db,
                port=port,
                ssl={
                    'ca': ssl_ca,
                    'cert': ssl_cert,
                    'key': ssl_key
                }
            )
            self.logger.log("資料庫連接成功", level="info")
        except Exception as e:
            self.logger.log(f"資料庫連接失敗: {e}", level="error")

def get_engine():
    db_uri = (
        f"mysql+pymysql://{DatabaseConfig.USER}:{DatabaseConfig.PASSWORD}@"
        f"{DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.DATABASE}"
        f"?ssl_ca={DatabaseConfig.ssl_ca}&ssl_cert={DatabaseConfig.ssl_cert}&ssl_key={DatabaseConfig.ssl_key}&ssl_verify_cert=false"
    )
    return create_engine(db_uri, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

