# BillBox-V2

🧾 **Invoice Processing System** with OCR, Google OAuth, and Calendar Integration

A complete web application that processes invoice images using advanced OCR technology and integrates with Google Calendar for automated event creation.

## ✨ Features

- **🔐 Google OAuth Authentication** - Secure login with Google accounts
- **📄 Advanced OCR Processing** - Extract text from invoice images using custom C++ preprocessing
- **📅 Google Calendar Integration** - Automatically create calendar events from invoice data
- **🖥️ Modern Web Interface** - Clean, responsive frontend for easy interaction
- **🚀 One-Click Startup** - Unified launcher script starts all services

## 🏗️ Architecture

```
BillBox-V2/
├── backend/              # FastAPI REST API
│   ├── main.py          # Application entry point
│   ├── routes/          # Organized route modules
│   │   ├── auth.py      # Google OAuth endpoints
│   │   ├── calendar.py  # Calendar integration
│   │   └── invoice.py   # OCR processing
│   └── requirements.txt # Python dependencies
├── frontend/            # Minimal web interface
│   ├── index.html      # Main application UI
│   └── callback.html   # OAuth callback handler
├── services/
│   ├── ocr/            # OCR service with C++ preprocessing
│   └── preprocessing/  # C++ image processing pipeline
└── run.py              # Unified launcher script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Console project with OAuth2 credentials
- Modern web browser

### 1. Clone & Setup
```bash
git clone <repository-url>
cd BillBox-V2
```

### 2. Configure Google OAuth
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Calendar API and OAuth2
3. Create OAuth 2.0 credentials
4. Copy `backend/.env.example` to `backend/.env`
5. Add your Google credentials to `.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:3000/callback.html
   JWT_SECRET=your_secret_key
   ```

### 3. Run the Application
```bash
# One command to start everything!
python run.py
```

Or use platform-specific scripts:
```bash
# macOS/Linux
./run.sh

# Windows
run.bat
```

### 4. Open Your Browser
The launcher automatically opens `http://localhost:3000`

## 🛠️ Manual Setup (Advanced)

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
python -m http.server 3000
```

### OCR Service
```bash
cd services/ocr
# Optional: Build C++ preprocessing module
python setup.py build_ext --inplace
```

## 📊 API Endpoints

### Authentication
- `GET /auth/google` - Initiate OAuth flow
- `GET /auth/callback` - Handle OAuth callback

### Invoice Processing
- `POST /invoice/process` - Upload and process invoice images

### Calendar Integration
- `POST /calendar/create-event` - Create Google Calendar events

### Utility
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🔧 Services

### Backend (Port 8000)
- **FastAPI** REST API with automatic documentation
- **Google OAuth2** integration for secure authentication
- **Google Calendar API** integration
- **OCR Service** integration with custom preprocessing

### Frontend (Port 3000)
- **Vanilla JavaScript** for maximum compatibility
- **Responsive design** for mobile and desktop
- **Real-time status updates** and progress indicators
- **OAuth popup flow** for seamless authentication

### OCR Service
- **Custom C++ preprocessing** for optimal OCR results
- **Tesseract integration** for text extraction
- **Multiple processing pipelines** (invoice, document, custom)
- **Confidence scoring** and word-level results

## 🎯 Usage Workflow

1. **Authenticate** - Login with your Google account
2. **Upload Invoice** - Select an image file (PNG, JPG, etc.)
3. **Process** - OCR extracts text automatically
4. **Create Events** - Optionally create calendar events
5. **Review Results** - View extracted text and confidence scores

## 🧪 Development

### Project Structure
- **Modular backend** with separated route files
- **Clean frontend** with minimal dependencies  
- **Reusable OCR service** with C++ optimization
- **Comprehensive error handling** and logging

### Key Technologies
- **Backend**: FastAPI, Uvicorn, Google APIs, JWT
- **Frontend**: HTML5, JavaScript ES6, CSS3
- **OCR**: Tesseract, OpenCV, Custom C++ preprocessing
- **Infrastructure**: Python HTTP server, Cross-platform scripts

## 🔍 Troubleshooting

### Common Issues
1. **Google OAuth errors** - Check redirect URI configuration
2. **OCR preprocessing unavailable** - C++ module not built (falls back to basic processing)
3. **Port conflicts** - Ensure ports 3000 and 8000 are available
4. **Python version** - Requires Python 3.8 or higher

### Logs
- Backend logs: Console output from FastAPI server
- Frontend: Browser developer console
- OCR: Service logs in terminal

## 📄 License

This project is provided as-is for demonstration purposes.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Database integration for user sessions
- Enhanced security measures
- Kubernetes deployment configuration
- Comprehensive test suite
- CI/CD pipeline setup
