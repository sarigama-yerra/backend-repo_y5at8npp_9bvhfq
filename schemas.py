"""
Database Schemas

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Product -> "product").
These schemas mirror the data used by the API so documents are consistently
validated and easy to inspect with the database viewer.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# ---------- Core Commerce Schemas ----------

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
    date: datetime = Field(default_factory=datetime.utcnow)

class Product(BaseModel):
    """
    Collection name: "product"
    """
    title: str
    description: Optional[str] = None
    category: str
    media: List[Media] = []
    price: PriceInfo
    trend_score: float = Field(ge=0, le=100, default=0)
    badges: List[str] = []
    seo: SEO
    angles: List[Angle] = []
    avatars: List[Avatar] = []
    reviews: List[Review] = []
    stock: int = 0

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)

class Cart(BaseModel):
    """
    Collection name: "cart"
    """
    items: List[CartItem]
    currency: str = "USD"
    subtotal: float
    created_at: datetime

class Order(BaseModel):
    """
    Collection name: "order"
    """
    cart_id: str
    email: str
    total: float
    currency: str
    payment_method: str
    status: str = "pending"
    created_at: datetime

class Reminder(BaseModel):
    """
    Collection name: "reminders"
    """
    cart_id: str
    type: str
    scheduled_for: datetime

class WebhookLog(BaseModel):
    """
    Collection name: "webhook_log"
    """
    provider: str
    payload: dict
    received_at: datetime = Field(default_factory=datetime.utcnow)

# Optional user schema (for future accounts/newsletter)
class User(BaseModel):
    name: str
    email: str
    is_active: bool = True
