# 🏥 Niramaya Health AI — Symptoms Checker

> 🤖 An **AI-powered health advisory platform** that lets users describe symptoms in natural language and receive intelligent disease predictions, descriptions, and precautions — powered by Logistic Regression, BioGPT, and Google Gemini.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![BioGPT](https://img.shields.io/badge/AI-BioGPT-ff6b6b)](https://huggingface.co/microsoft/biogpt)
[![Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-4285f4?logo=google)](https://ai.google.dev/)
[![Accuracy](https://img.shields.io/badge/LR%20Model%20Accuracy-91%25-brightgreen)](#-ml-models)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [ML Models](#-ml-models)
- [API Endpoints](#-api-endpoints)
- [Setup & Installation](#-setup--installation)
- [Running the Project](#-running-the-project)
- [Frontend Pages](#-frontend-pages)
- [Admin Panel](#-admin-panel)
- [Default Credentials](#-default-credentials)

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🧠 **3-Model AI Engine** | Logistic Regression (offline, fast), BioGPT (biomedical NLP), Gemini 1.5 Flash (conversational AI) |
| 👨‍👩‍👧‍👦 **Family Profile System** | One account manages multiple family member health profiles |
| 💬 **Chat History** | Persisted per-member conversation history, saved to PostgreSQL |
| 🔒 **Secure Auth** | bcrypt-hashed passwords, token-based admin sessions |
| 🛡️ **Admin Panel** | Full admin dashboard: user management, content management, system monitoring |
| 🌿 **Wellness Tips** | Seasonal health tips and articles managed by admin |
| 🔁 **Password Reset** | Built-in account password reset flow |
| 🤖 **Human Verification** | Captcha-style verify screen before AI session |
| 📊 **System Monitoring** | Admin can view live server stats and user activity |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML5, Vanilla CSS, Vanilla JavaScript |
| **Backend** | Python 3.9+, Flask 2.3.3, Flask-CORS |
| **Database** | PostgreSQL 12+ (via psycopg2-binary) |
| **ML — Model 1** | Scikit-learn Logistic Regression (`.pkl` — offline, instant) |
| **ML — Model 2** | Microsoft BioGPT via HuggingFace Transformers |
| **ML — Model 3** | Google Gemini 1.5 Flash (via `google-generativeai`) |
| **Security** | bcrypt password hashing, secrets-based token auth |
| **Data Processing** | pandas, joblib |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Frontend (HTML / CSS / JS)                │
│  home  │  about  │  symptom checker  │  wellness tips   │
│              admin login / dashboard                    │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTP REST (CORS enabled)
┌──────────────────────▼──────────────────────────────────┐
│           Flask Backend (Python 3.9+, port 5000)        │
│  /register  /login  /askgemini  /asklrv2  /askbiogpt   │
│  /savechat  /getchat  /member  /admin/*  /health-content│
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
┌─────────▼──────────┐   ┌──────────▼────────────────────┐
│   PostgreSQL DB    │   │      ML Model Pipeline         │
│  account_tbl       │   │  ├─ LR model (.pkl) — fast     │
│  member_tbl        │   │  ├─ BioGPT (HuggingFace)       │
│  chat_history_tbl  │   │  └─ Gemini 1.5 Flash (API)     │
│  admin_tbl         │   └────────────────────────────────┘
│  health_content_tbl│
└────────────────────┘
```

---

## 📁 Project Structure

```
Niramaya-Health-AI-Symptoms-Checker-Project/
│
├── backend/
│   ├── app.py                      # Flask app entry point + frontend serving
│   ├── db_config.py                # PostgreSQL connection helper
│   ├── init_db.py                  # DB setup + schema seeder
│   ├── schema.sql                  # Full PostgreSQL schema
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── routes/
│   │   ├── register_API.py         # POST /register
│   │   ├── user_login_API.py       # POST /login
│   │   ├── ask_AI_API.py           # POST /asklrv1, /asklrv2, /askgemini, /askbiogpt
│   │   ├── chat_API.py             # POST /savechat, /getchat, /deletechat
│   │   ├── member_API.py           # Family member CRUD
│   │   ├── password_reset_API.py   # Password reset flow
│   │   ├── admin_auth_API.py       # POST /admin/login, /admin/logout
│   │   ├── admin_users_API.py      # GET/PUT /admin/users
│   │   ├── health_content_API.py   # Wellness tips & articles CRUD
│   │   └── admin_monitoring_API.py # System stats & reports
│   │
│   └── model_LR/
│       ├── logistic_regression_model.pkl   # Trained LR disease predictor
│       ├── symptom_features.pkl            # Feature list (symptoms)
│       ├── Symptom_Description.csv         # Disease descriptions
│       └── Symptom_Precaution.csv          # Disease precautions
│
└── frontend/
    ├── home.html               # Landing page
    ├── verify_human.html       # Human verification before AI
    ├── question_input.html     # Main symptom checker chat UI
    ├── about.html              # About Niramaya
    ├── our_model.html          # Model info & performance metrics
    ├── wellness_tips.html      # Health tips (fetched from DB)
    ├── admin_login.html        # Admin login page
    ├── admin_dashboard.html    # Admin dashboard & monitoring
    ├── admin_users.html        # Admin user management
    ├── admin_content.html      # Admin content management
    ├── style.css               # Global stylesheet
    └── script.js               # Shared scripts (theme, research papers)
```

---

## 🗄️ Database Schema

The project uses a single **PostgreSQL** database named `projectH` with these tables:

| Table | Purpose |
|-------|---------|
| `account_tbl` | Family account (email, hashed password, family name) |
| `member_tbl` | Individual family members (name, age, gender, height, weight) |
| `chat_history_tbl` | Per-member AI conversation history (question, response, model used) |
| `admin_tbl` | Admin accounts with roles (`admin` / `superadmin`) |
| `admin_tokens_tbl` | Secure session tokens for admin authentication |
| `health_content_tbl` | Wellness tips and articles (published/draft) |

---

## 🤖 ML Models

### 1. Logistic Regression (LR) — Default & Fastest
- Trained on a multi-symptom disease dataset
- **91% accuracy** on test data
- Fully offline — no API calls needed
- Returns: predicted disease + description + precautions

### 2. Microsoft BioGPT
- Biomedical language model from HuggingFace (`microsoft/biogpt`)
- Loaded lazily on first request (heavy model)
- Best for: open-ended medical Q&A in biomedical context

### 3. Google Gemini 1.5 Flash
- Connected via `google-generativeai` SDK
- Fast, conversational, and highly capable
- Best for: natural language health explanations

---

## 🔌 API Endpoints

### 🔑 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register a new family account |
| `POST` | `/login` | Login to an existing account |
| `POST` | `/reset-password` | Reset account password |

### 👨‍👩‍👧 Family Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/addmember` | Add a family member |
| `POST` | `/getmembers` | Get all members for an account |
| `PUT` | `/updatemember` | Update member details |
| `DELETE` | `/deletemember` | Delete a family member |

### 🤖 AI / Symptom Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/asklrv1` | LR prediction (disease + description) |
| `POST` | `/asklrv2` | LR prediction (disease + description + precautions) |
| `POST` | `/askgemini` | Gemini 1.5 Flash health response |
| `POST` | `/askbiogpt` | BioGPT biomedical response |

### 💬 Chat History
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/savechat` | Save a chat exchange to DB |
| `POST` | `/getchat` | Retrieve chat history for a member |
| `POST` | `/deletechat` | Delete a specific chat record |

### 🛡️ Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/login` | Admin authentication → returns token |
| `POST` | `/admin/logout` | Revoke admin session token |
| `GET`  | `/admin/verify` | Verify admin token validity |
| `GET`  | `/admin/users` | List all user accounts |
| `PUT`  | `/admin/users/<id>` | Update or deactivate a user |
| `GET`  | `/admin/monitoring` | Server stats & usage reports |
| `GET`  | `/health-content` | Get published wellness content |
| `POST` | `/health-content` | Create new content (admin) |
| `PUT`  | `/health-content/<id>` | Update content (admin) |
| `DELETE` | `/health-content/<id>` | Delete content (admin) |

---

## ⚙️ Setup & Installation

### Prerequisites

```
- Python 3.9+
- PostgreSQL 12+
- pip (Python package manager)
```

### 1. Clone the Repository

```bash
git clone https://github.com/krunal-018/Niramaya-Health-AI-Symptoms-Checker-Project.git
cd Niramaya-Health-AI-Symptoms-Checker-Project
```

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

> ⚠️ `torch` and `transformers` are large packages (~2–4 GB). BioGPT is only loaded when the `/askbiogpt` endpoint is called.

### 3. Set Up PostgreSQL

Create the database and run the schema:

```bash
# Option A — Let the init script do everything automatically
cd backend
python init_db.py

# Option B — Manual setup in psql
psql -U postgres
CREATE DATABASE "projectH";
\c projectH
\i schema.sql
```

**Database connection defaults** (see `db_config.py`):
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password tried in order: env `DB_PASSWORD` → `1234` → `postgres`

To override, set environment variables:
```bash
set DB_HOST=localhost
set DB_PORT=5432
set DB_USER=postgres
set DB_PASSWORD=your_password
```

### 4. Configure Gemini API Key

In `backend/routes/ask_AI_API.py`, replace the API key with your own:

```python
GEMINI_API_KEY = "your-google-gemini-api-key-here"
```

Get a free key at: https://aistudio.google.com/app/apikey

---

## 🚀 Running the Project

```bash
cd backend
python app.py
```

Flask will start on `http://127.0.0.1:5000` and automatically serve the frontend.

Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

> ✅ The Flask app serves both the REST API **and** the HTML frontend — no separate web server needed.

---

## 🖥️ Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| 🏠 Home | `/home.html` | Landing page with research papers |
| ✅ Verify | `/verify_human.html` | Human check before starting AI chat |
| 💬 Checker | `/question_input.html` | Main symptom checker (select model, ask questions) |
| ℹ️ About | `/about.html` | About the platform |
| 🤖 Models | `/our_model.html` | How the models work + performance metrics |
| 🌿 Wellness | `/wellness_tips.html` | Seasonal health tips from the database |
| 🔐 Admin Login | `/admin_login.html` | Admin authentication |
| 📊 Dashboard | `/admin_dashboard.html` | Monitoring & system reports |
| 👥 Users | `/admin_users.html` | Manage registered users |
| 📝 Content | `/admin_content.html` | Manage wellness tips & articles |

---

## 🛡️ Admin Panel

The admin panel at `/admin_login.html` provides:

- **System Monitoring** — Active users, API request stats, server health
- **User Management** — View, activate/deactivate, and manage user accounts
- **Content Management** — Create, edit, publish, or delete wellness tips and articles
- **Secure Sessions** — Token-based auth with 24-hour expiry (auto-invalidated on logout)

---

## 🔑 Default Credentials

### Admin Account (auto-seeded on first run)

| Field | Value |
|-------|-------|
| **Email** | `admin@niramaya.com` |
| **Username** | `admin` |
| **Password** | `Admin@1234` |
| **Role** | `admin` |

> 🔒 Change the default admin password after your first login in a production environment.

---

## 📦 Dependencies

```
Flask==2.3.3
Flask-Cors==4.0.0
psycopg2-binary==2.9.9
bcrypt==4.0.1
joblib==1.3.2
pandas==2.2.2
google-generativeai==0.5.4
transformers>=4.38.0
torch>=2.2.0
```

Install all with:
```bash
pip install -r requirements.txt
```

---

## 🧪 Testing

Test scripts are available in the `backend/` directory:

```bash
# Admin authentication tests
python test_admin_auth.py

# Admin monitoring tests
python test_admin_monitoring.py

# User management tests
python test_admin_user_management.py

# Health content tests
python test_health_content.py

# Live server integration tests (requires running server)
python test_live_server.py
```

---

## 📄 License

This project is licensed under the **MIT License**.


*Built with ❤️ for healthcare innovation · Last Updated: October 2026*"# Niramaya-Health-AI" 
