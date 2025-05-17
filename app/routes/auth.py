from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from config.db import get_db
from schemas.user import UserCreate, UserResponse, UserLogin, UserUpdate, TokenData
from models.user import User, UserRole
from services.user_service import UserService
from utils.security import verify_token, COOKIE_NAME

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
user_service = UserService()

async def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        user_id = payload.get("user_id")  # Corrección aquí
        
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticación inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = TokenData(username=username, user_id=user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = user_service.get_user_by_id(db, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes"
        )
    return current_user

@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    result = user_service.create_user(db, user_data)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
        
    tokens = user_service.create_tokens(user)  # Corrección aquí
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=tokens["access_token"],
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False
    )
    
    return {
        **tokens,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Sesión cerrada"}

@router.get("/verify/{token}")
async def verify_email(
    token: str = Path(..., ge=1),  # Corrección de sintaxis
    db: Session = Depends(get_db)
):
    result = user_service.verify_account(db, token)  # Corrección aquí
    if result["success"]:
        return {"message": "Cuenta verificada"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result["message"]
    )

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(...),
    db: Session = Depends(get_db)
):
    user_service.request_password_reset(db, email)
    return {"message": "Instrucciones enviadas si el correo existe"}

@router.post("/reset-password/{token}")
async def reset_password(
    token: str = Path(...),
    password: str = Body(...),
    db: Session = Depends(get_db)
):
    result = user_service.reset_password(db, token, password)
    if result["success"]:
        return {"message": "Contraseña actualizada"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result["message"]
    )

@router.post("/change-password")
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        success = user_service.change_password(db, current_user.id, current_password, new_password)
        if success:
            return {"message": "Contraseña cambiada"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al cambiar contraseña"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    return user_service.get_all_users(db, skip, limit)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )
        
    result = user_service.delete_user(db, user_id)
    if result["success"]:
        return {"message": "Usuario eliminado"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=result["message"]
    )