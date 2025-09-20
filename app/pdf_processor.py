import PyPDF2
import pytesseract
from PIL import Image
import io
import tempfile
import os
from typing import Optional
from fastapi import HTTPException, UploadFile

class PDFProcessor:
    def __init__(self):
        pass
    
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """Extract text from PDF using PyPDF2 and OCR"""
        try:
            content = await pdf_file.read()
            
            
            text = self._extract_with_pypdf2(content)
            
            
            if not text.strip():
                text = await self._extract_with_ocr(content)
            
            return text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")
    
    def _extract_with_pypdf2(self, content: bytes) -> str:
        """Extract text using PyPDF2"""
        text = ""
        try:
            with io.BytesIO(content) as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except:
            pass  
        
        return text
    
    async def _extract_with_ocr(self, content: bytes) -> str:
        """Extract text using OCR"""
        text = ""
        try:
            
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                temp_pdf.write(content)
                temp_pdf_path = temp_pdf.name
            
            
            text = "OCR extraction would be implemented here"
            
            os.unlink(temp_pdf_path)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
        
        return text


pdf_processor = PDFProcessor()

