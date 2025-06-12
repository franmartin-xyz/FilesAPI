from database import engine, Base
from models import FileUpload, Conversation

def init_db():
    print("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
