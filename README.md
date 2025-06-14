# FitnessCoach Backend API

A FastAPI-based backend application for fitness coaches to manage clients, training programs, and nutrition plans.

## 🚀 Features

### Authentication & User Management
- JWT-based authentication
- User registration and login
- Password hashing with bcrypt
- Role-based access control (Trainer, Admin)
- Profile management

### Client Management
- Create and manage client profiles
- Track client information (personal, physical, fitness goals)
- Search and filter clients
- Client progress tracking
- Soft delete functionality

### Database Models
- **Users**: Trainers and admin accounts
- **Clients**: Client profiles with comprehensive information
- **Programs**: Training program templates (future feature)
- **Nutrition Plans**: Meal planning system (future feature)

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt via passlib
- **Migrations**: Alembic
- **Validation**: Pydantic schemas
- **CORS**: Enabled for frontend integration

## 📁 Project Structure

```
fitness-coach/
├── app/
│   ├── api/
│   │   ├── endpoints/          # API route handlers
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   └── clients.py      # Client management endpoints
│   │   └── api.py              # Main API router
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database connection
│   │   └── security.py         # JWT and password utilities
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── client.py           # Client model
│   │   ├── program.py          # Training program models
│   │   └── nutrition.py        # Nutrition plan models
│   ├── schemas/
│   │   ├── user.py             # User Pydantic schemas
│   │   └── client.py           # Client Pydantic schemas
│   ├── services/
│   │   ├── user_service.py     # User business logic
│   │   └── client_service.py   # Client business logic
│   ├── utils/
│   │   └── deps.py             # Dependency injection
│   └── main.py                 # FastAPI application
├── alembic/                    # Database migrations
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
├── setup_db.py                 # Database setup script
└── create_sample_users.py      # Create test users
```

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- pip or conda

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd C:/university/fitness-coach
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Create MySQL database**:
   ```sql
   CREATE DATABASE fitness_coach_db;
   CREATE USER 'fitness_coach_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON fitness_coach_db.* TO 'fitness_coach_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. **Setup database**:
   ```bash
   python setup_db.py
   ```

7. **Initialize Alembic**:
   ```bash
   alembic stamp head
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

8. **Create sample users** (optional):
   ```bash
   python create_sample_users.py
   ```

9. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update current user
- `POST /api/v1/auth/change-password` - Change password

### Clients
- `POST /api/v1/clients/` - Create client
- `GET /api/v1/clients/` - Get all clients
- `GET /api/v1/clients/{client_id}` - Get specific client
- `PUT /api/v1/clients/{client_id}` - Update client
- `DELETE /api/v1/clients/{client_id}` - Delete client
- `GET /api/v1/clients/count` - Get client count

### Health Check
- `GET /api/v1/health` - API health status

## 🔒 Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Register** or **login** to get an access token
2. Include the token in the `Authorization` header:
   ```
   Authorization: Bearer <your_jwt_token>
   ```

### Sample Login Request
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trainer@fitnesscoach.com",
    "password": "trainer123"
  }'
```

## 🗄️ Database Schema

### Users Table
- Personal information (name, email, phone)
- Professional details (specialization, experience)
- Authentication (hashed password, role)
- Account status (active, verified)

### Clients Table
- Personal information
- Physical measurements
- Fitness goals and preferences
- Medical information
- Emergency contacts

## 🧪 Testing

### Sample Users
After running `create_sample_users.py`:

**Admin User:**
- Email: `admin@fitnesscoach.com`
- Password: `admin123`

**Trainer User:**
- Email: `trainer@fitnesscoach.com` 
- Password: `trainer123`

### Manual Testing
1. Register a new trainer account
2. Login to get JWT token
3. Create clients using the token
4. Test CRUD operations on clients

## 🔄 Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## ⚙️ Configuration

Key environment variables in `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=fitness_coach_user
DB_PASSWORD=your_password
DB_NAME=fitness_coach_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 🚀 Deployment

### Production Considerations
1. Use strong `SECRET_KEY` 
2. Set `ENVIRONMENT=production`
3. Configure secure database credentials
4. Set up SSL/TLS certificates
5. Use a production ASGI server (Gunicorn + Uvicorn)
6. Set up monitoring and logging

### Docker Deployment (Future)
```dockerfile
# Example Dockerfile structure
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Frontend Integration

This backend is designed to work with the Next.js frontend located at:
`C:/university/fitness-coach-fe`

### CORS Configuration
The API is configured to allow requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`

### API Base URL
Frontend should use: `http://localhost:8000/api/v1`

## 🔮 Future Features

- [ ] Training program management
- [ ] Nutrition plan creation
- [ ] Progress tracking with charts
- [ ] File upload for client photos
- [ ] Email notifications
- [ ] Calendar integration
- [ ] Workout logging
- [ ] Meal tracking
- [ ] Payment integration
- [ ] Mobile app API support

## 📝 Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Write docstrings for all classes and methods
4. Create tests for new features
5. Update documentation

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error:**
- Check MySQL is running
- Verify credentials in `.env`
- Ensure database exists

**Import Errors:**
- Activate virtual environment
- Install all requirements
- Check Python path

**JWT Token Issues:**
- Verify `SECRET_KEY` is set
- Check token expiration
- Ensure proper Authorization header format

### Logs
Check application logs for detailed error information:
```bash
tail -f logs/app.log  # If logging to file
```

## 📄 License

This project is for educational purposes.

---

**API Status**: ✅ Ready for development and testing
**Frontend Integration**: ✅ CORS configured for Next.js
**Database**: ✅ MySQL with comprehensive schema
**Authentication**: ✅ JWT-based security implemented