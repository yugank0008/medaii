from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
import os
import logging
import re

from .database import get_db, User, Prediction, Chat, Report  # Import models from database
from .schemas import (
    UserBase, UserCreate, User as UserSchema, 
    PredictionCreate, Prediction as PredictionSchema, 
    ChatCreate, Chat as ChatSchema, 
    ReportCreate, Report as ReportSchema, 
    HealthData
)
from .ml_model import predictor
from .gemini_client import gemini_client
from .pdf_processor import pdf_processor
from .report_generator import report_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Health Assistant API",
    description="AI-powered disease risk prediction and health assistance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Email validation function
def validate_email(email: str):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "AI Health Assistant API is running", "status": "healthy"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        model_status = "loaded" if predictor.model is not None else "not loaded"
        
        return {
            "status": "healthy",
            "database": "connected",
            "model": model_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@app.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Validate email
        validate_email(user.email)
        
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {db_user.email}")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.post("/predict/", response_model=PredictionSchema)
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
        
        # Parse response
        lines = gemini_response.split('\n')
        explanation = lines[0] if lines else "Risk assessment completed"
        recommendations = '\n'.join(lines[1:]) if len(lines) > 1 else "Consult with healthcare provider"
        
        # Save prediction to database
        db_prediction = Prediction(
            user_id=health_data.user_id,
            disease="Diabetes",
            risk=risk_score,
            explanation=explanation,
            recommendations=recommendations,
            input_data=json.dumps(health_data.dict())
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        logger.info(f"Prediction created for user {health_data.user_id}: risk {risk_score}")
        return db_prediction
        
    except Exception as e:
        db.rollback()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

@app.post("/chat/", response_model=ChatSchema)
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
        db_chat = Chat(
            user_id=chat_data.user_id,
            query=chat_data.query,
            response=response
        )
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        
        logger.info(f"Chat response generated for user {chat_data.user_id}")
        return db_chat
        
    except Exception as e:
        db.rollback()
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )

@app.post("/analyze-report/", response_model=ReportSchema)
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
        {extracted_text[:4000]}
        """
        
        analysis = gemini_client.call_gemini(prompt)
        
        # Split into findings and advice
        parts = analysis.split('\n\n', 1)
        findings = parts[0] if parts else "No specific findings"
        advice = parts[1] if len(parts) > 1 else "Consult with healthcare provider"
        
        # Save to database
        db_report = Report(
            user_id=user_id,
            findings=findings,
            advice=advice,
            file_name=file.filename
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"Report analyzed for user {user_id}: {file.filename}")
        return db_report
        
    except Exception as e:
        db.rollback()
        logger.error(f"Report analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report analysis error: {str(e)}"
        )

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
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get prediction data
        prediction_data = None
        if prediction_id:
            prediction = db.query(Prediction).filter(
                Prediction.id == prediction_id,
                Prediction.user_id == user_id
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
            chat = db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            if chat:
                chat_summary = f"Q: {chat.query}\nA: {chat.response}"
        
        # Get report findings
        report_findings = ""
        if report_id:
            report = db.query(Report).filter(
                Report.id == report_id,
                Report.user_id == user_id
            ).first()
            if report:
                report_findings = f"Findings: {report.findings}\nAdvice: {report.advice}"
        
        # Generate PDF report
        user_data = {
            'name': user.name,
            'email': user.email,
            'age': 30
        }
        
        filepath = report_generator.generate_health_report(
            user_data, prediction_data or {}, chat_summary, report_findings
        )
        
        logger.info(f"Report generated for user {user_id}: {filepath}")
        return FileResponse(
            filepath, 
            filename="health_report.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(e)}"
        )

@app.get("/history/predictions/{user_id}", response_model=List[PredictionSchema])
def get_prediction_history(user_id: int, db: Session = Depends(get_db)):
    try:
        predictions = db.query(Prediction).filter(
            Prediction.user_id == user_id
        ).order_by(Prediction.created_at.desc()).all()
        return predictions
    except Exception as e:
        logger.error(f"Error fetching prediction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching prediction history: {str(e)}"
        )

@app.get("/history/chats/{user_id}", response_model=List[ChatSchema])
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    try:
        chats = db.query(Chat).filter(
            Chat.user_id == user_id
        ).order_by(Chat.created_at.desc()).all()
        return chats
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chat history: {str(e)}"
        )

@app.get("/history/reports/{user_id}", response_model=List[ReportSchema])
def get_report_history(user_id: int, db: Session = Depends(get_db)):
    try:
        reports = db.query(Report).filter(
            Report.user_id == user_id
        ).order_by(Report.created_at.desc()).all()
        return reports
    except Exception as e:
        logger.error(f"Error fetching report history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching report history: {str(e)}"
        )

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
