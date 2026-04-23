# Configuration Deep Dive

This document explains the three core files that **configure, connect, and boot** the entire backend.

---

## Files Covered

| # | File | Role |
|---|------|------|
| 1 | `app/config.py` | Reads all settings from environment variables |
| 2 | `app/database.py` | Opens/closes the MongoDB connection and creates DB indexes |
| 3 | `app/main.py` | Assembles the FastAPI app, wires all routers, manages startup/shutdown |

---

## 1. `app/config.py` — Application Settings

**Think of it like this:** Imagine a restaurant chain where every branch needs the supplier's phone number. Instead of printing it in every branch's manual (hardcoded), you put it on ONE master notice board at HQ. Every branch calls HQ to get the number. That notice board is `config.py`. One change here → the whole app updates automatically.

```python
import os
```
> **Line 1**: Imports Python's built-in `os` module. The only thing used from it is `os.getenv()` — which reads values from environment variables at runtime.

```python
from dataclasses import dataclass
```
> **Line 2**: Imports the `@dataclass` decorator.
>
> **Why?** Normally if you write a class to store data, you'd have to manually write `__init__`, `__repr__`, and `__eq__` yourself — that's boilerplate (repetitive, boring, zero-logic code you're forced to write). `@dataclass` writes all three automatically for you.
>
> - **`__init__`** → How the object gets created with values. This is the only truly required one.
> - **`__repr__`** → What happens when you `print(settings)`. Without it, you'd see a useless memory address like `<Settings object at 0x10f3a>`. With it, you see all 15 fields at once.
> - **`__eq__`** → Lets you compare two Settings objects with `==`. Without it, Python compares by RAM address (always `False`), not by actual values.
>
> You don't *need* `__repr__` and `__eq__` — but they're given **for free as a bonus**. Think of it as ordering a burger and getting fries + drink in a combo at no extra cost.

```python
from dotenv import load_dotenv
```
> **Line 4**: Imports `load_dotenv` from the `python-dotenv` package. This function reads your `.env` file from disk and loads every `KEY=VALUE` pair into the program's memory.

```python
load_dotenv()
```
> **Line 6**: Actually triggers the reading of the `.env` file. **Must run before `Settings` is created**, otherwise `os.getenv()` won't find anything.

---

```python
def _env_str(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()
```
> **Lines 9–10**: A small private helper (the `_` prefix means "internal use only").
> - `os.getenv(key, default)` → Give me the env variable named `key`. If it doesn't exist, return `default`.
> - `.strip()` → Removes accidental spaces/newlines that might be in the `.env` file, preventing invisible bugs.
> - `-> str` → Type hint. Doesn't enforce anything at runtime, just documents that this always returns a string.

---

```python
@dataclass(frozen=True)
class Settings:
```
> **Lines 13–14**: Defines the `Settings` class.
> - `@dataclass` → Writes `__init__`, `__repr__`, `__eq__` automatically.
> - `frozen=True` → Makes the object **immutable**. Once created, no value can be changed. Crucial for settings — you never want a service accidentally overwriting a config value while the app is running.

```python
    app_name: str = _env_str("APP_NAME", "CareerBuilder Clone Backend")
    app_version: str = _env_str("APP_VERSION", "1.0.0")
    app_description: str = _env_str("APP_DESCRIPTION", "Backend-only CareerBuilder clone...")
```
> **Lines 15–20**: App metadata directly shown in the Swagger UI (`/docs`) as the title and description.

```python
    mongodb_uri: str = _env_str("MONGODB_URI", "")
    mongodb_db_name: str = _env_str("MONGODB_DB_NAME", "careerbuilder_clone_db")
```
> **Lines 22–23**: MongoDB connection info.
> - `mongodb_uri`: The full Atlas connection string. Defaults to empty — `database.py` will crash with a clear error at startup if this is missing (intentional fail-fast behavior).
> - `mongodb_db_name`: The name of the database inside Atlas.

```python
    usajobs_base_url: str = _env_str("USAJOBS_BASE_URL", "https://data.usajobs.gov/api/search")
    usajobs_api_host: str = _env_str("USAJOBS_API_HOST", "data.usajobs.gov")
    usajobs_user_agent: str = _env_str("USAJOBS_USER_AGENT", "")
    usajobs_api_key: str = _env_str("USAJOBS_API_KEY", "")
    usajobs_results_per_page: int = int(_env_str("USAJOBS_RESULTS_PER_PAGE", "25"))
    usajobs_keyword: str = _env_str("USAJOBS_KEYWORD", "software engineer")
    usajobs_location: str = _env_str("USAJOBS_LOCATION", "")
```
> **Lines 25–31**: Config for the USAJOBS Federal Job API.
> - `usajobs_user_agent`: USAJOBS requires your email as the `User-Agent` header — it's how they identify callers.
> - `usajobs_results_per_page`: **Note the `int(...)` wrapper.** `_env_str` always returns a string. Wrapping with `int()` converts it so it can be used in math/pagination logic.
> - `usajobs_location`: Empty by default = nationwide results.

```python
    rss_feed_url: str = _env_str("RSS_FEED_URL", "https://remotive.com/remote-jobs/feed")
```
> **Lines 33–36**: The RSS feed URL that `rss_service.py` polls for job listings. Defaults to Remotive's remote jobs feed.

```python
    serpapi_base_url: str = _env_str("SERPAPI_BASE_URL", "https://serpapi.com/search.json")
    serpapi_engine: str = _env_str("SERPAPI_ENGINE", "google_jobs")
    serpapi_api_key: str = _env_str("SERPAPI_API_KEY", "")
    serpapi_location: str = _env_str("SERPAPI_LOCATION", "United States")
    serpapi_keywords: str = _env_str("SERPAPI_KEYWORDS", "software engineer,data analyst,...")
```
> **Lines 38–45**: Config for SerpAPI (Google Jobs dynamic scraping).
> - `serpapi_engine`: Tells SerpAPI to emulate Google Jobs specifically.
> - `serpapi_keywords`: A comma-separated list of job titles to search when dynamically injecting jobs for a user.

```python
    jwt_secret_key: str = _env_str("JWT_SECRET_KEY", "")
    jwt_algorithm: str = _env_str("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(_env_str("JWT_EXPIRE_MINUTES", "60"))
```
> **Lines 47–49**: Security settings for login tokens (JWT = JSON Web Token).
> - `jwt_secret_key`: The private password used to **sign** tokens. If this is leaked, an attacker can forge any user's login.
> - `jwt_algorithm`: `"HS256"` = HMAC-SHA256. Symmetric — same key signs and verifies.
> - `jwt_expire_minutes`: How long a login stays valid (default: 60 minutes).

```python
    fetch_interval_hours: int = int(_env_str("FETCH_INTERVAL_HOURS", "6"))
```
> **Line 51**: How often the background scheduler re-fetches jobs from USAJOBS and RSS. Default: every 6 hours.

```python
settings = Settings()
```
> **Line 54**: Creates the **one and only** `Settings` instance for the whole app. Every other file imports this single object — not the class. This is the **Singleton pattern**: one remote control for the entire application.

---

## 2. `app/database.py` — Database Connection & Indexing

This file's job: open the MongoDB door at startup, close it at shutdown, and set up the filing system (indexes) so searches are fast.

```python
from typing import Optional
```
> **Line 1**: `Optional[X]` means a variable can be either type `X` or `None`. Used here to say the `client` variable starts as `None` and later becomes a real connection object.

```python
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
```
> **Line 3**: Imports Motor — the **async** MongoDB driver.
> - **Why async?** FastAPI handles thousands of requests at once. A regular (synchronous) DB driver would block and freeze while waiting for a database response. Motor is non-blocking — it waits for MongoDB in the background while the server handles other requests.
> - `AsyncIOMotorClient` → The actual connection to Atlas (like opening a phone line).
> - `AsyncIOMotorDatabase` → The specific database inside Atlas you talk to.

```python
from pymongo import ASCENDING, DESCENDING, TEXT
```
> **Line 4**: Constants for index direction.
> - `ASCENDING` = `1` → A to Z / 0 to 9
> - `DESCENDING` = `-1` → Z to A / 9 to 0
> - `TEXT` → Special mode for full-text search

```python
from app.config import settings
```
> **Line 6**: Gets the `settings` singleton from `config.py` to read the MongoDB URI and DB name.

```python
client: Optional[AsyncIOMotorClient] = None
```
> **Line 8**: A **module-level global variable** that holds the connection. Starts as `None` because no connection exists yet when the file first loads.

---

```python
async def connect_to_mongo() -> None:
    global client
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured.")
    client = AsyncIOMotorClient(settings.mongodb_uri)
```
> **Lines 11–15**: Called once at startup.
> - `global client` → Tells Python we want to modify the module-level `client`, not create a new local variable.
> - The `if not settings.mongodb_uri` check → **Fail fast**: crash immediately with a clear message rather than letting the app run broken and fail mysteriously later.
> - `AsyncIOMotorClient(...)` → Opens the actual TCP connection pool to MongoDB Atlas.

```python
async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
    client = None
```
> **Lines 18–22**: Called once at shutdown. Gracefully closes all open connections and resets `client` to `None`.

```python
def get_database() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo first.")
    return client[settings.mongodb_db_name]
```
> **Lines 25–28**: A getter used by every route and service when they need to talk to the database.
> - Guard clause protects against being called before startup.
> - `client["careerbuilder_clone_db"]` → Dictionary-style access selects the specific database. MongoDB creates it automatically on the first write if it doesn't exist.

---

```python
async def init_indexes() -> None:
    db = get_database()
```
> **Lines 31–32**: Called once at startup after connecting. Gets the DB handle to create indexes on.

```python
    await db.jobs.create_index(
        [("title", ASCENDING), ("company", ASCENDING), ("location", ASCENDING), ("source", ASCENDING)],
        unique=True,
        name="unique_job_signature",
    )
```
> **Lines 34–38**: **The deduplication index.** A combination of title + company + location + source must be unique. MongoDB will silently reject any duplicate job insert — this is the entire deduplication mechanism for the ingestion pipeline. No code logic needed, the database enforces it.

```python
    await db.jobs.create_index([(("title", TEXT), ("description", TEXT)], name="text_search_idx")
```
> **Line 39**: **Full-text search index.** Enables smart search across title and description. Supports stemming — searching "engineering" also matches "engineer".

```python
    await db.jobs.create_index([("posted_date", DESCENDING)], name="posted_date_idx")
    await db.jobs.create_index([("source", ASCENDING)], name="source_idx")
    await db.jobs.create_index([("location", ASCENDING)], name="location_idx")
    await db.jobs.create_index([("company", ASCENDING)], name="company_idx")
```
> **Lines 40–43**: Speed indexes for common queries. Without these, MongoDB would scan every single document for each filter. With them, it jumps directly to matching documents.

```python
    await db.users.create_index([("email", ASCENDING)], unique=True, name="unique_user_email")
```
> **Line 45**: No two users can share an email. `unique=True` enforces this at the database level — even if the application code forgets to check.

```python
    await db.resume_profiles.create_index([("user_id", ASCENDING)], unique=True, name="unique_resume_user_id")
```
> **Line 46**: One user → one resume profile. Enforces the one-to-one relationship at the database level.

---

## 3. `app/main.py` — Application Entry Point

This is the file `uvicorn` runs. It's the **assembler** — it takes all the parts (routers, database, scheduler) and wires them into one working application.

```python
import asyncio
```
> **Line 1**: Python's async task manager. Needed to fire the first job ingestion as a background task at startup.

```python
import logging
```
> **Line 2**: Standard Python logging. Used for structured messages in the console (timestamps, severity levels, module names).

```python
from contextlib import asynccontextmanager
```
> **Line 3**: Converts an async generator function into a **context manager** — the modern FastAPI pattern for startup/shutdown logic. Think of it like a try/finally that wraps the entire app's life.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
```
> **Lines 5–6**:
> - `FastAPI` → The web server class. One instance = the entire API.
> - `CORSMiddleware` → A security layer. Without it, your React frontend (port 5173) can't call the API (port 8000). Browsers block cross-origin requests by default.

```python
import app.resume_service as resume_service
import app.guidance_service as guidance_service
import app.scraping_service as scraping_service
```
> **Lines 7–9**: Imported as full modules (not specific symbols) because we access the `.router` attribute off them on lines 58–60.

```python
from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, init_indexes
from app.routes.analytics import router as analytics_router
from app.routes.jobs import router as jobs_router
from app.routes.users import router as users_router
from app.scheduler.fetch_scheduler import run_ingestion_cycle, start_scheduler, stop_scheduler
```
> **Lines 11–16**: All the pieces being assembled. Routers aliased with `as` to avoid naming conflicts (all three would be called `router` otherwise).

---

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
```
> **Lines 18–22**: Sets up the logging format for the whole app.
> - `level=logging.INFO` → Shows INFO, WARNING, ERROR. Hides DEBUG (too noisy for production).
> - `format` → Defines what each log line looks like: `2026-03-30 11:00:00 | INFO | app.main | Application started`.
> - `logging.getLogger(__name__)` → Creates a logger named after this specific file (`app.main`). Best practice — each module gets its own named logger.

---

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    await init_indexes()
    start_scheduler()
    asyncio.create_task(run_ingestion_cycle())
    logger.info("Application started successfully.")
    try:
        yield
    finally:
        stop_scheduler()
        await close_mongo_connection()
        logger.info("Application shutdown complete.")
```
> **Lines 25–37**: The **lifespan manager** — controls what happens when the app boots and when it dies.
>
> Everything **before `yield`** = Startup. Everything in **`finally`** = Shutdown (runs even if the app crashes).
>
> **Startup order:**
> 1. Open MongoDB connection
> 2. Create all indexes
> 3. Start the background scheduler (every 6 hours)
> 4. `asyncio.create_task(run_ingestion_cycle())` → **Fire one immediate fetch right now** — don't wait 6 hours for the first tick
> 5. Log success
>
> **Shutdown order:**
> 1. Stop the scheduler
> 2. Close MongoDB connection
> 3. Log completion
>
> `_: FastAPI` → The underscore means "FastAPI passes the app instance here but we don't use it."

---

```python
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)
```
> **Lines 40–45**: Creates the FastAPI application.
> - Title/version/description pulled from `settings` → shown on Swagger UI automatically.
> - `lifespan=lifespan` → Registers our startup/shutdown logic above.

---

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
> **Lines 47–53**: Enables CORS so the React frontend can call this API.
> - `allow_origins=["*"]` → Any origin allowed. In production, lock this to your actual frontend domain.
> - `allow_credentials=False` → No cookies. Auth is handled via `Authorization` header (JWT), not cookies.
> - `allow_methods/headers=["*"]` → No restrictions on HTTP methods or headers.

---

```python
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(resume_service.router, prefix="/resume-service", tags=["Resume Service"])
app.include_router(guidance_service.router, prefix="/guidance", tags=["Guidance"])
app.include_router(scraping_service.router, prefix="/scraping-injection", tags=["Scraping Injection"])
```
> **Lines 55–60**: Wires all 6 routers (endpoint groups) into the app.
> - First 3 routers define their own URL prefixes inside their files.
> - Last 3 get their prefix added here (e.g., all routes in `guidance_service` now live under `/guidance/...`).
> - `tags` groups them visually in the Swagger UI.

---

```python
@app.get("/", tags=["Health"], summary="API health endpoint")
async def root() -> dict:
    return {"message": "ReCompass backend is running.", "docs": "/docs"}
```
> **Lines 63–68**: A simple `GET /` health check. Confirms the server is alive. Load balancers and monitoring tools ping this URL to check if the service is up and running.

---

*All three files work together: `config.py` provides values → `database.py` uses them to connect → `main.py` orchestrates everything at boot.*
