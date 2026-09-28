# FashionHub

A full-stack fashion e-commerce project — Flask + MongoDB backend, vanilla HTML/CSS/JS frontend. This is the starter scaffold from the project blueprint (Phases 1-4): folder structure, Flask app, MongoDB connection, and working authentication + product APIs.

## What's already working

- `backend/app.py` — Flask app factory, connects to MongoDB, registers routes
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`
- `GET /api/products`, `GET /api/products/<id>`, `POST/PUT/DELETE /api/products/<id>`
- `frontend/index.html` — homepage that fetches and displays products from the API

## What you still need to build

Following the blueprint's roadmap: wishlist, cart, orders and reviews routes (Phase 7-8), admin-only access control on the product write routes (Phase 9), and the remaining frontend pages (product details, cart, checkout, login/register forms, admin panel).

## Run it locally (without Docker)

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cd ..
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
# then edit .env and paste your MongoDB Atlas connection string

# 4. Run the Flask server
cd backend
python app.py
```

The API will run at `http://localhost:5000`. Check `http://localhost:5000/api/health` to confirm it's connected to MongoDB.

Open `frontend/index.html` directly in your browser (or serve it with VS Code's "Live Server" extension) to see the homepage call the API.

## Run it with Docker

```bash
docker-compose up --build
```

This builds the backend image and runs it on port 5000, using the same `.env` file.

## Project structure

```
fashion-store/
├── frontend/          HTML, CSS, JS
├── backend/
│   ├── app.py         Flask app factory
│   ├── config.py      Reads secrets from .env
│   ├── routes/        One blueprint per feature (auth, products, ...)
│   ├── models/        Data-shape helpers (MongoDB is schema-less)
│   ├── services/      Reusable business logic
│   └── utils/         Small shared helpers
├── admin/             Admin panel pages (build in Phase 9)
├── tests/             Backend/frontend tests (Phase 10)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
