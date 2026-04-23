# Frontend (React + Vite + Tailwind)

This frontend is fully isolated under `frontend/` and consumes the existing backend APIs without modifying backend routes.

## Setup

1. Create env file:
```bash
cp .env.example .env
```

2. Install dependencies:
```bash
npm install
```

3. Run dev server:
```bash
npm run dev
```

Default UI URL: `http://127.0.0.1:5173`

## Environment

- `VITE_API_BASE_URL` -> backend base URL (default: `http://127.0.0.1:8000`)

## Pages

- `/` Landing
- `/register` Register (multipart/form-data with optional PDF upload)
- `/login` Login
- `/dashboard` Recommended jobs
- `/guidance/:jobId` Guidance report
- `/profile` User profile + recommendations

## API Endpoints Used

- `POST /users/register` (multipart/form-data)
- `POST /users/login`
- `GET /resume-service/recommendations/{user_id}`
- `GET /resume-service/profile/{user_id}`
- `GET /jobs/{job_id}`
- `POST /guidance/analyze`

## Notes

- Auth token is stored in `localStorage`.
- User ID is extracted from JWT `sub` claim.
- All frontend code lives inside this folder for independent debugging.
