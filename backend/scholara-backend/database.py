from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Change this to your PostgreSQL URL later: "postgresql://user:password@localhost/scholara"
SQLALCHEMY_DATABASE_URL = "sqlite:///./scholara.db"

# THIS IS THE VARIABLE IT IS LOOKING FOR:
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Only needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()