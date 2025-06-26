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
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Primary Database)
- SQLite (Development Fallback)
- Alembic (Database Migrations)
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

- Python 3.11+
- Node.js 16+
- PostgreSQL 14+
- Google Gemini API key

## Setup

### Database Setup

1. **Install PostgreSQL** (if not already installed):
```bash
# macOS with Homebrew
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Windows
# Download from https://www.postgresql.org/download/windows/
```

2. **Create Database**:
```bash
# Create the database
createdb journal_db

# Or using psql
psql postgres -c "CREATE DATABASE journal_db;"
```

### Backend Setup

1. **Clone and navigate to the project**:
```bash
git clone <repository-url>
cd journal-app
```

2. **Create and activate a virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://$(whoami)@localhost:5432/journal_db
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
EOF
```

5. **Initialize the database**:
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

6. **Start the backend server**:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Start the development server**:
```bash
npm start
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username@localhost:5432/journal_db

# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Security
SECRET_KEY=your_secret_key_here
```

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in your `.env` file

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Management

### Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

### Database Backup
```bash
# Backup PostgreSQL database
pg_dump journal_db > backup.sql

# Restore from backup
psql journal_db < backup.sql
```

## Development

### Backend Development
- API endpoints are in `backend/app/api/`
- Database models in `backend/app/models/`
- AI services in `backend/app/services/`
- Database migrations in `backend/alembic/`
- Run tests: `pytest`

### Frontend Development
- Components in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- API services in `frontend/src/services/`
- Run tests: `npm test`

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Error**:
   - Ensure PostgreSQL is running: `brew services start postgresql@14`
   - Check if database exists: `psql -l`
   - Verify connection string in `.env`

2. **API Key Invalid**:
   - Get a new API key from Google AI Studio
   - Update the `GEMINI_API_KEY` in `.env`
   - Restart the server

3. **Migration Errors**:
   - Check if database exists
   - Verify PostgreSQL user permissions
   - Run `alembic current` to check migration status

## Latest Updates

- ✅ Migrated from SQLite to PostgreSQL
- ✅ Added Alembic database migrations
- ✅ Improved environment variable management
- ✅ Enhanced error handling and logging
- ✅ Added persistent conversation history for AI responses
- ✅ Improved date-based filtering with smooth transitions
- ✅ Added loading states and animations
- ✅ Improved mobile responsiveness

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 