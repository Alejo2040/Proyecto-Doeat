from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from ..config.db import Base
import enum

class UserRole(str, enum.Enum):
    """
    Enumeración para los roles de usuario.
    """
    ADMIN = "admin"
    CASHIER = "cashier"

class User(Base):
    """
    Modelo para representar usuarios en el sistema.
    
    Attributes:
        id (int): Identificador único del usuario
        username (str): Nombre de usuario único
        email (str): Correo electrónico único
        password (str): Contraseña hasheada
        role (UserRole): Rol del usuario (admin o cashier)
        is_active (bool): Estado de activación de la cuenta
        created_at (datetime): Fecha de creación de la cuenta
        updated_at (datetime): Fecha de última actualización
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CASHIER, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"