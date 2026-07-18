# Digital Sovereignty Mirror (DSM)

**Your Data. Your Knowledge. Your Decision.**

A personal AI-powered platform designed to help individuals regain control over their digital lives.

## 📌 About The Project

Digital Sovereignty Mirror combines local-first data management, privacy protection, knowledge organization, and AI assistance into a single transparent system.

### Core Mission
Build a trusted layer between humans and AI systems, where the user remains the owner of data, knowledge, and decisions.

## 🚀 Key Features

- **Privacy Dashboard** - View permissions, track data access, monitor AI activity logs
- **Personal AI Assistant** - Summarize notes, organize projects, search personal knowledge
- **Local-First Storage** - SQLite database with encrypted records and optional cloud backup
- **Knowledge Graph** - Connect ideas, link documents, build a personal knowledge network

## 🏗️ Architecture

```
Mobile App (Flutter / React Native)
    ↓
Personal AI Layer (Knowledge · Search · Planning)
    ↓
Local DB (SQLite)
    ↓
Security Layer (Encryption · Authentication · Audit Logs)
    ↓
Cloud (Optional Encrypted Backup)
```

## 📂 Project Structure

```
Digital-Sovereignty-Mirror/
├── README.md
├── mobile-app/
│   ├── lib/
│   ├── pubspec.yaml
│   └── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── database/
│   ├── schema.sql
│   └── README.md
├── ai-engine/
│   ├── search.py
│   ├── summarization.py
│   └── README.md
├── security/
│   ├── encryption.py
│   ├── authentication.py
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── SECURITY.md
└── tests/
    ├── test_backend.py
    ├── test_database.py
    └── test_security.py
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Mobile | Flutter / React Native |
| Backend | Python FastAPI |
| Database | SQLite / PostgreSQL |
| AI Engine | LLM APIs + Local Models |
| Security | AES Encryption, JWT |
| Search | Vector Search (Future) |

## 🔐 Security Principles

- Least Privilege Access
- End-to-End Encryption
- Local Processing Whenever Possible
- Transparent Audit Logs
- User-Controlled Data Deletion

## 📅 Roadmap

| Version | Features |
|---------|----------|
| v0.1 | Authentication, Notes, Dashboard |
| v0.2 | AI Search & Summarization |
| v0.3 | Knowledge Graph |
| v0.4 | Encrypted Cloud Sync |
| v1.0 | Full Personal AI Platform |

## ⚡ Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/omd15667-oss/Studio.git
cd Studio
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Mobile App Setup
```bash
cd mobile-app
flutter pub get
flutter run
```

### 4. Database Setup
```bash
sqlite3 database/dsm.db < database/schema.sql
```

## 🎯 First Release Goals (v0.1)

- [x] Project Structure
- [ ] Secure Login System
- [ ] Notes Dashboard
- [ ] Privacy Activity Log
- [ ] Privacy Center

## 📜 License

This project is released under the MIT License.

---

**Built for Human-Centered AI**

Digital Sovereignty Mirror aims to create a future where AI empowers people without taking ownership of their identity, knowledge, or privacy.

**Repository**: https://github.com/omd15667-oss/Studio
