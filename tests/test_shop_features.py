"""
End-to-end backend test for search/filters, cart rules, stock and checkout.
Uses an in-memory fake MongoDB, so it needs no Atlas connection and changes no real data.

    pip install mongomock
    python tests/test_shop_features.py
"""
import sys, os
os.environ.setdefault("FLASK_ENV", "development")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mongomock
from unittest import mock

client = mongomock.MongoClient()
db = client["fashionhub"]

import seed_data
seed_data.connect = lambda: db
sys.argv = ["seed_data.py"]
seed_data.main()
seed_data.main()   # run twice: must be idempotent
print("products", db.products.count_documents({}), "orders", db.orders.count_documents({}), "reviews", db.reviews.count_documents({}))
assert db.products.count_documents({}) == 30
assert min(p["stock"] for p in db.products.find()) >= 0

with mock.patch("pymongo.MongoClient", lambda *a, **k: client):
    import app as app_module
    app_module.MongoClient = lambda *a, **k: client
    app = app_module.create_app()
app.db = db
c = app.test_client()

def get(url, **kw): r = c.get(url, **kw); return r.status_code, r.get_json()

# ---- search / filter / sort
s, d = get("/api/products"); assert s == 200 and len(d) == 30
s, d = get("/api/products?search=denim"); print("search denim:", [p["name"] for p in d])
s, d = get("/api/products?search=(.*"); assert s == 200 and d == []     # regex chars are escaped
s, d = get("/api/products?category=Men&sort=price_asc"); prices=[p["price"] for p in d]; assert prices==sorted(prices); print("men asc", prices)
s, d = get("/api/products?min_price=1000&max_price=1500"); assert all(1000<=p["price"]<=1500 for p in d); print("1000-1500:", len(d))
s, d = get("/api/products?size=XL,XS"); assert all(set(p["sizes"]) & {"XL","XS"} for p in d); print("size XL/XS:", len(d))
s, d = get("/api/products?color=Gold&in_stock=1"); print("gold in stock:", [p["name"] for p in d])
s, d = get("/api/products?brand=Stride,Luna%20Label"); assert {p["brand"] for p in d} <= {"Stride","Luna Label"}
s, d = get("/api/products?min_price=abc"); assert s == 200
s, d = get("/api/products/filters"); print("filters:", d["categories"], d["brands"], d["sizes"], d["min_price"], d["max_price"])

# ---- auth
import json
def login(email, pw):
    r = c.post("/api/auth/login", json={"email": email, "password": pw}); assert r.status_code == 200, r.get_json(); return {"Authorization": "Bearer " + r.get_json()["token"]}
h = login("aisha@example.com", "Customer@123")
admin = login("admin@fashionhub.com", "Admin@123")

pid = lambda name: str(db.products.find_one({"name": name})["_id"])
loafers = pid("Casual Slip-On Loafers")   # stock after seed?
print("loafers stock", db.products.find_one({"_id": __import__('bson').ObjectId(loafers)})["stock"])

# ---- cart validation
db.carts.delete_many({})
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1}); assert r.status_code == 400, r.get_json(); print("no size:", r.get_json())
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1, "size": "M"}); assert r.status_code == 400   # colour required
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1, "size": "ZZ", "color": "White"}); assert r.status_code == 400
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 2, "size": "M", "color": "White"}); assert r.status_code == 201, r.get_json()
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1, "size": "M", "color": "White"}); assert r.status_code == 200   # merged
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1, "size": "L", "color": "White"}); assert r.status_code == 201   # different variant -> new line
s, cart = get("/api/cart", headers=h); assert len(cart) == 2 and sorted(i["quantity"] for i in cart) == [1, 3], cart
print("cart ok:", [(i["size"], i["quantity"], i["stock"]) for i in cart])
r = c.post("/api/cart", headers=h, json={"product_id": pid("Canvas Low-Top Sneakers"), "quantity": 1, "size": "8", "color": "White"}); assert r.status_code == 409; print("sold out:", r.get_json())
r = c.post("/api/cart", headers=h, json={"product_id": pid("Navy Bomber Jacket"), "quantity": 50, "size": "M", "color": "Navy"}); assert r.status_code == 409; print("over stock:", r.get_json())
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": -1, "size": "M", "color": "White"}); assert r.status_code == 400
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": "abc", "size": "M", "color": "White"}); assert r.status_code == 400
r = c.post("/api/cart", headers=h, json={"product_id": pid("White Cotton T-Shirt"), "quantity": 1.5, "size": "M", "color": "White"}); assert r.status_code == 400

# ---- quantity edit
line = [i for i in cart if i["size"] == "M"][0]["_id"]
assert c.put(f"/api/cart/{line}", headers=h, json={"quantity": 5}).status_code == 200
assert c.put(f"/api/cart/{line}", headers=h, json={"quantity": 0}).status_code == 400
assert c.put(f"/api/cart/{line}", headers=h, json={"quantity": 2.5}).status_code == 400
assert c.put(f"/api/cart/{line}", headers=h, json={"quantity": 999}).status_code == 409
assert c.put(f"/api/cart/{line}", headers=h, json={"size": "XXL"}).status_code == 400
assert c.put(f"/api/cart/{line}", headers=h, json={"quantity": 2}).status_code == 200

# ---- checkout reduces stock; cancel restores it
before = db.products.find_one({"name": "White Cotton T-Shirt"})["stock"]
r = c.post("/api/orders", headers=h, json={"delivery_address": {"city": "Delhi"}}); assert r.status_code == 201, r.get_json()
oid = r.get_json()["order_id"]
after = db.products.find_one({"name": "White Cotton T-Shirt"})["stock"]
assert before - after == 3, (before, after)   # 2 (M) + 1 (L)
assert db.carts.count_documents({"user_id": {"$exists": True}}) == 0
r = c.put(f"/api/orders/{oid}/status", headers=admin, json={"status": "Cancelled"}); assert r.status_code == 200
assert db.products.find_one({"name": "White Cotton T-Shirt"})["stock"] == before
c.put(f"/api/orders/{oid}/status", headers=admin, json={"status": "Cancelled"})   # second cancel must not double-restock
assert db.products.find_one({"name": "White Cotton T-Shirt"})["stock"] == before

# ---- race: stock changed after add-to-cart
db.products.update_one({"name": "Navy Bomber Jacket"}, {"$set": {"stock": 3}})
assert c.post("/api/cart", headers=h, json={"product_id": pid("Navy Bomber Jacket"), "quantity": 2, "size": "M", "color": "Navy"}).status_code == 201
db.products.update_one({"name": "Navy Bomber Jacket"}, {"$set": {"stock": 1}})
r = c.post("/api/orders", headers=h, json={"delivery_address": {"city": "Delhi"}}); assert r.status_code == 409; print("checkout race:", r.get_json())
assert db.carts.count_documents({}) == 1     # cart untouched on failure
print("ALL TESTS PASSED")
