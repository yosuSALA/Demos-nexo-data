from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Usamos SQLite localmente de acuerdo a nuestro Prompt 6
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
