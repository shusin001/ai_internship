# AI-Powered CareerBuilder Platform

An intelligent job board and career advancement platform that dynamically ingests job listings from multiple sources, analyzes user resumes using AI/ML, and provides personalized job recommendations and skills gap analysis.

## 🎯 Features

### Core AI & Matching Functionality
- **Advanced Resume Parsing**: Extracts skills, experience, and key information from PDF resumes using PyMuPDF and spaCy.
- **AI-Based Recommendation Engine**: Matches candidate profiles against thousands of job listings using TF-IDF and Cosine Similarity, scoring each job for relevance.
- **Generative AI Gap Analysis**: Leverages Google Gemini to analyze gaps between user skills and job requirements, providing customized learning roadmaps and free resource links.

### Data Ingestion & Management
- **Automated Job Sourcing**: Scheduled background tasks to fetch latest opportunities from USAJOBS and RSS feeds.
- **Dynamic SerpAPI Injection**: Augments job listings dynamically for specific users by fetching resume-aligned jobs directly from Google Jobs.
- **Intelligent Deduplication**: Ensures clean data via MongoDB unique indexing constraints across source, company, title, and location.

### Web Interface
- **Modern React Dashboard**: Built with Next-generation frontend tooling (Vite, React 18, Tailwind CSS) for a lightning-fast user experience.
- **Analytics View**: Real-time insights into system health, top locations, top companies, and jobs-by-source.
- **Job Discovery & Saved Jobs**: Intuitive search interface to browse, filter, and save matched jobs.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB Atlas Account
- API Keys: USAJOBS (Optional), Google Gemini (Optional), SerpAPI (Optional)

### Installation

1. **Clone/Navigate to the project directory**:
```bash
cd "New project"
```

2. **Backend Setup**:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MONGODB_URI and other keys
```

3. **Frontend Setup**:
```bash
cd frontend
npm install
```

### Running the Application

1. **Start the Backend Server**:
```bash
# From the project root with the virtual environment activated
uvicorn app.main:app --reload
```
The API and Swagger UI will be accessible at `http://127.0.0.1:8000/docs`.

2. **Start the Frontend Development Server**:
```bash
# From the frontend directory
npm run dev
```
Access the web application via the URL provided by Vite (usually `http://localhost:5173`).

## 🏗️ Project Structure

```text
New project/
│
├── app/                        # Backend API and Machine Learning core
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # MongoDB Atlas connection handling
│   ├── routes/                 # REST API controllers (jobs, users, analytics)
│   ├── models/                 # Database schema definitions
│   ├── schemas/                # Pydantic validation schemas
│   ├── services/               # Job ingestion services (USAJOBS, RSS)
│   ├── resume_service/         # NLP, ML recommenders, and resume parsing
│   ├── guidance_service/       # AI resume gap analysis and learning roadmaps
│   ├── scraping_service/       # Dynamic SerpAPI job injection
│   └── scheduler/              # APScheduler configuration for background tasks
│
├── frontend/                   # Web interface
│   ├── src/                    # React components, pages, and API clients
│   ├── package.json            # Node.js dependencies
│   ├── tailwind.config.js      # Utility-first CSS configuration
│   └── vite.config.js          # Build tool configuration
│
└── requirements.txt            # Python dependencies
```

## 💡 How It Works

### The AI Matching Engine

The recommendation pipeline evaluates candidates based on parsed context rather than simple keyword matching:

1. **Information Extraction**: `regex` and `spaCy` NLP models extract a unified skill vector and estimate years of experience from unstructured PDF data.
2. **Feature Vectorization**: User skill arrays and job descriptions are transformed into vectors via `scikit-learn`'s `TfidfVectorizer`.
3. **Similarity Scoring**: Uses Cosine Similarity to score matches. The ranking normalizes scores across multiple candidate vectors.
4. **LLM Refinement (Optional)**: Can send the top matched jobs to Gemini to provide a conversational `match_note` explaining exactly *why* a job is a good fit.

### Data Flow

1. **Data Ingestion**: Jobs are pulled from APIs/RSS and inserted into MongoDB Atlas.
2. **Profile Generation**: Candidates upload their resume during Registration. The profile is permanently stored and linked to their account.
3. **Continuous Matching**: Whenever candidates visit their dashboard, the system processes existing jobs against their parsed profile to deliver top recommendations instantly.

## 📊 Features Demonstration

### Resume Gap Analysis
- Upload a resume and select a target job.
- Receive categorized missing skills (e.g., "Hard Skills", "Tools", "Soft Skills").
- Get actionable, step-by-step strategies to acquire these specific missing skills.

### Analytics Dashboard
- View total jobs processed and currently active.
- Track source distribution (e.g., USAJOBS 45%, RSS 35%, SerpAPI 20%).
- View geographical hot spots for hiring.

## 🔧 Configuration

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Connection String | Yes |
| `JWT_SECRET_KEY` | Secret for Passlib / JWT generation | Yes |
| `USAJOBS_API_KEY` | Token for standard job ingestion | No |
| `USAJOBS_USER_AGENT`| Email for USAJOBS headers | No |
| `SERPAPI_API_KEY` | For dynamic job scraping & injection | No |
| `GEMINI_API_KEY` | Enable generative feedback & guidance | No |
| `GUIDANCE_LLM_ENABLED`| Set to `true` to use Gemini API | No |

## 🎨 User Interface

The frontend provides an intuitive interface with:
- **Responsive Design**: Flawless experience across desktop, tablet, and mobile, utilizing Tailwind CSS.
- **Modern Routing**: Fast SPA navigation powered by React Router.
- **Component-Driven UI**: Modular, reusable UI components for candidates and jobs.
- **Axios-Based API Layer**: Robust and interceptor-ready fetch mechanisms to securely handle JWT tokens.

## 📈 Performance

- **Non-blocking Architecture**: FastAPI combined with asynchronous Motor (MongoDB client) ensures thousands of concurrent requests are handled smoothly.
- **Efficient Indexing**: Uses MongoDB compound keys `(title, company, location, source)` and text indexing for ultra-fast full-text searches.
- **Scheduled Workers**: Memory-intensive job ingestion tasks are offloaded to background schedulers.

## 🔐 Future Enhancements

- **OAuth2 Social Logins**: Sign in with Google, GitHub, or LinkedIn.
- **Advanced Job Alerting**: Email notifications (integrated with SendGrid/AWS SES) when highly relevant jobs are discovered by background schedulers.
- **Recruiter Portal**: Separate authenticated flows for recruiters to post jobs manually.
- **Containerization**: Dockerize the entire application (`docker-compose.yml`) for seamless one-click production deployments.
- **Automated Testing Suite**: Expand `pytest` coverage for CI/CD pipelines.

## 🤝 Contributing

Contributions are welcome! Please ensure that you:
1. Open an issue first to discuss the proposed change.
2. Keep the backend fully testable via Swagger.
3. Adhere to the existing code formatting (`black` for Python, `prettier` for frontend).

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 👥 Contact

For questions or support regarding this system, please open an issue or contact the project maintainers.
