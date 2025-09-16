"""
Invoice processing routes with OCR integration
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from .auth import get_current_user
from .calendar import CalendarEventRequest

# Add OCR service to path
sys.path.append('../services/ocr')
from billbox_ocr import BillBoxOCR

router = APIRouter(prefix="/invoice", tags=["invoice"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Initialize OCR service
ocr_service = BillBoxOCR(pipeline_type='invoice')

class InvoiceResponse(BaseModel):
    success: bool
    invoice_data: Optional[Dict] = None
    calendar_event: Optional[Dict] = None
    error: Optional[str] = None

@router.post("/process")
async def process_invoice(
    file: UploadFile = File(...),
    create_calendar_event: bool = Form(False),
    event_summary: Optional[str] = Form(None),
    event_description: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    """Process invoice image with OCR and optionally create calendar event"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Extract invoice data using OCR
        invoice_data = ocr_service.extract_invoice_data(image)
        
        if "error" in invoice_data:
            return InvoiceResponse(
                success=False,
                error=f"OCR processing failed: {invoice_data['error']}"
            )
        
        response_data = {
            "success": True,
            "invoice_data": invoice_data
        }
        
        # Optionally create calendar event
        if create_calendar_event and event_summary:
            try:
                # Create default event timing (1 hour from now)
                start_time = datetime.utcnow()
                end_time = start_time + timedelta(hours=1)
                
                event_request = CalendarEventRequest(
                    summary=event_summary,
                    description=event_description or f"Invoice processing: {file.filename}",
                    start_time=start_time.isoformat() + 'Z',
                    end_time=end_time.isoformat() + 'Z'
                )
                
                # Reconstruct Google credentials
                credentials = Credentials(
                    token=current_user["google_access_token"],
                    refresh_token=current_user.get("google_refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET
                )
                
                if credentials.expired:
                    credentials.refresh(Request())
                
                service = build('calendar', 'v3', credentials=credentials)
                
                event = {
                    'summary': event_request.summary,
                    'description': event_request.description,
                    'start': {
                        'dateTime': event_request.start_time,
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': event_request.end_time,
                        'timeZone': 'UTC',
                    },
                }
                
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                
                response_data["calendar_event"] = {
                    "event_id": created_event['id'],
                    "event_link": created_event.get('htmlLink'),
                    "summary": created_event['summary']
                }
                
            except Exception as calendar_error:
                response_data["calendar_event"] = {
                    "error": f"Calendar event creation failed: {str(calendar_error)}"
                }
        
        return InvoiceResponse(**response_data)
    
    except Exception as e:
        return InvoiceResponse(
            success=False,
            error=f"Invoice processing failed: {str(e)}"
        )