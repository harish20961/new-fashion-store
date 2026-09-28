import json
import urllib.request

API = "http://127.0.0.1:5000/api/products"

# Add one entry per product. image_url must match a file that exists
# in frontend/images/products/. Remove entries you don't have photos for yet.
PRODUCTS = [
    {"name": "White Cotton T-Shirt", "price": 599, "category": "Men",
     "brand": "FashionHub", "sizes": ["S", "M", "L", "XL"], "stock": 50,
     "image_url": "images/products/tshirt1.jpg"},
    {"name": "Blue Denim Jacket", "price": 1999, "category": "Men",
     "brand": "FashionHub", "sizes": ["M", "L", "XL"], "stock": 20,
     "image_url": "images/products/jacket1.jpg"},
    {"name": "Floral Summer Dress", "price": 1499, "category": "Women",
     "brand": "FashionHub", "sizes": ["S", "M", "L"], "stock": 30,
     "image_url": "images/products/dress1.jpg"},
    {"name": "White Sneakers", "price": 2499, "category": "Footwear",
     "brand": "FashionHub", "sizes": ["7", "8", "9", "10"], "stock": 25,
     "image_url": "images/products/sneaker1.jpg"},
    {"name": "Leather Handbag", "price": 1799, "category": "Accessories",
     "brand": "FashionHub", "sizes": [], "stock": 15,
     "image_url": "images/products/bag1.jpg"},
]


def call_api(method, url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=body, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


existing_names = {p["name"] for p in call_api("GET", API)}

for product in PRODUCTS:
    if product["name"] in existing_names:
        print(f"skipped (already exists): {product['name']}")
        continue
    call_api("POST", API, product)
    print(f"added: {product['name']}")