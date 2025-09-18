from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PredictionBase(BaseModel):
    disease: str
    risk: float
    explanation: str
    recommendations: str

class PredictionCreate(BaseModel):
    user_id: int
    demographics: dict
    lifestyle: dict
    symptoms: dict
    vitals: dict

class Prediction(PredictionBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    query: str
    response: str

class ChatCreate(BaseModel):
    user_id: int
    query: str

class Chat(ChatBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    findings: str
    advice: str

class ReportCreate(BaseModel):
    user_id: int

class Report(ReportBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class HealthData(BaseModel):
    user_id: int
    demographics: dict
    lifestyle: dict
    symptoms: dict
    vitals: dict
