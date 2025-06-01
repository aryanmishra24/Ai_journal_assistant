# Journal App

A modern journaling application with AI-powered insights and mood tracking. Built with FastAPI, React, and Material-UI.

## Features

- 📝 **Journal Entries**
  - Create and manage daily journal entries
  - AI-powered responses to your entries
  - Conversation history with context-aware AI
  - Date-based filtering and organization
  - Smooth animations and transitions

- 🎯 **Mood Tracking**
  - Track your daily moods with scores and labels
  - Visualize mood trends over time
  - AI-generated mood summaries
  - Detailed mood analysis

- 🤖 **AI Features**
  - Context-aware responses using conversation history
  - Daily journal summaries
  - Mood pattern analysis
  - Writing style insights
  - Sentiment analysis

- 📊 **Insights & Analytics**
  - Daily summaries of your journaling
  - Mood statistics and trends
  - Writing patterns and frequency
  - Keyword analysis
  - Sentiment tracking

- 🎨 **Modern UI/UX**
  - Clean, responsive design
  - Dark/Light theme support
  - Smooth animations
  - Intuitive navigation
  - Mobile-friendly interface

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy (ORM)
- PostgreSQL
- LangChain
- Google Gemini API
- JWT Authentication

### Frontend
- React
- TypeScript
- Material-UI
- Axios
- React Router
- Context API

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Google Gemini API key

## Setup

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your configuration:
```
DATABASE_URL=postgresql://user:password@localhost:5432/journal_db
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Start the backend server:
```bash
uvicorn app.main:app --reload --port 8003
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8003/docs`
- ReDoc: `http://localhost:8003/redoc`

## Development

### Backend Development
- API endpoints are in `backend/app/api/`
- Database models in `backend/app/models/`
- AI services in `backend/app/services/`
- Run tests: `pytest`

### Frontend Development
- Components in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- API services in `frontend/src/services/`
- Run tests: `npm test`

## Latest Updates

- Added persistent conversation history for AI responses
- Improved date-based filtering with smooth transitions
- Enhanced error handling and user feedback
- Added loading states and animations
- Improved mobile responsiveness

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 