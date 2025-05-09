import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from jose import JWTError 

from ..models.user import User, UserRole
from ..utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token
from ..schemas.user import UserCreate, UserUpdate, TokenData
from ..services.email_service import EmailService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.email_service = EmailService()
        self.verification_tokens = {}
        self.reset_tokens = {}

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, user_data: UserCreate) -> Union[User, Dict[str, str]]:
        try:
            if self.get_user_by_username(db, user_data.username):
                return {"error": "Usuario ya existe"}
                
            if self.get_user_by_email(db, user_data.email):
                return {"error": "Email ya registrado"}
                
            hashed_password = get_password_hash(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                password=hashed_password,
                role=user_data.role
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            verification_token = str(uuid4())
            self.verification_tokens[verification_token] = {
                "user_id": db_user.id,
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
            
            self.email_service.send_verification_email(db_user.email, verification_token)
            
            logger.info(f"Usuario creado: {db_user.id}")
            return db_user
            
        except IntegrityError:
            db.rollback()
            return {"error": "Error de base de datos"}
        except Exception as e:
            db.rollback()
            logger.error(f"Error: {str(e)}")
            return {"error": "Error al crear usuario"}

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(db, username)
        if not user or not verify_password(password, user.password):
            return None
        return user if user.is_active else None

    def verify_account(self, db: Session, token: str) -> Dict[str, Any]:
        if token not in self.verification_tokens:
            return {"success": False, "message": "Token inválido"}
            
        token_data = self.verification_tokens[token]
        if datetime.utcnow() > token_data["expires_at"]:
            del self.verification_tokens[token]
            return {"success": False, "message": "Token expirado"}
            
        user = self.get_user_by_id(db, token_data["user_id"])
        if not user:
            return {"success": False, "message": "Usuario no existe"}
            
        user.is_active = True
        db.commit()
        del self.verification_tokens[token]
        return {"success": True, "message": "Cuenta verificada"}

    def request_password_reset(self, db: Session, email: str) -> Dict[str, Any]:
        user = self.get_user_by_email(db, email)
        if not user:
            return {"success": True, "message": "Instrucciones enviadas"}
            
        reset_token = str(uuid4())
        self.reset_tokens[reset_token] = {
            "user_id": user.id,
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }
        
        self.email_service.send_password_reset_email(user.email, reset_token, user.username)
        return {"success": True, "message": "Correo enviado"}

    def reset_password(self, db: Session, token: str, new_password: str) -> Dict[str, Any]:
        if token not in self.reset_tokens:
            return {"success": False, "message": "Token inválido"}
            
        token_data = self.reset_tokens[token]
        if datetime.utcnow() > token_data["expires_at"]:
            del self.reset_tokens[token]
            return {"success": False, "message": "Token expirado"}
            
        user = self.get_user_by_id(db, token_data["user_id"])
        if not user:
            return {"success": False, "message": "Usuario no existe"}
            
        user.password = get_password_hash(new_password)
        db.commit()
        del self.reset_tokens[token]
        return {"success": True, "message": "Contraseña actualizada"}

    def change_password(
        self, 
        db: Session, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
            
        if not verify_password(current_password, user.password):
            raise ValueError("Contraseña actual incorrecta")
            
        user.password = get_password_hash(new_password)
        db.commit()
        return True

    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> Union[User, Dict[str, str]]:
        user = self.get_user_by_id(db, user_id)
        if not user:
            return {"error": "Usuario no encontrado"}
            
        if user_data.email and user_data.email != user.email:
            if self.get_user_by_email(db, user_data.email):
                return {"error": "Email en uso"}
            user.email = user_data.email
            
        if user_data.username and user_data.username != user.username:
            if self.get_user_by_username(db, user_data.username):
                return {"error": "Usuario en uso"}
            user.username = user_data.username
            
        if user_data.role:
            user.role = user_data.role
            
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
            
        db.commit()
        return user

    def create_tokens(self, user: User) -> Dict[str, str]:
        access_token = create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        })
        
        refresh_token = create_refresh_token({
            "sub": user.username,
            "user_id": user.id
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        try:
            payload = verify_token(refresh_token)
            if payload.get("token_type") != "refresh":
                return {"error": "Token inválido"}
                
            return {
                "access_token": create_access_token({
                    "sub": payload["sub"],
                    "user_id": payload["user_id"]
                }),
                "token_type": "bearer"
            }
        except JWTError:
            return {"error": "Token inválido"}

    def delete_user(self, db: Session, user_id: int) -> Dict[str, Any]:
        user = self.get_user_by_id(db, user_id)
        if not user:
            return {"success": False, "message": "Usuario no existe"}
            
        db.delete(user)
        db.commit()
        return {"success": True, "message": "Usuario eliminado"}

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> list:
        return db.query(User).offset(skip).limit(limit).all()
        # Enviar correo de restablecimiento
        sent = self.email_service.send_password_reset_email(user.email, reset_token, user.username)
        
        if sent:
            logger.info(f"Solicitud de restablecimiento de contraseña para usuario ID: {user.id}")
            return {"success": True, "message": "Se han enviado instrucciones para restablecer tu contraseña"}
        else:
            logger.error(f"Error al enviar correo de restablecimiento para usuario ID: {user.id}")
            return {"success": False, "message": "Error al enviar el correo electrónico"}

    def reset_password(self, db: Session, token: str, new_password: str) -> Dict[str, Any]:
        """
        Restablece la contraseña de un usuario usando un token.
        
        Args:
            db: Sesión de base de datos
            token: Token de restablecimiento
            new_password: Nueva contraseña
            
        Returns:
            Dict[str, Any]: Resultado de la operación
        """
        # Verificar si el token existe y no ha expirado
        if token not in self.reset_tokens:
            return {"success": False, "message": "Token inválido o expirado"}
            
        token_data = self.reset_tokens[token]
        if datetime.utcnow() > token_data["expires_at"]:
            self.reset_tokens.pop(token)
            return {"success": False, "message": "El token ha expirado"}
            
        # Actualizar contraseña del usuario
        user = self.get_user_by_id(db, token_data["user_id"])
        if not user:
            return {"success": False, "message": "Usuario no encontrado"}
            
        user.password = get_password_hash(new_password)
        db.commit()
        
        # Eliminar el token usado
        self.reset_tokens.pop(token)
        
        logger.info(f"Contraseña restablecida para usuario ID: {user.id}")
        return {"success": True, "message": "Contraseña restablecida correctamente"}

    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> Union[User, Dict[str, str]]:
        """
        Actualiza los datos de un usuario.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario a actualizar
            user_data: Datos actualizados
            
        Returns:
            Union[User, Dict[str, str]]: Usuario actualizado o diccionario con error
        """
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return {"error": "Usuario no encontrado"}
                
            # Actualizar email si se proporciona y no está en uso
            if user_data.email and user_data.email != user.email:
                existing_email = self.get_user_by_email(db, user_data.email)
                if existing_email:
                    return {"error": "El correo electrónico ya está en uso"}
                user.email = user_data.email
                
            # Actualizar nombre de usuario si se proporciona y no está en uso
            if user_data.username and user_data.username != user.username:
                existing_username = self.get_user_by_username(db, user_data.username)
                if existing_username:
                    return {"error": "El nombre de usuario ya está en uso"}
                user.username = user_data.username
                
            # Actualizar rol si se proporciona
            if user_data.role is not None:
                user.role = user_data.role
                
            # Actualizar estado activo si se proporciona
            if user_data.is_active is not None:
                user.is_active = user_data.is_active
                
            db.commit()
            db.refresh(user)
            
            logger.info(f"Usuario actualizado ID: {user.id}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error al actualizar usuario: {str(e)}")
            return {"error": "Error al actualizar el usuario"}

    def create_tokens(self, user: User) -> Dict[str, str]:
        """
        Crea tokens JWT para un usuario autenticado.
        
        Args:
            user: Usuario autenticado
            
        Returns:
            Dict[str, str]: Tokens de acceso y actualización
        """
        access_token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
        
        access_token = create_access_token(access_token_data)
        refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renueva un token de acceso usando un token de actualización.
        
        Args:
            refresh_token: Token de actualización
            
        Returns:
            Dict[str, Any]: Nuevo token de acceso o error
        """
        try:
            # Verificar el token de actualización
            payload = verify_token(refresh_token)
            
            # Verificar que sea un token de tipo refresh
            if payload.get("token_type") != "refresh":
                return {"error": "Token inválido"}
                
            # Crear nuevo token de acceso
            access_token_data = {
                "sub": payload.get("sub"),
                "user_id": payload.get("user_id")
            }
            
            new_access_token = create_access_token(access_token_data)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error al refrescar token: {str(e)}")
            return {"error": "Token inválido o expirado"}

    def delete_user(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Elimina un usuario del sistema.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario a eliminar
            
        Returns:
            Dict[str, Any]: Resultado de la operación
        """
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}
                
            db.delete(user)
            db.commit()
            
            logger.info(f"Usuario eliminado ID: {user_id}")
            return {"success": True, "message": "Usuario eliminado correctamente"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error al eliminar usuario: {str(e)}")
            return {"success": False, "message": "Error al eliminar el usuario"}

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> list:
        """
        Obtiene una lista de usuarios paginada.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            list: Lista de usuarios
        """
        return db.query(User).offset(skip).limit(limit).all()