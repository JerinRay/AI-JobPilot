# AI-JobPilot
### Intelligent AI-Powered Job Discovery, Matching and Application Assistant

AI-JobPilot is a modular Python-based job assistance platform designed to
help candidates discover job opportunities, analyze job descriptions,
evaluate candidate-job compatibility, prepare tailored resumes and cover
letters, and track application progress.

The project combines job discovery, NLP-based job analysis, recommendation
logic, document generation, application workflow preparation, and a
Streamlit dashboard.

---

## Features

### 1. Resume Intelligence
- Resume PDF parsing and information extraction.
- Candidate profile loading and validation.
- Resume content tailoring based on job requirements.
- ATS-friendly DOCX and PDF resume generation.

### 2. Job Discovery
- Job discovery through the Arbeitnow job API.
- Job data ingestion and database storage.
- Duplicate job handling.
- Structured job information processing.

### 3. Job Description Analysis
- Job description parsing.
- Skill and requirement extraction.
- Candidate-to-job requirement comparison.
- Job suitability analysis and ranking.

### 4. Intelligent Recommendations
- Job matching and ranking.
- Skill match analysis.
- Recommendation generation.
- Manual verification indicators.

### 5. Application Preparation
- Job-specific cover letter generation.
- Application data preparation.
- Application form inspection.
- Application field mapping.
- Application safety validation.

### 6. Application Tracking
- Application status management.
- Application history tracking.
- Failure and retry information.
- Application statistics.

### 7. Interactive Dashboard
- Streamlit-based dashboard.
- Job recommendation overview.
- Application status metrics.
- Job recommendation analysis.
- Application tracking and history.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Frontend | Streamlit |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Database | SQLite, SQLAlchemy |
| Job Discovery | Requests, BeautifulSoup |
| Resume Processing | pypdf |
| Document Generation | python-docx, ReportLab |
| Configuration | python-dotenv |
| API Framework | FastAPI |

---

## Project Structure

```text
AI-JobPilot/
├── config/
├── database/
│   ├── db.py
│   ├── init_db.py
│   └── job_repository.py
├── frontend/
│   ├── app.py
│   └── style.css
├── src/
│   ├── application_agent/
│   ├── job_discovery/
│   ├── job_matching/
│   ├── recommendation_engine/
│   ├── resume_intelligence/
│   ├── tracking/
│   └── profile_loader.py
├── tests/
├── data/
├── outputs/
├── docs/
├── scripts/
├── requirements.txt
├── .gitignore
└── README.md
git clone YOUR_GITHUB_REPOSITORY_URL
cd AI-JobPilot
