from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from .database import get_db
from .schemas import (
    UserCreate, User, PredictionCreate, Prediction, 
    ChatCreate, Chat, ReportCreate, Report, HealthData
)
from .models import User as UserModel, Prediction as PredictionModel, \
                   Chat as ChatModel, Report as ReportModel
from .ml_model import predictor
from .gemini_client import gemini_client
from .pdf_processor import pdf_processor
from .report_generator import report_generator

app = FastAPI(title="AI Health Assistant", version="1.0.0")

@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = UserModel(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/predict/", response_model=Prediction)
async def predict_disease_risk(health_data: HealthData, db: Session = Depends(get_db)):
    try:
        # Predict risk using ML model
        risk_score = predictor.predict_diabetes_risk({
            **health_data.demographics,
            **health_data.vitals
        })
        
        # Generate explanation using Gemini
        prompt = f"""
        Based on the following health data, provide a clear explanation of diabetes risk:
        Demographics: {health_data.demographics}
        Lifestyle: {health_data.lifestyle}
        Symptoms: {health_data.symptoms}
        Vitals: {health_data.vitals}
        Calculated risk score: {risk_score:.2f}
        
        Please provide:
        1. A simple explanation of what this risk score means
        2. Key factors contributing to this risk
        3. 3-5 specific recommendations to reduce risk
        """
        
        gemini_response = gemini_client.call_gemini(prompt)
        
        # Parse response (this is simplified - you might want more structured parsing)
        lines = gemini_response.split('\n')
        explanation = lines[0] if lines else "Risk assessment completed"
        recommendations = '\n'.join(lines[1:]) if len(lines) > 1 else "Consult with healthcare provider"
        
        # Save prediction to database
        db_prediction = PredictionModel(
            user_id=health_data.user_id,
            disease="Diabetes",
            risk=risk_score,
            explanation=explanation,
            recommendations=recommendations
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return db_prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/chat/", response_model=Chat)
async def chat_with_assistant(chat_data: ChatCreate, db: Session = Depends(get_db)):
    try:
        # Forward query to Gemini
        prompt = f"""
        You are a helpful health assistant. Answer the following health-related question:
        {chat_data.query}
        
        Please provide:
        1. A clear, concise answer
        2. Any relevant health information
        3. When appropriate, suggest consulting a healthcare professional
        """
        
        response = gemini_client.call_gemini(prompt)
        
        # Save chat to database
        db_chat = ChatModel(
            user_id=chat_data.user_id,
            query=chat_data.query,
            response=response
        )
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        
        return db_chat
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/analyze-report/", response_model=Report)
async def analyze_medical_report(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Extract text from PDF
        extracted_text = await pdf_processor.extract_text_from_pdf(file)
        
        # Analyze with Gemini
        prompt = f"""
        Analyze this medical report and provide:
        1. Key findings and abnormalities
        2. Summary of important values
        3. General health advice based on the report
        
        Medical Report Content:
        {extracted_text[:4000]}  # Limit length
        """
        
        analysis = gemini_client.call_gemini(prompt)
        
        # Split into findings and advice (simplified)
        parts = analysis.split('\n\n', 1)
        findings = parts[0] if parts else "No specific findings"
        advice = parts[1] if len(parts) > 1 else "Consult with healthcare provider"
        
        # Save to database
        db_report = ReportModel(
            user_id=user_id,
            findings=findings,
            advice=advice
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return db_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report analysis error: {str(e)}")

@app.post("/generate-report/")
async def generate_comprehensive_report(
    user_id: int,
    prediction_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    report_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        # Get user data
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get prediction data
        prediction_data = None
        if prediction_id:
            prediction = db.query(PredictionModel).filter(
                PredictionModel.id == prediction_id,
                PredictionModel.user_id == user_id
            ).first()
            if prediction:
                prediction_data = {
                    'disease': prediction.disease,
                    'risk': prediction.risk,
                    'explanation': prediction.explanation,
                    'recommendations': prediction.recommendations
                }
        
        # Get chat summary
        chat_summary = ""
        if chat_id:
            chat = db.query(ChatModel).filter(
                ChatModel.id == chat_id,
                ChatModel.user_id == user_id
            ).first()
            if chat:
                chat_summary = f"Q: {chat.query}\nA: {chat.response}"
        
        # Get report findings
        report_findings = ""
        if report_id:
            report = db.query(ReportModel).filter(
                ReportModel.id == report_id,
                ReportModel.user_id == user_id
            ).first()
            if report:
                report_findings = f"Findings: {report.findings}\nAdvice: {report.advice}"
        
        # Generate PDF report
        user_data = {
            'name': user.name,
            'email': user.email,
            'age': 30  # This should come from user profile
        }
        
        filepath = report_generator.generate_health_report(
            user_data, prediction_data or {}, chat_summary, report_findings
        )
        
        return FileResponse(
            filepath, 
            filename="health_report.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

@app.get("/history/predictions/{user_id}", response_model=List[Prediction])
def get_prediction_history(user_id: int, db: Session = Depends(get_db)):
    predictions = db.query(PredictionModel).filter(
        PredictionModel.user_id == user_id
    ).order_by(PredictionModel.created_at.desc()).all()
    return predictions

@app.get("/history/chats/{user_id}", response_model=List[Chat])
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(ChatModel).filter(
        ChatModel.user_id == user_id
    ).order_by(ChatModel.created_at.desc()).all()
    return chats

@app.get("/history/reports/{user_id}", response_model=List[Report])
def get_report_history(user_id: int, db: Session = Depends(get_db)):
    reports = db.query(ReportModel).filter(
        ReportModel.user_id == user_id
    ).order_by(ReportModel.created_at.desc()).all()
    return reports

@app.get("/")
def read_root():
    return {"message": "AI Health Assistant API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
