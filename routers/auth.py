from fastapi import FastAPI, HTTPException, APIRouter, Depends, BackgroundTasks
from database.connections import users, database
from database.schemas import UserCreate, UserLogin, OTPRequest, OTPVerify
from security import get_password_hash, verify_password, create_access_token, generate_otp, send_otp_email
from fastapi.security import OAuth2PasswordRequestForm
import database.queries as db_queries

router = APIRouter()


@router.post("/register")
async def register(user_data: UserCreate):
    query = users.select().where(users.c.email == user_data.email)
    existing_user = await database.fetch_one(query)
    
    if existing_user:
        raise HTTPException(status_code=400, detail="email already exists")

    hashed_password = get_password_hash(user_data.password)

    query = users.insert().values(
        email=user_data.email,
        password=hashed_password,
        otp=None,
        otp_expires_at=None,
        is_verified=False
    )

    user_id = await database.execute(query)

    return {
        "message": "user registered successfully",
        "user_id": user_id,
        "email": user_data.email
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = users.select().where(users.c.email == form_data.username)
    db_user = await database.fetch_one(query)

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=400, detail="Invalid username or password"
        )

    if not db_user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified. Please verify your email before logging in.",
        )

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/send-otp")
async def send_otp(request: OTPRequest, background_tasks:BackgroundTasks):
    query = users.select().where(users.c.email == request.email)
    existing_user = await database.fetch_one(query)

    if not existing_user:
        raise HTTPException(status_code = 404, detail="user not found")

    otp = generate_otp()
    await db_queries.save_otp(request.email, otp)

    background_tasks.add_task(send_otp_email, request.email, otp)

    return {"message": "otp sent to your email"}

@router.post("/verify-otp")
async def verify_otp(request: OTPVerify):
    is_valid = await db_queries.verify_and_clear_otp(request.email, request.otp)

    if not is_valid:
        raise HTTPException(status_code=400, detail="invalid or expired otp")

    return{"message": "email verified successfully"}
