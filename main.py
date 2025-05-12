#main.py
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schemas.user import UserCreate , UserLogin , UserOut
import models
from models import User
from dependencies import get_db , engine
from utils import hash_password, verify_password
from auth import create_access_token, get_current_user
from routes.user import router as user_router
from routes.photo import router as photo_router
from routes.comments import router as comment_router
from routes.follow import router as follow_router
from routes.rating import router as ratings_router
from routes.likes import router as likes_router
from routes.feed import router as feed_router
from settings import settings


app = FastAPI()

# Create tables
if settings.ENV != "testing":
    models.Base.metadata.create_all(bind=engine)
# Routes

app.include_router(user_router)
app.include_router(photo_router)
app.include_router(comment_router)
app.include_router(follow_router)
app.include_router(ratings_router)
app.include_router(likes_router)
app.include_router(feed_router)

@app.get('/')
async def hello():
    return {"message": "Hello, world!"}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
