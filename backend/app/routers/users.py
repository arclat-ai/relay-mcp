from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    pass

@router.patch("/me", response_model=UserResponse)
async def update_current_user(user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    pass
