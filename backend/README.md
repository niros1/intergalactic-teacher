# Intergalactic Teacher Backend

AI-powered interactive reading platform backend built with FastAPI, LangGraph, and PostgreSQL.

## 🌟 Features

### Core Functionality
- **AI Story Generation**: Personalized story creation using LangGraph workflows and OpenAI GPT-4
- **Interactive Storytelling**: Choice-driven narratives with branching storylines
- **Content Safety**: Multi-layered content filtering for child safety
- **Reading Analytics**: Comprehensive progress tracking and parent dashboards
- **Multi-language Support**: Hebrew and English story generation
- **Child Profiles**: Age-appropriate content personalization

### Technical Features
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **LangGraph**: Advanced AI workflow orchestration for story generation
- **PostgreSQL**: Robust relational database with full ACID compliance
- **Redis**: High-performance caching and session management
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: API protection with Redis-backed rate limiting
- **Comprehensive Logging**: Structured logging with request tracing
- **Security Headers**: OWASP-compliant security middleware

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- OpenAI API Key

### Option 1: Docker Compose (Recommended)
```bash
# Clone the repository
cd intergalactic-teacher/backend

# Copy environment file
cp .env.example .env

# Edit .env with your OpenAI API key and other settings
nano .env

# Start all services
docker-compose up -d

# Run setup script
docker-compose exec api python scripts/setup.py
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL and Redis (using your preferred method)

# Run setup script
python scripts/setup.py

# Start the server
uvicorn app.main:app --reload
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Demo Account
- **Email**: demo@intergalactic.com
- **Password**: Demo123!

## 🏗️ Architecture

### Directory Structure
```
backend/
├── app/
│   ├── api/                 # API routes and endpoints
│   │   └── api_v1/
│   │       ├── api.py       # Main API router
│   │       └── endpoints/   # Individual endpoint modules
│   ├── core/                # Core application logic
│   │   ├── config.py        # Application settings
│   │   ├── security.py      # Authentication utilities
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   ├── logging.py       # Logging configuration
│   │   └── middleware.py    # Custom middleware
│   ├── db/                  # Database configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic services
│   ├── utils/               # Utility functions
│   ├── workflows/           # LangGraph workflows
│   └── main.py              # FastAPI application
├── migrations/              # Alembic database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suites
└── docker-compose.yml       # Docker services
```

### Database Schema

#### Core Models
- **Users**: Parent accounts with authentication
- **Children**: Child profiles with reading preferences
- **Stories**: AI-generated stories with metadata
- **Story Sessions**: Reading session tracking
- **Choices**: Story decision points
- **Story Branches**: Story paths based on choices
- **User Analytics**: Reading progress and metrics

### LangGraph Workflows

#### Story Generation Workflow
1. **Content Generation**: Create personalized story content
2. **Safety Check**: Multi-layered content safety validation
3. **Content Enhancement**: Improve content if needed
4. **Metrics Calculation**: Estimate reading time and difficulty

#### Content Safety Workflow
1. **OpenAI Moderation**: Automated content screening
2. **Age Appropriateness**: Child age-specific validation
3. **Cultural Sensitivity**: Cultural appropriateness analysis
4. **Educational Value**: Learning outcome assessment

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/intergalactic_teacher

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=3000

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Production Considerations
- Set `DEBUG=false` in production
- Use strong `SECRET_KEY` (32+ character random string)
- Configure proper CORS origins
- Set up SSL/TLS termination
- Use environment-specific database credentials
- Enable monitoring and alerting

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest -m "not slow"  # Skip slow tests
```

## 🛡️ Security Features

### Authentication & Authorization
- JWT token-based authentication
- Refresh token rotation
- Password strength validation
- Rate-limited login attempts

### Content Safety
- OpenAI moderation API integration
- Age-appropriate content filtering
- Cultural sensitivity analysis
- Multi-language profanity detection

### API Security
- Rate limiting per endpoint
- Request size validation
- Input sanitization
- Security headers (OWASP compliance)
- CORS configuration

### Data Protection
- Password hashing with bcrypt
- JWT token expiration
- Session invalidation
- COPPA compliance measures

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging
- Request tracing with unique IDs
- Error tracking with stack traces
- Performance metrics

### Metrics
- Request/response times
- API endpoint usage
- Error rates
- User engagement metrics

### Health Checks
- Database connectivity: `/health`
- Redis connectivity
- External API status

## 🚀 Deployment

### Docker Deployment
```bash
# Build production image
docker build -t intergalactic-teacher-backend .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start with Gunicorn
gunicorn app.main:app -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60
```

## 🤝 Development

### Code Quality
- **Black**: Code formatting
- **isort**: Import sorting  
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks

### Git Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Adding New Features
1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation
4. Run quality checks
5. Submit pull request

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Verify credentials in .env file
# Check if database exists
```

**Redis Connection Issues**
```bash
# Test Redis connectivity
redis-cli ping

# Check Redis configuration
redis-cli info
```

**OpenAI API Errors**
- Verify API key is valid
- Check API usage limits
- Monitor rate limiting

**Story Generation Failures**
- Check OpenAI API connectivity
- Verify content safety thresholds
- Review LangGraph workflow logs

## 📄 API Reference

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login  
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout

### User Management
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update user profile

### Children Management
- `GET /api/v1/children/` - List children
- `POST /api/v1/children/` - Create child profile
- `GET /api/v1/children/{id}` - Get child details
- `PUT /api/v1/children/{id}` - Update child
- `DELETE /api/v1/children/{id}` - Delete child

### Stories
- `GET /api/v1/stories/` - List stories
- `GET /api/v1/stories/{id}` - Get story details
- `POST /api/v1/stories/generate` - Generate new story
- `GET /api/v1/stories/recommendations/{child_id}` - Get recommendations

### Analytics
- `GET /api/v1/analytics/dashboard` - Parent dashboard
- `GET /api/v1/analytics/child/{id}` - Child analytics
- `GET /api/v1/analytics/child/{id}/progress` - Reading progress

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

For questions or support, please open an issue on GitHub.