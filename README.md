# Digital Sovereignty Mirror (DSM) 🔐

**Your Data. Your Knowledge. Your Decision.**

A personal AI-powered platform designed to help individuals regain control over their digital lives.

## 📌 About The Project

Digital Sovereignty Mirror combines local-first data management, privacy protection, knowledge organization, and AI assistance into a single transparent system.

### 🎯 Core Mission
Build a trusted layer between humans and AI systems, where the user remains the owner of data, knowledge, and decisions.

## 🚀 Key Features

- **🔒 Privacy Dashboard** - View permissions, track data access, monitor AI activity logs
- **🤖 Personal AI Assistant** - Summarize notes, organize projects, search personal knowledge  
- **💾 Local-First Storage** - SQLite database with encrypted records and optional cloud backup
- **🧠 Knowledge Graph** - Connect ideas, link documents, build a personal knowledge network
- **🔐 End-to-End Encryption** - Fernet symmetric encryption for all sensitive data
- **📋 Audit Logging** - Complete transparency on all actions and AI access

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│         Mobile Application (Flutter)                │
│    Privacy Dashboard · Notes · Knowledge Graph      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│            API Gateway (FastAPI)                    │
│      Authentication · Rate Limiting · CORS          │
└──────────────────┬──────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼──────┐ ┌──────▼────┐ ┌────▼─────┐
│  Auth    │ │  Content  │ │  Search  │
│  APIs    │ │   APIs    │ │  APIs    │
└───┬──────┘ └──────┬────┘ └────┬─────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼──────────┐ ┌─▼─────────┐ ┌──▼────────┐
│ Encryption   │ │ AI Engine │ │ Audit Log │
│ Manager      │ │ (Search & │ │ (Full    │
│ (Fernet)     │ │ Summarize)│ │ Tracking)│
└───┬──────────┘ └─┬─────────┘ └──┬────────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
        ┌──────────▼──────────┐
        │  SQLite Database    │
        │  (Encrypted)        │
        │  Users · Notes · KG │
        │  Audit Logs · Perms │
        └─────────────────────┘
```

## 📂 Project Structure

```
Studio/
├── README.md
├── DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
├── startup.sh
├── .gitignore
│
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
│
├── database/
│   ├── schema.sql           # Database schema
│   └── init_db.py           # Database initialization
│
├── security/
│   ├── encryption.py        # Fernet encryption manager
│   ├── authentication.py    # JWT & bcrypt auth
│   └── audit.py             # Audit logging
│
├── ai-engine/
│   ├── search.py            # Knowledge search
│   └── summarization.py     # Text summarization
│
├── docs/
│   ├── ARCHITECTURE.md      # System design
│   ├── API.md               # API documentation
│   └── SECURITY.md          # Security guide
│
└── tests/
    ├── test_encryption.py   # Encryption tests
    └── test_auth.py         # Authentication tests
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python FastAPI |
| **Database** | SQLite (local) / PostgreSQL (prod) |
| **Encryption** | Fernet (AES-128) |
| **Auth** | JWT + bcrypt |
| **Mobile** | Flutter / React Native |
| **AI** | OpenAI API (optional) |
| **DevOps** | Docker & Docker Compose |

## 🔐 Security Features

✅ **Least Privilege Access** - Users access only their own data  
✅ **End-to-End Encryption** - Fernet symmetric encryption at rest  
✅ **Password Hashing** - bcrypt with 12 rounds  
✅ **JWT Tokens** - 30-minute expiration  
✅ **Audit Logs** - All actions tracked with timestamps  
✅ **PBKDF2 Key Derivation** - 100,000 iterations  
✅ **GZIP Compression** - Optimized API responses  
✅ **CORS Protection** - Configurable cross-origin access  

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Git
- pip or virtualenv

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/omd15667-oss/Studio.git
cd Studio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Initialize database
python database/init_db.py
```

### 2️⃣ Configuration

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env with your settings
# (Change SECRET_KEY and ENCRYPTION_KEY for production)
```

### 3️⃣ Run Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ **API Ready**: http://localhost:8000  
📖 **Docs**: http://localhost:8000/docs  
🔄 **Redoc**: http://localhost:8000/redoc  

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f dsm-api

# Stop services
docker-compose down
```

**API**: http://localhost:8000

## 📋 API Endpoints (v0.1)

### Health & System
```
GET /health              # Health check
GET /                    # API info
```

### Authentication (Coming v0.1)
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
```

### Notes Management (Coming v0.2)
```
GET    /api/v1/notes
POST   /api/v1/notes
PUT    /api/v1/notes/{id}
DELETE /api/v1/notes/{id}
```

### Search & AI (Coming v0.2)
```
GET  /api/v1/search?q=query
POST /api/v1/ai/summarize
POST /api/v1/ai/extract-keywords
```

### Privacy Dashboard (Coming v0.3)
```
GET /api/v1/privacy/permissions
GET /api/v1/privacy/activity
GET /api/v1/audit/logs
```

## 📅 Roadmap

| Version | Timeline | Features |
|---------|----------|----------|
| **v0.1** | Q1 2024 | ✅ Project setup, API gateway, health checks |
| **v0.2** | Q2 2024 | Auth, Notes CRUD, basic search & summarization |
| **v0.3** | Q3 2024 | Knowledge graph, enhanced privacy dashboard |
| **v0.4** | Q4 2024 | Encrypted cloud sync, 2FA |
| **v1.0** | 2025 | Full personal AI platform, mobile app |

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=security tests/

# Specific test
pytest tests/test_encryption.py -v
```

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design & layers
- **[API.md](docs/API.md)** - Complete API documentation
- **[SECURITY.md](docs/SECURITY.md)** - Security principles & implementation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## 🔒 Security Checklist

For production deployment:

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Change `ENCRYPTION_KEY` in `.env`
- [ ] Set `DEBUG=False`
- [ ] Configure HTTPS/TLS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up database backups
- [ ] Enable rate limiting
- [ ] Configure monitoring
- [ ] Keep dependencies updated
- [ ] Implement brute-force protection

## 🚀 Performance Optimizations

- **GZIP Compression** - API responses compressed
- **Database Indexing** - Fast queries on user_id, created_at
- **Connection Pooling** - Efficient database connections
- **Caching** - Response caching for search results
- **Pagination** - Large result sets paginated

## 📞 Support & Issues

- **GitHub Issues**: [Report bugs](https://github.com/omd15667-oss/Studio/issues)
- **Discussions**: [Ask questions](https://github.com/omd15667-oss/Studio/discussions)
- **Email**: Contact through GitHub profile

## 📜 License

This project is released under the **MIT License**.

---

## 🎯 First Release Goals (v0.1)

- ✅ Project structure & setup
- ✅ API gateway with FastAPI
- ✅ Health checks & monitoring
- ✅ Security layer (encryption & auth modules)
- ✅ Database schema & initialization
- ✅ Audit logging framework
- ✅ Documentation & deployment guide
- ⏳ Full auth endpoints (next)
- ⏳ Notes CRUD operations (next)
- ⏳ Mobile app integration (next)

---

## 🌟 Built for Human-Centered AI

Digital Sovereignty Mirror aims to create a future where AI empowers people without taking ownership of their identity, knowledge, or privacy.

**Your data stays yours. Always.**

---

**Repository**: https://github.com/omd15667-oss/Studio  
**Live API**: http://localhost:8000 (development)  
**Documentation**: http://localhost:8000/docs  
**Version**: 0.1.0  
**Status**: 🟢 Active Development
