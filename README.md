# FashionHub

A full-stack fashion e-commerce project — Flask + MongoDB backend, vanilla HTML/CSS/JS frontend.

## Features

- Search products by name, brand, or type; filter by category, price, size, colour, brand, and stock; sort by newest, price, or name. Search/filter state is shareable in the URL.
- Product detail pages with size and colour choices.
- Cart quantity editing, variant-aware lines, stock validation, and a live cart count.
- Checkout rechecks stock and reserves inventory; cancelling an order restores it.
- Admin product catalog management, authentication, orders, wishlists, and reviews.
- Demo data seeding and an in-memory backend feature test.

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
# then edit .env:
# - replace <username> and <password> in MONGO_URI with your Atlas database user
# - keep /fashionhub in the URI, or set MONGO_DB_NAME to your preferred database
# - allow your IP address in Atlas Network Access

# 4. Run the Flask server
cd backend
python app.py
```

The API will run at `http://localhost:5000`. Check `http://localhost:5000/api/health` to confirm the MongoDB connection. It returns HTTP 503 if MongoDB is unreachable.

Open `frontend/index.html` directly in your browser (or use VS Code's "Live Server" extension) to use the storefront.

## Demo data and tests

From the project root, run `python tools/seed_data.py` to add or refresh the demo catalog, accounts, orders, and reviews. It preserves non-demo orders and reviews. Do not use `--reset` unless you intend to delete all products, carts, orders, reviews, and wishlists in the configured database.

Products from before inventory tracking that have no `stock` field show as sold out until stock is set in the admin product form or the demo seeder updates them.

The demo accounts are `admin@fashionhub.com / Admin@123` and `aisha@example.com / Customer@123`. Change these credentials before any public deployment.

To run the backend feature tests against an in-memory MongoDB, install the dev dependencies and run:

```bash
pip install -r backend/requirements-dev.txt
python tests/test_shop_features.py
```

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
