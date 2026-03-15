# Golf Scoring App - Deployment Guide

## Architecture
- **Backend**: Python FastAPI + PostgreSQL (hosted on Railway)
- **Frontend**: React + Vite (can be hosted on Railway or Vercel/Netlify)

## Deploy to Railway

### 1. Backend
1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) and create a new project
3. Click "New Service" → "GitHub Repo" → select your repo
4. Set the **Root Directory** to `backend`
5. Add a **PostgreSQL** plugin to your project (Railway will auto-set `DATABASE_URL`)
6. Add environment variable: `FRONTEND_URL` = your frontend URL
7. Deploy! The API will be available at your Railway-provided URL

### 2. Frontend
1. Add another service in the same Railway project
2. Point it to the same repo, set **Root Directory** to `frontend`
3. Add environment variable: `VITE_API_URL` = your backend Railway URL (e.g., `https://golf-api-production.up.railway.app`)
4. Deploy!

### 3. Initialize Data
After both services are running:
```bash
curl -X POST https://YOUR-BACKEND-URL/api/seed/all
```
This seeds North Hants Golf Club course data.

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt

# Start a local PostgreSQL or use Docker:
docker run -d --name golf-db -p 5432:5432 -e POSTGRES_DB=golf_app -e POSTGRES_PASSWORD=postgres postgres:16

# Run the API
uvicorn main:app --reload
```
API docs available at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend at http://localhost:5173 (auto-proxies /api to backend)

## Game Formats Supported
- Strokeplay, Stableford
- Better Ball (Fourball & Stableford)
- Foursomes (Alternate Shot)
- Combined Team Stableford
- Texas Scramble, Ambrose
- Wolfie, Perch, Skins
- Match Play
- Greensomes, Chapman/Pinehurst
- Flags

## Key Features
- **Shareable game codes**: Anyone with the code can view/score the game
- **Live leaderboards**: Auto-refresh every 15 seconds
- **Multi-format scoring**: Automatic handicap-adjusted scoring for all formats
- **League system**: Order of Merit with best-of-N scoring, attestor requirements
- **Mobile-friendly**: Responsive design for on-course scoring
