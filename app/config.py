import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_str(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


@dataclass(frozen=True)
class Settings:
    app_name: str = _env_str("APP_NAME", "CareerBuilder Clone Backend")
    app_version: str = _env_str("APP_VERSION", "1.0.0")
    app_description: str = _env_str(
        "APP_DESCRIPTION",
        "Backend-only CareerBuilder clone with USAJOBS + RSS ingestion.",
    )

    mongodb_uri: str = _env_str("MONGODB_URI", "")
    mongodb_db_name: str = _env_str("MONGODB_DB_NAME", "careerbuilder_clone_db")

    usajobs_base_url: str = _env_str("USAJOBS_BASE_URL", "https://data.usajobs.gov/api/search")
    usajobs_api_host: str = _env_str("USAJOBS_API_HOST", "data.usajobs.gov")
    usajobs_user_agent: str = _env_str("USAJOBS_USER_AGENT", "")
    usajobs_api_key: str = _env_str("USAJOBS_API_KEY", "")
    usajobs_results_per_page: int = int(_env_str("USAJOBS_RESULTS_PER_PAGE", "25"))
    usajobs_keyword: str = _env_str("USAJOBS_KEYWORD", "software engineer")
    usajobs_location: str = _env_str("USAJOBS_LOCATION", "")

    rss_feed_url: str = _env_str(
        "RSS_FEED_URL",
        "https://remotive.com/remote-jobs/feed",
    )

    serpapi_base_url: str = _env_str("SERPAPI_BASE_URL", "https://serpapi.com/search.json")
    serpapi_engine: str = _env_str("SERPAPI_ENGINE", "google_jobs")
    serpapi_api_key: str = _env_str("SERPAPI_API_KEY", "")
    serpapi_location: str = _env_str("SERPAPI_LOCATION", "United States")
    serpapi_keywords: str = _env_str(
        "SERPAPI_KEYWORDS",
        "software engineer,data analyst,project manager,operations specialist,business analyst",
    )

    jwt_secret_key: str = _env_str("JWT_SECRET_KEY", "")
    jwt_algorithm: str = _env_str("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(_env_str("JWT_EXPIRE_MINUTES", "60"))

    fetch_interval_hours: int = int(_env_str("FETCH_INTERVAL_HOURS", "6"))


settings = Settings()
