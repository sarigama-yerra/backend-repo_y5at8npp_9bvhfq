import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from bson import ObjectId
from datetime import datetime, timedelta, timezone

from database import db, create_document, get_documents

app = FastAPI(title="Headless Commerce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Models ----------------------

class Media(BaseModel):
    url: HttpUrl
    kind: str = Field("image", description="image|video|gif")

class SEO(BaseModel):
    title: str
    description: str
    keywords: List[str] = []

class PriceInfo(BaseModel):
    supplier_price: float
    target_price: float
    currency: str = "USD"
    margin_x: float = 3.0

class Angle(BaseModel):
    hook: str
    script: str

class Avatar(BaseModel):
    name: str
    age: int
    archetype: str
    pains: List[str]
    desires: List[str]

class Review(BaseModel):
    name: str
    rating: int = Field(ge=1, le=5)
    comment: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductIn(BaseModel):
    title: str
    description: str
    category: str
    media: List[Media]
    price: PriceInfo
    trend_score: float = Field(ge=0, le=100)
    badges: List[str] = []
    seo: SEO
    angles: List[Angle] = []
    avatars: List[Avatar] = []
    reviews: List[Review] = []
    stock: int = 100

class Product(ProductIn):
    id: str

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)

class Cart(BaseModel):
    id: str
    items: List[CartItem]
    currency: str = "USD"
    subtotal: float
    created_at: datetime

class CheckoutRequest(BaseModel):
    cart_id: str
    email: str
    payment_method: str  # stripe|paypal|payfast|payflex|yoco|ozow|card
    shipping_country: str
    shipping_city: str
    shipping_address: str

class Order(BaseModel):
    id: str
    cart_id: str
    email: str
    total: float
    currency: str
    payment_method: str
    status: str
    created_at: datetime

# ---------------------- Utilities ----------------------

def _to_product(doc) -> Product:
    return Product(
        id=str(doc.get("_id")),
        title=doc["title"],
        description=doc.get("description", ""),
        category=doc.get("category", "General"),
        media=doc.get("media", []),
        price=doc.get("price"),
        trend_score=doc.get("trend_score", 0),
        badges=doc.get("badges", []),
        seo=doc.get("seo"),
        angles=doc.get("angles", []),
        avatars=doc.get("avatars", []),
        reviews=doc.get("reviews", []),
        stock=doc.get("stock", 0),
    )

# ---------------------- Seed Data ----------------------

seed_products: List[ProductIn] = [
    ProductIn(
        title="Portable Blender Pro X",
        description="Blend smoothies on-the-go with a powerful, quiet motor. USB-C fast charging, self-cleaning, BPA-free.",
        category="Fitness",
        media=[Media(url="https://images.unsplash.com/photo-1556911220-e15b29be8c8f", kind="image")],
        price=PriceInfo(supplier_price=16.0, target_price=49.99, currency="USD", margin_x=3.1),
        trend_score=89,
        badges=["Money-back Guarantee", "BPA-Free", "USB-C Fast Charge"],
        seo=SEO(title="Portable Blender Pro X", description="Powerful portable blender for smoothies, shakes and more.", keywords=["portable blender","usb-c blender","smoothie maker"]),
        angles=[Angle(hook="Stop skipping breakfast", script="Open with chaotic morning, then show 10-sec smoothie." )],
        avatars=[Avatar(name="Lerato", age=28, archetype="Busy Professional", pains=["No time for breakfast"], desires=["Healthy lifestyle"])],
        reviews=[Review(name="Sam", rating=5, comment="Game changer for the gym! ")],
        stock=250,
    ),
    ProductIn(
        title="Pet Hair Eraser Turbo",
        description="Cordless handheld vacuum engineered for pet hair with turbo brush and HEPA filtration.",
        category="Pet",
        media=[Media(url="https://images.unsplash.com/photo-1581578731548-c64695cc6952", kind="image")],
        price=PriceInfo(supplier_price=22.0, target_price=69.99, currency="USD", margin_x=3.1),
        trend_score=91,
        badges=["HEPA Certified", "2-Year Warranty"],
        seo=SEO(title="Pet Hair Eraser Turbo", description="Cordless HEPA handheld vacuum for pet hair.", keywords=["pet vacuum","handheld vacuum","pet hair remover"]),
        angles=[Angle(hook="If you have pets, watch this", script="Show sofa full of hair → quick clean montage.")],
        avatars=[Avatar(name="Thabo", age=34, archetype="Pet Parent", pains=["Hair everywhere"], desires=["Clean home"])],
        reviews=[Review(name="Amy", rating=5, comment="Picks up everything." )],
        stock=180,
    ),
    ProductIn(
        title="LED Galaxy Projector 2.0",
        description="Transform rooms into a galaxy with app control, sleep timer, and white noise.",
        category="Lifestyle",
        media=[Media(url="https://images.unsplash.com/photo-1510940537115-1e3ab72b45dc", kind="image")],
        price=PriceInfo(supplier_price=14.5, target_price=49.99, currency="USD", margin_x=3.4),
        trend_score=87,
        badges=["App Control", "Timer", "White Noise"],
        seo=SEO(title="LED Galaxy Projector", description="Cosmic ambience projector with app control.", keywords=["galaxy projector","room lights","ambient light"]),
        angles=[Angle(hook="Turn any room into a vibe", script="Dark room → stars on → relaxing shots.")],
        avatars=[Avatar(name="Neo", age=22, archetype="Student Creator", pains=["Boring room"], desires=["Aesthetic vibe"])],
        reviews=[Review(name="Jess", rating=5, comment="My sleep improved a lot." )],
        stock=300,
    ),
    ProductIn(
        title="Smart Posture Corrector",
        description="Wearable posture trainer with vibration alerts and app analytics.",
        category="Tech",
        media=[Media(url="https://images.unsplash.com/photo-1543269865-cbf427effbad", kind="image")],
        price=PriceInfo(supplier_price=18.0, target_price=59.99, currency="USD", margin_x=3.3),
        trend_score=90,
        badges=["App Sync", "USB-C", "1-Year Warranty"],
        seo=SEO(title="Smart Posture Corrector", description="Wearable posture sensor with app analytics.", keywords=["posture corrector","wearable","back pain"]),
        angles=[Angle(hook="Hunching at your desk?", script="Office B-roll + phone notifications.")],
        avatars=[Avatar(name="Aisha", age=31, archetype="Remote Worker", pains=["Neck/back pain"], desires=["Better posture"])],
        reviews=[Review(name="Ben", rating=4, comment="Really helps me sit upright." )],
        stock=200,
    ),
    ProductIn(
        title="AeroBrew Kettle",
        description="Gooseneck electric kettle with precise temperature control for coffee & tea.",
        category="Kitchen",
        media=[Media(url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd", kind="image")],
        price=PriceInfo(supplier_price=21.0, target_price=69.99, currency="USD", margin_x=3.3),
        trend_score=86,
        badges=["Auto Shutoff", "Barista Approved"],
        seo=SEO(title="AeroBrew Kettle", description="Precision gooseneck kettle for pour-over coffee.", keywords=["gooseneck kettle","coffee kettle","barista"]),
        angles=[Angle(hook="Make café-quality coffee at home", script="Thermometer closeups + pour-over." )],
        avatars=[Avatar(name="Sipho", age=29, archetype="Coffee Enthusiast", pains=["Inconsistent pours"], desires=["Perfect brew"])],
        reviews=[Review(name="Mila", rating=5, comment="Dialed my pour-over." )],
        stock=160,
    ),
]

# ---------------------- Routes ----------------------

@app.get("/")
def read_root():
    return {"message": "Headless Commerce API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

@app.post("/seed", response_model=List[Product])
def seed_products_endpoint():
    created = []
    for p in seed_products:
        # Avoid duplicates by title
        existing = db["product"].find_one({"title": p.title}) if db else None
        if existing:
            created.append(_to_product(existing))
            continue
        _id = create_document("product", p.model_dump())
        doc = db["product"].find_one({"_id": ObjectId(_id)})
        created.append(_to_product(doc))
    return created

@app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = None, q: Optional[str] = None, sort: Optional[str] = None):
    filter_q = {}
    if category:
        filter_q["category"] = category
    if q:
        filter_q["title"] = {"$regex": q, "$options": "i"}
    docs = db["product"].find(filter_q) if db else []
    items = [_to_product(d) for d in docs]
    if sort == "trend":
        items.sort(key=lambda x: x.trend_score, reverse=True)
    return items

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    doc = db["product"].find_one({"_id": ObjectId(product_id)}) if db else None
    if not doc:
        raise HTTPException(404, "Product not found")
    return _to_product(doc)

@app.post("/cart", response_model=Cart)
def create_cart(items: List[CartItem]):
    # compute subtotal
    subtotal = 0.0
    for it in items:
        doc = db["product"].find_one({"_id": ObjectId(it.product_id)})
        if not doc:
            raise HTTPException(404, f"Product {it.product_id} not found")
        price = doc.get("price", {}).get("target_price", 0.0)
        subtotal += price * it.quantity
    cid = create_document("cart", {
        "items": [i.model_dump() for i in items],
        "currency": "USD",
        "subtotal": round(subtotal, 2),
        "created_at": datetime.now(timezone.utc)
    })
    cart_doc = db["cart"].find_one({"_id": ObjectId(cid)})
    return Cart(id=str(cart_doc["_id"]), items=cart_doc["items"], currency=cart_doc["currency"], subtotal=cart_doc["subtotal"], created_at=cart_doc["created_at"])

@app.get("/cart/{cart_id}", response_model=Cart)
def get_cart(cart_id: str):
    cart_doc = db["cart"].find_one({"_id": ObjectId(cart_id)}) if db else None
    if not cart_doc:
        raise HTTPException(404, "Cart not found")
    return Cart(id=str(cart_doc["_id"]), items=cart_doc["items"], currency=cart_doc["currency"], subtotal=cart_doc["subtotal"], created_at=cart_doc["created_at"])

@app.post("/checkout", response_model=Order)
def checkout(req: CheckoutRequest):
    cart_doc = db["cart"].find_one({"_id": ObjectId(req.cart_id)}) if db else None
    if not cart_doc:
        raise HTTPException(404, "Cart not found")
    total = cart_doc["subtotal"]  # taxes/shipping can be added here
    order_id = create_document("order", {
        "cart_id": req.cart_id,
        "email": req.email,
        "total": total,
        "currency": cart_doc.get("currency", "USD"),
        "payment_method": req.payment_method,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    })
    order_doc = db["order"].find_one({"_id": ObjectId(order_id)})
    return Order(
        id=str(order_doc["_id"]),
        cart_id=order_doc["cart_id"],
        email=order_doc["email"],
        total=order_doc["total"],
        currency=order_doc["currency"],
        payment_method=order_doc["payment_method"],
        status=order_doc["status"],
        created_at=order_doc["created_at"],
    )

@app.post("/abandoned/{cart_id}")
def send_abandoned_cart(cart_id: str):
    # Stub for email integration: SendGrid, Mailgun, or SMTP can be wired with env keys
    # Here we simply mark a follow-up reminder in DB
    reminder_id = create_document("reminders", {
        "cart_id": cart_id,
        "type": "abandoned_cart",
        "scheduled_for": datetime.now(timezone.utc) + timedelta(hours=3)
    })
    return {"scheduled": True, "id": reminder_id}

# Payment integrations are intentionally abstracted; real keys/SDKs are required.
# You can add PayFast, PayFlex, Yoco, Ozow, Stripe, PayPal by setting env keys and
# implementing webhooks on /webhooks/{provider}.

@app.post("/webhooks/{provider}")
def payment_webhook(provider: str, payload: dict):
    # Placeholder: log payload
    _id = create_document("webhook_log", {"provider": provider, "payload": payload})
    return {"logged": True, "id": _id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
