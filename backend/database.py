from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import time
from urllib.parse import quote_plus

# Get database URL from environment variable or use MySQL as default
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@db:3306/filesapi")

def wait_for_db(engine, max_retries=5, delay=5):
    """Wait for the database to be available."""
    import sqlalchemy
    from sqlalchemy.exc import OperationalError
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            with engine.connect() as conn:
                print("✅ Database connection successful!")
                return True
        except OperationalError as e:
            retry_count += 1
            print(f"⌛ Waiting for database to be ready... (attempt {retry_count}/{max_retries})")
            if retry_count >= max_retries:
                print(f"❌ Max retries reached. Could not connect to database: {e}")
                raise
            time.sleep(delay)
    return False

# Create SQLAlchemy engine
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # For MySQL/PostgreSQL, we don't need check_same_thread
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Wait for database to be ready
wait_for_db(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session factory
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database
def init_db():
    """Initialize the database"""
    print("🔄 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise
