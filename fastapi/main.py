from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import os
from datetime import datetime, timedelta

# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DB_FILE = "database.json"

# Initialize FastAPI app
app = FastAPI(title="Feedback System API", description="API for managing products and feedback")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class FeedbackBase(BaseModel):
    customer_name: str
    email: EmailStr
    message: str
    rating: int

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    product_id: int

    class Config:
        orm_mode = True

# Utility functions
def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(authorization: str = Header(...)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None
    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = read_db()
    user = next((u for u in db["users"] if u["email"] == email), None)
    if user is None:
        raise credentials_exception
    
    return user

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# API Endpoints
@app.post("/signup/", response_model=User)
def create_user(user: UserCreate):
    db = read_db()
    if any(u["email"] == user.email for u in db["users"]):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = {
        "id": len(db["users"]) + 1,
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password)
    }
    db["users"].append(new_user)
    write_db(db)
    return new_user

@app.post("/login/")
def login_route(email: str, password: str):
    db = read_db()
    user = next((u for u in db["users"] if u["email"] == email), None)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/products/", response_model=Product)
def create_product(product: ProductCreate, current_user: User = Depends(get_current_user)):
    db = read_db()
    new_product = {
        "id": len(db["products"]) + 1,
        "name": product.name,
        "description": product.description,
        "owner_id": current_user["id"]
    }
    db["products"].append(new_product)
    write_db(db)
    return new_product

@app.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 10):
    db = read_db()
    return db["products"][skip: skip + limit]

@app.post("/products/{product_id}/feedbacks/", response_model=Feedback)
def create_feedback(product_id: int, feedback: FeedbackCreate,):
    db = read_db()
    new_feedback = {
        "id": len(db["feedbacks"]) + 1,
        "customer_name": feedback.customer_name,
        "email": feedback.email,
        "message": feedback.message,
        "rating": feedback.rating,
        "product_id": product_id
    }
    db["feedbacks"].append(new_feedback)
    write_db(db)
    return new_feedback

@app.get("/products/{product_id}/feedbacks/", response_model=List[Feedback])
def read_feedbacks(product_id: int):
    db = read_db()
    return [f for f in db["feedbacks"] if f["product_id"] == product_id]

# Initialize the database file if it doesn't exist
if not os.path.exists(DB_FILE):
    initial_data = {
        "users": [],
        "products": [],
        "feedbacks": []
    }
    write_db(initial_data)