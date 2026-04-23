# User Point-of-View (POV) — Complete Data Flow

This document follows **exactly what happens** at every step a user takes — from opening the app for the first time, to getting AI-powered job recommendations. It covers both what the user sees and what the system does behind the scenes.

---

## The Full Journey at a Glance

```
Register → Login → Dashboard (AI Recommendations) → Search Jobs → Save Jobs → Gap Analysis
```

---

## Step 1: User Registers — `POST /users/register`

### What the user does:
- Opens the app, fills in `full_name`, `email`, `password`
- Optionally attaches their **PDF resume**
- Clicks Register

### What happens behind the scenes:

```
React Frontend
    │
    ├── Sends multipart/form-data request  (has to be multipart because of the file upload)
    │
    ▼
POST /users/register  (users.py → register_user)
    │
    ├── 1. Parses the form: extracts email, password, full_name, resume file
    │
    ├── 2. Validates email format and password (via Pydantic UserRegisterRequest)
    │        └── If invalid → 422 Unprocessable Entity returned immediately
    │
    ├── 3. Normalizes email: lowercased + stripped  (so "USER@Mail.COM" = "user@mail.com")
    │
    ├── 4. Hashes the password using passlib bcrypt
    │        └── "xyz123" → "$2b$12$abcde..."  (raw password NEVER stored)
    │
    ├── 5. Builds a user document and inserts into MongoDB `users` collection
    │        └── If email already exists → DuplicateKeyError → 409 Conflict returned
    │
    ├── 6. If resume PDF was uploaded:
    │        └── Reads the file bytes → adds safe_process_resume() as a BACKGROUND TASK
    │            (does not block the response — user gets registered instantly, resume processed in background)
    │
    └── 7. Returns UserResponse (user_id, email, full_name, saved_jobs_count)
```

### Resume Background Processing (runs after response is sent):

```
safe_process_resume() [background task]
    │
    ├── PyMuPDF extracts plain text from the PDF
    │
    ├── section_detector splits text into: Skills / Experience / Education
    │
    ├── spaCy NLP + skills_dictionary.json identifies hard skills
    │        e.g., ["Python", "React", "MongoDB", "FastAPI"]
    │
    ├── experience_estimator counts years of experience from dates
    │
    └── Stores ResumeProfile in MongoDB `resume_profiles` collection
             └── Linked to user by user_id (unique index ensures 1 profile per user)
```

> **Key insight:** The user sees "Registered successfully!" in under 1 second. The resume AI processing happens quietly in the background — they don't wait for it.

---

## Step 2: User Logs In — `POST /users/login`

### What the user does:
- Enters email + password
- Clicks Login

### What happens behind the scenes:

```
POST /users/login  (users.py → login_user)
    │
    ├── 1. Looks up user by email in MongoDB
    │        └── If not found → 401 Unauthorized  (vague on purpose to prevent email enumeration)
    │
    ├── 2. Verifies password against the stored bcrypt hash
    │        └── If wrong → 401 Unauthorized
    │
    ├── 3. Creates a JWT token:
    │        payload = { "user_id": "abc123" }
    │        signed with jwt_secret_key using HS256
    │        expires in 60 minutes
    │
    └── 4. Returns { "access_token": "eyJhbGci..." }
```

### On the frontend:
- React stores the JWT token (in memory or localStorage)
- Every subsequent request includes it in the header:
  ```
  Authorization: Bearer eyJhbGci...
  ```

---

## Step 3: User Views Dashboard — Recommendations

### What the user does:
- Lands on their dashboard after login
- Sees **Top Matched Jobs** without searching for anything

### What happens behind the scenes:

```
GET /resume-service/recommendations/{user_id}
    │
    ├── 1. Checks if recommendation cache exists in resume_profiles
    │        └── If cache exists and fresh → returns it immediately (no heavy computation)
    │
    ├── 2. If no cache:
    │        └── Loads resume_text and extracted_skills from the user's ResumeProfile
    │
    ├── 3. Pulls all jobs from MongoDB (up to 10,000)
    │
    ├── 4. For each job, computes 6 scoring signals:
    │
    │   ┌─────────────────────────────────────────────────────────────────┐
    │   │  Signal                  │  Weight │  What it measures          │
    │   │─────────────────────────│─────────│────────────────────────────│
    │   │  Cosine Similarity       │  40%    │  Text/semantic match        │
    │   │  Skill Overlap           │  25%    │  Exact skill matches        │
    │   │  Title-Skill Focus       │  15%    │  Skills mentioned in title  │
    │   │  Job-Skill Coverage      │  10%    │  % of job skills you have   │
    │   │  Role-Title Alignment    │  5%     │  Does title match your role  │
    │   │  Recency Score           │  5%     │  How fresh the job is        │
    │   └─────────────────────────────────────────────────────────────────┘
    │
    ├── 5. Applies Domain Alignment Factor (penalty multiplier)
    │        └── If you're a software engineer but job is "Social Worker" → score × 0.35
    │            Prevents completely irrelevant recommendations
    │
    ├── 6. Sorts all jobs by final_score (highest to lowest)
    │
    ├── 7. Saves TOP 10 results into recommendation_cache in MongoDB
    │
    └── 8. Returns top 10 jobs with:
             └── job_id, score, match_note
                 match_note example: "Ranked by semantic alignment 82%, skill overlap 74%..."
```

> **Key insight:** The heavy computation (scoring 10,000 jobs) runs once and is **cached**. The next time the user visits, it returns the cached result instantly.

---

## Step 4: User Searches Jobs — `GET /jobs`

### What the user does:
- Goes to the Job Search page
- Types a keyword (e.g., "backend engineer")
- Optionally filters by location, salary, employment type

### What happens behind the scenes:

```
GET /jobs?keyword=backend engineer&location=New York&page=1&limit=10
    │
    ├── 1. Builds a MongoDB query:
    │        └── keyword → uses $text index (full-text search, handles "engineering" = "engineer")
    │            location, employment_type → exact filter match
    │            min_salary / max_salary → range filter
    │
    ├── 2. Counts total matching documents (for pagination)
    │
    ├── 3. Sorts by posted_date DESCENDING (newest first — uses index, very fast)
    │
    ├── 4. Applies pagination: skip (page-1) × limit, take `limit` docs
    │
    └── 5. Returns:
             └── List of jobs + total_count + page + limit
```

### User clicks on a specific job:

```
GET /jobs/{job_id}
    │
    └── Fetches full job document by _id from MongoDB
        └── Returns all fields including full description
```

---

## Step 5: User Saves a Job — `POST /jobs/{job_id}/save`

### What the user does:
- Sees a job they like
- Clicks the Bookmark/Save button

### What happens behind the scenes:

```
POST /jobs/{job_id}/save
    │
    ├── Header: Authorization: Bearer <token>
    │
    ├── 1. get_current_user() runs first (JWT verification):
    │        ├── Extracts token from Authorization header
    │        ├── Decodes & verifies JWT using jwt_secret_key
    │        ├── Extracts user_id from token payload
    │        └── Looks up user in MongoDB to confirm they still exist
    │            └── If expired or invalid → 401 Unauthorized
    │
    ├── 2. Calls save_job_for_user(user_id, job_id)
    │        └── MongoDB $addToSet operation:
    │            Adds job_id to user's saved_jobs array ONLY if not already there
    │            (prevents duplicates silently)
    │
    └── 3. Returns { "message": "Job saved successfully.", "job_id": "..." }
```

---

## Step 6: User Views Saved Jobs — `GET /users/{user_id}/saved-jobs`

### What the user does:
- Navigates to "My Saved Jobs" section

### What happens behind the scenes:

```
GET /users/{user_id}/saved-jobs
    │
    ├── 1. JWT verified → current user identified
    │
    ├── 2. Authorization check:
    │        └── current_user["_id"] must match the {user_id} in the URL
    │            If different → 403 Forbidden (you can't view someone else's saved jobs)
    │
    └── 3. Fetches all job documents from the user's saved_jobs list
             └── Returns complete job details for each saved job
```

---

## Step 7: Gap Analysis — `POST /guidance/analyze`

### What the user does:
- Finds a job they want but feel underqualified for
- Clicks "Analyze Gap"

### What happens behind the scenes:

```
POST /guidance/analyze
Body: { "user_id": "abc123", "job_id": "xyz789" }
    │
    ├── 1. Loads user's ResumeProfile (extracted skills, resume text)
    │
    ├── 2. Loads the target job's full description + required skills
    │
    ├── 3. Computes gap: job_required_skills - user_skills
    │        └── e.g., user has [Python, React] but job needs [Python, React, Kubernetes, Docker]
    │            Gap = [Kubernetes, Docker]
    │
    ├── 4. Categorises missing skills:
    │        └── Hard Skills / Tools / Soft Skills / Domain Knowledge
    │
    ├── 5. If GUIDANCE_LLM_ENABLED=true (Gemini active):
    │        ├── Sends the gap to Gemini API
    │        ├── Cap: max 3 Gemini calls per user per day
    │        └── Gemini returns: learning strategy + free resource links for each missing skill
    │
    └── 6. Returns:
             └── { gap_skills, categorised_missing, roadmap, strategy, resource_links }
```

---

## Step 8: Dynamic Job Injection — `POST /scraping-injection/inject/{user_id}`

### What happens (optional power feature):

```
POST /scraping-injection/inject/{user_id}
Body: { "max_results": 20, "refresh_recommendations": true }
    │
    ├── 1. Loads user's extracted skill keywords (e.g., ["Python", "FastAPI", "MongoDB"])
    │
    ├── 2. Calls SerpAPI Google Jobs with those skill keywords as the search query
    │
    ├── 3. Parses the Google Jobs results
    │
    ├── 4. Inserts only NEW jobs into the shared `jobs` collection
    │        └── Duplicate index silently rejects any already-existing jobs
    │
    ├── 5. If refresh_recommendations=true:
    │        └── Immediately re-runs the recommendation engine for this user
    │            with the newly injected jobs included
    │
    └── 6. Returns summary: { injected_count, skipped_duplicates }
```

---

## Complete System Flow Diagram

```
User Opens App
      │
      ▼
  REGISTER ──── Upload PDF ──► Background: NLP Processing ──► ResumeProfile saved in DB
      │
      ▼
   LOGIN ──────────────────────────────────────────────────► JWT Token issued
      │
      ▼
  DASHBOARD ──► GET /resume-service/recommendations
                    └── Score all jobs vs resume → cache top 10 → display
      │
      ▼
  JOB SEARCH ─► GET /jobs?keyword= → Full-text search + filters + pagination
      │
      ▼
  VIEW JOB ──► GET /jobs/{job_id} → Full job details
      │
      ▼
  SAVE JOB ──► POST /jobs/{job_id}/save → JWT verified → added to user's saved list
      │
      ▼
  GAP ANALYSIS ► POST /guidance/analyze → skills diff → Gemini roadmap + resources
      │
      ▼
  INJECT JOBS ─► POST /scraping-injection/inject → SerpAPI → new jobs → refresh recs
```

---

*Every protected endpoint (save job, saved jobs list, gap analysis, injection) verifies the JWT token first. If the token is missing, expired, or invalid — the request is rejected with 401 Unauthorized before any database operation runs.*
