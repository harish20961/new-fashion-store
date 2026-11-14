"""
Fills the FashionHub database with demo data:
  - 30 products (stock levels, sizes, colours, descriptions)
  - 1 admin + 6 customer accounts
  - ~20 orders spread over the last 6 weeks (stock is reduced to match)
  - reviews written only by customers who received that product

Run from the project root:
    python tools/seed_data.py            # add / refresh demo data (safe to re-run)
    python tools/seed_data.py --reset    # wipe products, carts, orders, reviews, wishlists first

Needs:  pip install pymongo python-dotenv werkzeug   (already in backend/requirements.txt)
Uses MONGO_URI from your .env file, same as the Flask app.

Demo logins (change them if you ever deploy this publicly!):
    admin@fashionhub.com     /  Admin@123
    aisha@example.com        /  Customer@123   (and the other @example.com users)
"""
import argparse
import datetime
import os
import random
import sys

from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

ADMIN_PASSWORD = "Admin@123"
CUSTOMER_PASSWORD = "Customer@123"

CLOTHING = ["S", "M", "L", "XL"]
WOMEN_SIZES = ["XS", "S", "M", "L"]
SHOE_SIZES = ["6", "7", "8", "9", "10"]
WOMEN_SHOE_SIZES = ["4", "5", "6", "7", "8"]
JEAN_SIZES = ["28", "30", "32", "34", "36"]

# Only 6 photos exist in frontend/images/products, so products share them by type.
# Drop more photos in that folder and change the image paths below to use them.
TSHIRT = "images/products/tshirt1.jpg"
JACKET = "images/products/jacket1.jpg"
DRESS = "images/products/dress1.jpg"
SNEAKER = "images/products/sneaker1.jpg"
SHOES = "images/products/shoes1.jpg"
BAG = "images/products/bag1.jpg"

# name, price, category, subcategory, brand, sizes, colours, stock, image, description
PRODUCTS = [
    # ---------- Men ----------
    ("White Cotton T-Shirt", 599, "Men", "T-Shirts", "FashionHub", CLOTHING, ["White", "Black", "Grey"], 50, TSHIRT,
     "A soft everyday crew-neck in breathable 100% combed cotton. Pre-shrunk, so it keeps its fit wash after wash."),
    ("Blue Denim Jacket", 1999, "Men", "Jackets", "FashionHub", ["M", "L", "XL"], ["Blue", "Black"], 20, JACKET,
     "A classic trucker jacket in mid-weight denim with metal buttons and two chest pockets. Layers over anything."),
    ("Slim Fit Oxford Shirt", 1299, "Men", "Shirts", "Urban Thread", CLOTHING, ["White", "Blue", "Pink"], 34, TSHIRT,
     "A smart-casual Oxford with a button-down collar. Works for the office and for weekends."),
    ("Classic Polo T-Shirt", 799, "Men", "T-Shirts", "Urban Thread", CLOTHING, ["Black", "Navy", "Maroon"], 42, TSHIRT,
     "Pique-knit cotton polo with a two-button placket and ribbed collar. Easy to dress up or down."),
    ("Straight Fit Blue Jeans", 1799, "Men", "Jeans", "Maple & Co", JEAN_SIZES, ["Blue", "Black"], 28, JACKET,
     "Comfort-stretch denim with a straight leg and a mid rise. Built to last through years of wear."),
    ("Olive Cargo Pants", 1599, "Men", "Trousers", "Maple & Co", ["30", "32", "34", "36"], ["Olive", "Khaki", "Black"], 18, JACKET,
     "Relaxed-fit cargos in cotton twill with six pockets. Roomy where you need it, tapered at the ankle."),
    ("Grey Pullover Hoodie", 1499, "Men", "Hoodies", "FashionHub", CLOTHING, ["Grey", "Black", "Navy"], 36, TSHIRT,
     "Heavyweight fleece hoodie with a brushed inside, kangaroo pocket and adjustable drawcord."),
    ("Striped Linen Shirt", 1399, "Men", "Shirts", "Urban Thread", CLOTHING, ["White", "Blue"], 22, TSHIRT,
     "A lightweight linen-blend shirt that stays cool in summer heat. Slightly relaxed cut."),
    ("Navy Bomber Jacket", 2799, "Men", "Jackets", "Maple & Co", ["M", "L", "XL"], ["Navy", "Olive"], 4, JACKET,
     "Water-resistant bomber with a quilted lining and ribbed cuffs. A limited run, so stock is low."),

    # ---------- Women ----------
    ("Floral Summer Dress", 1499, "Women", "Dresses", "FashionHub", ["S", "M", "L"], ["Pink", "Yellow", "Blue"], 30, DRESS,
     "A flowy knee-length dress in a soft floral print with a tie waist. Made from light, breathable viscose."),
    ("Black Wrap Dress", 1999, "Women", "Dresses", "Luna Label", WOMEN_SIZES, ["Black", "Maroon"], 16, DRESS,
     "A flattering wrap silhouette with flutter sleeves. Goes from dinner dates to office parties."),
    ("Printed Cotton Kurti", 899, "Women", "Ethnic Wear", "Aarav Ethnics", ["S", "M", "L", "XL"], ["Teal", "Mustard", "Pink"], 40, DRESS,
     "A straight-cut cotton kurti with hand-block inspired prints and three-quarter sleeves."),
    ("High-Waist Skinny Jeans", 1699, "Women", "Jeans", "Maple & Co", ["26", "28", "30", "32"], ["Blue", "Black"], 25, JACKET,
     "Stretch denim that sculpts without squeezing. High rise, full length, five-pocket styling."),
    ("Pleated Midi Skirt", 1199, "Women", "Skirts", "Luna Label", WOMEN_SIZES, ["Beige", "Black", "Green"], 20, DRESS,
     "An elastic-waist midi skirt with fine pleats that move beautifully when you walk."),
    ("Ribbed Knit Top", 699, "Women", "Tops", "Luna Label", WOMEN_SIZES, ["White", "Black", "Lilac"], 45, TSHIRT,
     "A fitted ribbed top with a square neckline. Stretchy, soft, and easy to layer."),
    ("Embroidered Anarkali Kurta Set", 2899, "Women", "Ethnic Wear", "Aarav Ethnics", ["S", "M", "L", "XL"], ["Maroon", "Navy"], 12, DRESS,
     "A festive three-piece set: embroidered anarkali kurta, churidar and dupatta. Ideal for weddings and celebrations."),
    ("Oversized White Shirt", 1299, "Women", "Tops", "FashionHub", WOMEN_SIZES, ["White", "Blue"], 28, TSHIRT,
     "A crisp cotton shirt cut generously for an easy, relaxed look. Wear it buttoned up or as a layer."),
    ("Women's Denim Jacket", 2199, "Women", "Jackets", "Maple & Co", WOMEN_SIZES, ["Blue", "White"], 14, JACKET,
     "A cropped denim jacket with a slightly worn wash and a soft, broken-in feel."),

    # ---------- Footwear ----------
    ("White Sneakers", 2499, "Footwear", "Sneakers", "FashionHub", SHOE_SIZES[1:], ["White", "Black"], 25, SNEAKER,
     "Clean low-top sneakers in smooth faux leather with a cushioned insole and durable rubber sole."),
    ("Cushioned Running Shoes", 2999, "Footwear", "Sports Shoes", "Stride", SHOE_SIZES, ["Black", "Blue", "Grey"], 32, SHOES,
     "Lightweight mesh runners with responsive foam cushioning and a grippy outsole for road and treadmill."),
    ("Canvas Low-Top Sneakers", 1499, "Footwear", "Sneakers", "Stride", SHOE_SIZES, ["White", "Navy", "Red"], 0, SNEAKER,
     "Timeless canvas sneakers with a vulcanised sole. Currently sold out; check back soon."),
    ("Leather Formal Shoes", 3499, "Footwear", "Formal Shoes", "Stride", ["7", "8", "9", "10"], ["Brown", "Black"], 10, SHOES,
     "Hand-finished leather Oxfords with a cushioned footbed. Made for interviews, weddings and long workdays."),
    ("Casual Slip-On Loafers", 1999, "Footwear", "Casual Shoes", "Stride", ["7", "8", "9", "10"], ["Tan", "Black", "Navy"], 3, SHOES,
     "Easy slip-on loafers in soft suede-finish fabric. Very few pairs left."),
    ("Block Heel Sandals", 1799, "Footwear", "Sandals", "Luna Label", WOMEN_SHOE_SIZES, ["Beige", "Black", "Gold"], 18, SHOES,
     "Comfortable 5 cm block heels with an adjustable ankle strap. Stable enough to dance in."),

    # ---------- Accessories ----------
    ("Leather Handbag", 1799, "Accessories", "Bags", "FashionHub", [], ["Brown", "Black", "Tan"], 15, BAG,
     "A structured faux-leather handbag with a zip-top, inner pockets and a detachable shoulder strap."),
    ("Canvas Tote Bag", 799, "Accessories", "Bags", "Urban Thread", [], ["Beige", "Black", "Green"], 60, BAG,
     "Sturdy cotton canvas tote with a zip pocket inside. Fits a laptop, a book and your lunch."),
    ("Minimalist Analog Watch", 2299, "Accessories", "Watches", "Tick & Co", [], ["Silver", "Gold", "Black"], 0, BAG,
     "A slim stainless-steel watch with a clean dial and a 3-year warranty. Sold out for now."),
    ("Genuine Leather Belt", 699, "Accessories", "Belts", "Urban Thread", ["30", "32", "34", "36", "38"], ["Brown", "Black"], 38, BAG,
     "Full-grain leather belt with a brushed metal buckle. Develops character as it ages."),
    ("Aviator Sunglasses", 1199, "Accessories", "Sunglasses", "Tick & Co", [], ["Gold", "Silver", "Black"], 27, BAG,
     "Lightweight metal-frame aviators with UV400 polarised lenses."),
    ("Crossbody Sling Bag", 1399, "Accessories", "Bags", "Luna Label", [], ["Black", "Olive", "Tan"], 22, BAG,
     "A compact crossbody with an adjustable strap and two zip compartments. Holds your phone, wallet and keys."),
]

# name, email, city, pincode
CUSTOMERS = [
    ("Aisha Khan", "aisha@example.com", "New Delhi", "110001"),
    ("Rohan Mehta", "rohan@example.com", "Mumbai", "400001"),
    ("Priya Sharma", "priya@example.com", "Bengaluru", "560001"),
    ("Arjun Nair", "arjun@example.com", "Kochi", "682001"),
    ("Sneha Iyer", "sneha@example.com", "Chennai", "600001"),
    ("Vikram Singh", "vikram@example.com", "Jaipur", "302001"),
]

REVIEW_TEXT = {
    5: ["Absolutely love it, great quality for the price.", "Fits perfectly and looks even better in person.",
        "Fast delivery and the fabric feels premium. Will buy again.", "Exactly as shown in the photos. Very happy!"],
    4: ["Really good overall. Slightly different shade than the photo.", "Comfortable and well made. Would recommend.",
        "Good value for money. Stitching could be a little neater."],
    3: ["It's okay. Does the job but nothing special.", "Decent product, but the size runs a bit small."],
    2: ["Quality was lower than I expected for the price."],
}

STATUS_NOTE = ["Delivered"] * 8 + ["Shipped"] * 2 + ["Processing"] + ["Placed"] + ["Cancelled"]


def connect():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fashionhub")
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        sys.exit(f"Could not connect to MongoDB.\n  MONGO_URI = {uri.split('@')[-1]}\n  Error: {exc}\n"
                 "Check your .env file (and your Atlas IP allow-list).")
    return client.get_default_database(default="fashionhub")


def seed_products(db, now):
    ids = {}
    for i, (name, price, cat, sub, brand, sizes, colors, stock, img, desc) in enumerate(PRODUCTS):
        doc = {
            "name": name, "price": price, "category": cat, "subcategory": sub, "brand": brand,
            "sizes": sizes, "colors": colors, "stock": stock, "image_url": img, "description": desc,
        }
        existing = db.products.find_one({"name": name})
        if existing:
            db.products.update_one({"_id": existing["_id"]}, {"$set": doc})
            ids[name] = existing["_id"]
        else:
            # stagger created_at so "newest" has a real order
            doc["created_at"] = now - datetime.timedelta(hours=len(PRODUCTS) - i)
            ids[name] = db.products.insert_one(doc).inserted_id
    return ids


def seed_users(db, now):
    users = {}
    people = [("FashionHub Admin", "admin@fashionhub.com", "admin", ADMIN_PASSWORD, "New Delhi", "110001")]
    people += [(n, e, "customer", CUSTOMER_PASSWORD, c, p) for n, e, c, p in CUSTOMERS]
    for name, email, role, password, city, pincode in people:
        fields = {"name": name, "role": role, "password": generate_password_hash(password), "city": city, "pincode": pincode}
        existing = db.users.find_one({"email": email})
        if existing:
            db.users.update_one({"_id": existing["_id"]}, {"$set": fields})
            users[email] = {**existing, **fields}
        else:
            doc = {"email": email, "created_at": now - datetime.timedelta(days=60), **fields}
            doc["_id"] = db.users.insert_one(doc).inserted_id
            users[email] = doc
    return users


def seed_orders_and_reviews(db, rng, now, users):
    # Stock: orders reduce it, exactly like the real checkout does.
    stock = {p["_id"]: p.get("stock", 0) for p in db.products.find()}
    products = [p for p in db.products.find() if p.get("stock", 0) > 0]
    customers = [u for u in users.values() if u["role"] == "customer"]

    orders_made, reviews_made = 0, 0
    delivered = []  # (user, product, delivered_at) pairs eligible for reviews

    for status in STATUS_NOTE + ["Delivered"] * 8:
        user = rng.choice(customers)
        days_ago = rng.randint(1, 40) if status == "Delivered" else rng.randint(0, 6)
        created = now - datetime.timedelta(days=days_ago, hours=rng.randint(0, 20))

        items, total = [], 0
        for product in rng.sample(products, rng.randint(1, 3)):
            qty = rng.randint(1, 2)
            if status != "Cancelled":
                if stock[product["_id"]] < qty + 1:   # always leave at least 1 on the shelf
                    continue
                stock[product["_id"]] -= qty
            items.append({
                "product_id": str(product["_id"]), "product_name": product["name"], "price": product["price"],
                "quantity": qty, "size": rng.choice(product["sizes"]) if product.get("sizes") else None,
                "color": rng.choice(product["colors"]) if product.get("colors") else None,
                "image_url": product.get("image_url"),
            })
            total += product["price"] * qty
            if status == "Delivered":
                delivered.append((user, product, created + datetime.timedelta(days=rng.randint(3, 6))))
        if not items:
            continue

        db.orders.insert_one({
            "user_id": str(user["_id"]), "items": items, "total_amount": total, "status": status,
            "delivery_address": {"full_name": user["name"], "phone": f"98{rng.randint(10000000, 99999999)}",
                                 "line1": f"{rng.randint(1, 250)}, MG Road", "city": user["city"], "pincode": user["pincode"]},
            "created_at": created, "seeded": True,
        })
        orders_made += 1

    # write the stock back (cancelled orders never took any)
    for pid, left in stock.items():
        db.products.update_one({"_id": pid}, {"$set": {"stock": left}})

    # Reviews: one per (user, product), only for delivered items - matches the "verified buyer" rule.
    seen = set()
    for user, product, when in delivered:
        key = (user["_id"], product["_id"])
        if key in seen or rng.random() < 0.1:
            continue
        seen.add(key)
        rating = rng.choices([5, 4, 3, 2], weights=[50, 30, 14, 6])[0]
        db.reviews.insert_one({
            "user_id": str(user["_id"]), "reviewer_name": user["name"], "product_id": str(product["_id"]),
            "rating": rating, "comment": rng.choice(REVIEW_TEXT[rating]), "created_at": when, "seeded": True,
        })
        reviews_made += 1
    return orders_made, reviews_made


def main():
    parser = argparse.ArgumentParser(description="Seed FashionHub demo data")
    parser.add_argument("--reset", action="store_true",
                        help="delete ALL products, carts, orders, reviews and wishlists before seeding")
    args = parser.parse_args()

    db = connect()
    now = datetime.datetime.utcnow()
    rng = random.Random(42)  # fixed seed -> same demo data every run

    if args.reset:
        for name in ("products", "carts", "orders", "reviews", "wishlists"):
            db[name].delete_many({})
        print("Cleared products, carts, orders, reviews and wishlists.")
    else:
        # only remove what a previous seed run created, so real orders/reviews are kept
        db.orders.delete_many({"seeded": True})
        db.reviews.delete_many({"seeded": True})

    ids = seed_products(db, now)
    users = seed_users(db, now)
    orders, reviews = seed_orders_and_reviews(db, rng, now, users)

    print(f"Database: {db.name}")
    print(f"  products: {len(ids)}   users: {len(users)}   orders: {orders}   reviews: {reviews}")
    print(f"  admin login:    admin@fashionhub.com / {ADMIN_PASSWORD}")
    print(f"  customer login: aisha@example.com / {CUSTOMER_PASSWORD}")


if __name__ == "__main__":
    main()
