from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
from typing import Dict, Any

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.report_dir = "static/reports"
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_health_report(self, user_data: Dict[str, Any], 
                             prediction: Dict[str, Any],
                             chat_summary: str,
                             report_findings: str) -> str:
        """Generate PDF health report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_report_{timestamp}.pdf"
        filepath = os.path.join(self.report_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  
        )
        story.append(Paragraph("Health Assessment Report", title_style))
        
        
        story.append(Paragraph("Personal Information", self.styles['Heading2']))
        user_info = [
            ["Name:", user_data.get('name', 'N/A')],
            ["Age:", str(user_data.get('age', 'N/A'))],
            ["Email:", user_data.get('email', 'N/A')],
            ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M")]
        ]
        
        user_table = Table(user_info, colWidths=[1.5*inch, 3*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(user_table)
        story.append(Spacer(1, 20))
        
        
        story.append(Paragraph("Disease Risk Assessment", self.styles['Heading2']))
        risk_info = [
            ["Disease:", prediction.get('disease', 'N/A')],
            ["Risk Score:", f"{prediction.get('risk', 0) * 100:.1f}%"],
            ["Explanation:", prediction.get('explanation', 'N/A')]
        ]
        
        risk_table = Table(risk_info, colWidths=[1.5*inch, 3*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 20))
        
        
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        recommendations = prediction.get('recommendations', '').split('\n')
        for rec in recommendations:
            if rec.strip():
                story.append(Paragraph(f"• {rec.strip()}", self.styles['BodyText']))
        
        story.append(Spacer(1, 20))
        
        
        if chat_summary:
            story.append(Paragraph("Chat Summary", self.styles['Heading2']))
            story.append(Paragraph(chat_summary, self.styles['BodyText']))
            story.append(Spacer(1, 20))
        
        
        if report_findings:
            story.append(Paragraph("Medical Report Analysis", self.styles['Heading2']))
            story.append(Paragraph(report_findings, self.styles['BodyText']))
            story.append(Spacer(1, 20))
        
        
        doc.build(story)
        
        return filepath


report_generator = ReportGenerator()

