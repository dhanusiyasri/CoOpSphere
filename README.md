# 🌐 CoOpSphere

### AI & LMS-Enabled Cooperative Capacity Building, ERP & Employment Ecosystem

> **One Connected Journey — From Training to Skills, Skills to Opportunities, and Opportunities to Empowerment.**

[![Problem Statement](https://img.shields.io/badge/SIH-26087-blue)](https://github.com/dhanusiyasri/CoOpSphere)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB)](https://react.dev/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/Project-SIH%20Prototype-orange)](https://github.com/dhanusiyasri/CoOpSphere)

**CoOpSphere** is an integrated digital ecosystem designed for NCCT's cooperative capacity-building and employment ecosystem.

It connects **Training ERP, Learning Management, Skills & Credentials, Career Services, Employer Engagement, Placement Tracking, and Training Intelligence** in a single platform.

---

## 📌 Problem Statement

NCCT and its affiliated institutions conduct training and capacity-building programmes for cooperative personnel, farmers, SHGs, dairy cooperatives, rural youth, and other stakeholders.

However, training-related activities can become fragmented across different processes and systems.

This can lead to:

* 📋 Manual programme and participant management
* 🔄 Duplication of trainee information
* 📊 Limited visibility into training outcomes
* 🎓 Difficulty tracking learning and skills
* 📜 Fragmented certification records
* 💼 Weak connection between training and employment
* 📈 Limited placement and retention analytics
* 🧩 Difficulty identifying future training requirements

CoOpSphere addresses these challenges by creating a **unified digital journey from training to employment**.

---

# 💡 Our Solution

CoOpSphere provides a centralized platform where different stakeholders can interact through role-based workflows.

### 👤 Trainees

* Access training programmes
* Track learning and applications
* Manage career information
* Apply for employment opportunities
* Track interviews, offers, and placements
* View post-placement follow-up information

### 👨‍🏫 Trainers / Institutions

* Manage training programmes
* Create courses and modules
* Define learning objectives
* Create lessons
* Manage batches and training activities
* Track training operations

### 🏢 Employers

* Publish job opportunities
* View applications
* Shortlist candidates
* Schedule interviews
* Manage offers
* Track joining and employment outcomes
* Record post-placement feedback

### 🏛️ NCCT Administrators

* Monitor the complete ecosystem
* Manage training and institutional activities
* Monitor employment outcomes
* Access placement analytics
* Track post-placement retention

---

# 🚀 Key Features

## 🎓 Training ERP

The Training ERP provides the operational foundation for managing training programmes.

Features include:

* Training programme management
* Training batch management
* Participant profiles
* Nomination workflows
* Enrolment management
* Course management
* Module management
* Lesson management
* Learning objectives
* Training scheduling
* Training logistics
* Training evaluation

The backend exposes dedicated Training ERP APIs and role-based programme management.

---

## 📚 Learning Management System

CoOpSphere provides the foundation for structured digital learning.

A course can contain:

```text
Course
 ├── Module
 │    ├── Learning Objectives
 │    └── Lessons
 │          ├── Content
 │          ├── Duration
 │          └── Mandatory Status
```

This enables training content to be organized into measurable learning units.

---

## 🧠 Skills & Skill Passport

The platform includes dedicated skill-management functionality for building a learner's digital skill profile.

The long-term vision is to connect:

```text
Training
   ↓
Learning Objectives
   ↓
Assessment
   ↓
Skills
   ↓
Credentials
   ↓
Skill Passport
   ↓
Career Opportunities
```

This creates a continuous record of learner development.

---

## 💼 Careers & Employment Ecosystem

CoOpSphere includes an end-to-end employment workflow.

### Job Lifecycle

```text
Job Published
      ↓
Trainee Applies
      ↓
Application Review
      ↓
Shortlisting
      ↓
Interview
      ↓
Selection
      ↓
Offer
      ↓
Offer Acceptance
      ↓
Joining
      ↓
Employment Follow-up
```

The current implementation supports job posting, applications, application status management, interview scheduling, offers, placement outcomes, and role-based access for trainees, employers, and NCCT administrators.

---

## 📊 Placement Analytics

CoOpSphere provides placement analytics based on jobs, applications, offers, and employment outcomes.

Current analytics include:

* Total jobs
* Published jobs
* Total applications
* Shortlisted applications
* Interview-stage applications
* Selected applications
* Rejected applications
* Pending offers
* Accepted offers
* Declined offers
* Total placements
* Pending joining
* Joined candidates
* Not-joined candidates
* Placement join rate

---

## 🔄 Employment Follow-up & Retention

The latest Careers-08 implementation extends placement tracking beyond joining.

Post-placement follow-ups are supported at:

* **30 days**
* **90 days**
* **180 days**

Employers and NCCT administrators can record employment status and feedback, while trainees can view follow-up information for their own placements.

This enables the ecosystem to move beyond simply measuring **placement** and towards understanding **employment continuity and retention**.

---

# 🔐 Role-Based Access

The system supports role-based workflows for major stakeholders.

| Role              | Primary Responsibilities                          |
| ----------------- | ------------------------------------------------- |
| `NCCT_ADMIN`      | Platform administration, monitoring and analytics |
| `INSTITUTE_ADMIN` | Institution and training management               |
| `TRAINER`         | Training and learning activities                  |
| `TRAINEE`         | Learning, skills and employment                   |
| `EMPLOYER`        | Jobs, applications, interviews and placements     |

Authorization is enforced at the backend API level rather than relying only on frontend navigation.

---

# 🏗️ System Architecture

```text
                    ┌───────────────────────┐
                    │      CoOpSphere       │
                    │   Cooperative Portal  │
                    └───────────┬───────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                │
        ┌───────▼────────┐              ┌────────▼────────┐
        │ React Frontend │              │ FastAPI Backend │
        │   Vite + TS    │              │   REST APIs     │
        └───────┬────────┘              └────────┬────────┘
                │                                │
                │                       ┌────────▼────────┐
                │                       │ Business Modules│
                │                       │                 │
                │                       │ Auth            │
                │                       │ Users           │
                │                       │ Institutions    │
                │                       │ Training ERP    │
                │                       │ LMS             │
                │                       │ Attendance      │
                │                       │ Skills          │
                │                       │ Credentials     │
                │                       │ Careers         │
                │                       │ Intelligence    │
                │                       │ Dashboard       │
                │                       └────────┬────────┘
                │                                │
                │                       ┌────────▼────────┐
                └──────────────────────►│  PostgreSQL     │
                                        │  + Alembic      │
                                        └─────────────────┘
```

---

# 🛠️ Technology Stack

### Frontend

* React
* TypeScript
* Vite
* React Router
* Axios
* Recharts
* Zod
* HTML5 QR Code

The current frontend package is configured around React/Vite with TypeScript, Axios, React Router, Recharts, Zod and QR-code support.

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic Settings
* Alembic
* Uvicorn
* JWT authentication
* PostgreSQL driver

The backend currently uses FastAPI 0.115.6, SQLAlchemy 2.x, Psycopg 3.x, Alembic, Pydantic Settings and JWT-related packages.

### Database

**PostgreSQL**

Database schema evolution is managed through **Alembic migrations**.

---

# 📂 Project Structure

```text
CoOpSphere/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── institutions/
│   │   ├── training/
│   │   ├── attendance/
│   │   ├── lms/
│   │   ├── credentials/
│   │   ├── skills/
│   │   ├── careers/
│   │   ├── intelligence/
│   │   ├── dashboard/
│   │   ├── notifications/
│   │   └── core/
│   │
│   ├── alembic/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.*
│
├── database/
│
├── docs/
│   └── careers-08.md
│
├── scripts/
│
├── SETUP.md
└── README.md
```

The repository currently separates backend, database, documentation, frontend and scripts into dedicated directories.

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/dhanusiyasri/CoOpSphere.git
cd CoOpSphere
```

## 2. Configure PostgreSQL

Create a PostgreSQL database:

```text
ncct_db
```

The default development configuration expects:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/ncct_db
```

The repository provides `.env.example` for backend configuration.

---

## 3. Backend Setup

```bash
cd backend
```

Create and activate a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```bash
cp .env.example .env
```

Update the database credentials and JWT secret as required.

---

## 4. Run Database Migrations

```bash
alembic upgrade head
```

Alembic is used by the project to apply database schema migrations.

---

## 5. Start Backend

```bash
uvicorn app.main:app --port 8000
```

For development with auto-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

The FastAPI application exposes system root and health endpoints and registers modules under `/api/v1`.

---

## 6. Start Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

The repository's setup instructions use Vite for the frontend and FastAPI on port 8000 for the backend.

---

# 🔗 API Modules

The backend currently exposes modules for:

```text
/api/v1/auth
/api/v1/users
/api/v1/institutions
/api/v1/training
/api/v1/attendance
/api/v1/lms
/api/v1/credentials
/api/v1/careers
/api/v1/intelligence
/api/v1/dashboard
/api/v1/skills
/api/v1/notifications
```

Additional training scheduling, logistics, evaluation, skill passport and skill recommendation routers are also registered in the application.

---

# 🤖 AI & Intelligence Roadmap

The platform is designed to evolve into an AI-enabled cooperative capacity-building ecosystem.

Planned capabilities include:

### 🧠 Skill Intelligence

Map:

```text
Courses → Learning Objectives → Assessments → Skills
```

### 🎯 Skill Gap Analysis

Identify gaps between:

```text
Current Skills
      ↓
Target Career / Role
      ↓
Required Skills
      ↓
Skill Gap
      ↓
Recommended Training
```

### 💬 AI Career Counselling

An AI assistant can help learners explore career pathways based on:

* Skills
* Training history
* Qualifications
* Interests
* Career goals
* Available opportunities

### 🔎 Intelligent Job Matching

Match learners with employment opportunities using:

* Required skills
* Qualifications
* Experience
* Location
* Eligibility
* Semantic skill similarity

### 📊 Training Intelligence

Use training and employment data to support decisions around:

* What skills are in demand?
* What training should be offered?
* Where is training required?
* Which learner groups need additional capacity building?
* Which training programmes are associated with better employment outcomes?

---

# 🔮 Future Enhancements

* 🤖 AI-powered personalized learning
* 🧠 Advanced skill-gap analysis
* 💬 AI career counselling
* 🔗 Skill-based job matching
* 📜 Digital skill passport
* ✅ Certificate verification
* 📷 QR / face-based attendance
* 🌐 Multilingual learning
* 📱 Offline-first learning
* 📊 Advanced institutional analytics
* 🏢 Expanded employer ecosystem
* 📈 Long-term employment and retention analytics
* 🔌 Integration with relevant external government and employment platforms

---

# 🎯 Project Impact

CoOpSphere aims to create a measurable digital journey:

```text
                    TRAINING
                       │
                       ▼
                    LEARNING
                       │
                       ▼
                    SKILLS
                       │
                       ▼
                  CREDENTIALS
                       │
                       ▼
                CAREER GUIDANCE
                       │
                       ▼
                 JOB MATCHING
                       │
                       ▼
                  EMPLOYMENT
                       │
                       ▼
             PLACEMENT FOLLOW-UP
                       │
                       ▼
                RETENTION DATA
                       │
                       ▼
             TRAINING INTELLIGENCE
                       │
                       └──────────────► Better Future Training
```

This transforms the platform from a simple training-management system into a **continuous capacity-building and employment ecosystem**.

---

# 🏆 Smart India Hackathon

**Problem Statement:** 26087
**Title:** AI & LMS - Enabled Cooperative Capacity Building, ERP & Employment Ecosystem

**Organization:** National Council for Cooperative Training (NCCT)

**Project:** CoOpSphere

---

# 👥 Team

**CoOpSphere Team**

Built for **Smart India Hackathon** with the objective of creating a unified digital ecosystem for cooperative capacity building, skill development, and employment.

---

# 📌 Project Status

**Current Status: SIH Prototype / Active Development**

The current repository contains implemented training, LMS, skills, career, employment, placement analytics, and post-placement follow-up components. Further AI-driven intelligence, advanced matching, multilingual support, offline capabilities, and ecosystem integrations are part of the planned evolution of the platform.

---

# 📄 License

This project is currently developed as a **Smart India Hackathon prototype**.

If the project is released for public open-source use, an appropriate open-source license should be added to the repository.

---

## 🌱 Vision

> **CoOpSphere aims to connect every learner's journey — from training and learning to skills, opportunities, employment, and long-term career growth.**

### **From Training → Skills → Opportunities → Employment → Empowerment**
