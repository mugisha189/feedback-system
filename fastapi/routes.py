from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Product, Feedback, User as UserModel
from schemas import ProductCreate, Product, FeedbackCreate, Feedback, UserCreate, User
from database import get_db
from auth import signup, login, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

router = APIRouter()

@router.post(
    "/signup/",
    response_model=User,
    tags=["Authentication"],
    summary="Create a new user",
    description="This endpoint allows you to create a new user account."
)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return signup(user, db)

@router.post(
    "/login/",
    tags=["Authentication"],
    summary="User login",
    description="This endpoint allows users to log in and receive a JWT token."
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(form_data, db)

@router.post(
    "/products/",
    response_model=Product,
    tags=["Product Management"],
    summary="Create a new product",
    description="This endpoint allows an authenticated user to create a new product."
)
def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_product = Product(name=product.name, description=product.description, owner_id=current_user.id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get(
    "/products/",
    response_model=List[Product],
    tags=["Product Management"],
    summary="Get all products",
    description="This endpoint retrieves a list of all products."
)
def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@router.post(
    "/products/{product_id}/feedbacks/",
    response_model=Feedback,
    tags=["Feedback Management"],
    summary="Create feedback for a product",
    description="This endpoint allows an authenticated user to submit feedback for a specific product."
)
def create_feedback(product_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    db_feedback = Feedback(**feedback.dict(), product_id=product_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@router.get(
    "/products/{product_id}/feedbacks/",
    response_model=List[Feedback],
    tags=["Feedback Management"],
    summary="Get feedbacks for a product",
    description="This endpoint retrieves all feedbacks for a specific product. Authorization is required."
)
def read_feedbacks(product_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    feedbacks = db.query(Feedback).filter(Feedback.product_id == product_id).all()
    if not feedbacks:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedbacks 