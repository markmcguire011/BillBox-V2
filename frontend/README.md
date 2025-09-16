# BillBox Frontend

A minimal frontend for the BillBox invoice processing application.

## Features

- **Google OAuth Authentication** - Secure login with Google
- **Invoice Upload & Processing** - Upload images and extract text using OCR
- **Calendar Integration** - Create Google Calendar events automatically
- **Real-time Results** - View OCR results and processing status

## Setup

1. **Start a local server** (required for Google OAuth):
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Or using Node.js
   npx serve -s . -l 3000
   ```

2. **Configure Google OAuth**:
   - Set redirect URI to: `http://localhost:3000/callback.html`
   - Update backend `.env` file with your Google credentials

3. **Start the backend**:
   ```bash
   cd ../backend
   python main.py
   ```

4. **Open the frontend**:
   Navigate to `http://localhost:3000` in your browser

## Usage

1. **Login** - Click "Login with Google" to authenticate
2. **Upload Invoice** - Select an image file (PNG, JPG, etc.)
3. **Process** - Click "Process Invoice" to extract text
4. **Create Events** - Use the calendar section to create events
5. **Combined Flow** - Check "Create calendar event" when processing invoices

## Files

- `index.html` - Main application interface
- `callback.html` - OAuth callback handler
- `README.md` - This documentation

## API Integration

The frontend communicates with the FastAPI backend running on `http://localhost:8000`:

- `GET /auth/google` - Initiate OAuth flow
- `GET /auth/callback` - Handle OAuth callback
- `POST /invoice/process` - Process invoice images
- `POST /calendar/create-event` - Create calendar events

## Browser Requirements

- Modern browser with JavaScript enabled
- Supports File API for image uploads
- Popup windows enabled for OAuth flow