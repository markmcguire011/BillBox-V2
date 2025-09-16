"""
Google Calendar integration routes
"""

import os
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from .auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

class CalendarEventRequest(BaseModel):
    summary: str
    description: Optional[str] = ""
    start_time: str  # ISO format
    end_time: str    # ISO format
    attendees: Optional[List[str]] = []

@router.post("/create-event")
async def create_calendar_event(
    event_data: CalendarEventRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create a Google Calendar event"""
    try:
        # Reconstruct Google credentials from JWT
        credentials = Credentials(
            token=current_user["google_access_token"],
            refresh_token=current_user.get("google_refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Refresh token if needed
        if credentials.expired:
            credentials.refresh(Request())
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Prepare event data
        event = {
            'summary': event_data.summary,
            'description': event_data.description,
            'start': {
                'dateTime': event_data.start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event_data.end_time,
                'timeZone': 'UTC',
            },
        }
        
        if event_data.attendees:
            event['attendees'] = [{'email': email} for email in event_data.attendees]
        
        # Create the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            "success": True,
            "event_id": created_event['id'],
            "event_link": created_event.get('htmlLink'),
            "summary": created_event['summary'],
            "start_time": created_event['start']['dateTime'],
            "end_time": created_event['end']['dateTime']
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create calendar event: {str(e)}")