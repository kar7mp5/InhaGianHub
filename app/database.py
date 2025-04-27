import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection settings from environment variables
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "inha_facility")

# SQLAlchemy Database URL
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# SQLAlchemy engine and session
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize database tables if they do not exist.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS facilities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                facility_id INT,
                date VARCHAR(50),
                place VARCHAR(100),
                department VARCHAR(100),
                event VARCHAR(200),
                approval VARCHAR(20),
                print_link TEXT,
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS popup_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reservation_id INT,
                `key` VARCHAR(100),
                `value` TEXT,
                FOREIGN KEY (reservation_id) REFERENCES reservations(id)
            );
        """))
