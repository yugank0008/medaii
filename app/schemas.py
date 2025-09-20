from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re

class UserBase(BaseModel):
    name: str
    email: str

    @field_validator('email')
    def validate_email(cls, v):
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

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

