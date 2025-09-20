from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from urllib.parse import urlparse


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./health_data.db")


parsed_url = urlparse(DATABASE_URL)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
elif DATABASE_URL.startswith("postgresql"):
    
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    predictions = relationship("Prediction", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    reports = relationship("Report", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    disease = Column(String)
    risk = Column(Float)
    explanation = Column(String)
    recommendations = Column(String)
    input_data = Column(String)  # Store input data as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="predictions")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String)
    response = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chats")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    findings = Column(String)
    advice = Column(String)
    file_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reports")


try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ['User', 'Prediction', 'Chat', 'Report', 'get_db', 'Base']

