from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db import Base

class Product(Base):
    """
    Modelo para representar productos en el inventario.
    
    Attributes:
        id (int): Identificador único del producto
        name (str): Nombre del producto (único)
        description (str): Descripción del producto
        price (float): Precio del producto
        quantity (int): Cantidad disponible en inventario
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de última actualización
        movements (list): Relación con los movimientos de stock
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación con los movimientos de stock
    movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")
    # Relación con las ventas
    sale_items = relationship("SaleItem", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', quantity={self.quantity})>"


class StockMovement(Base):
    """
    Modelo para registrar los movimientos de stock (entradas y salidas).
    
    Attributes:
        id (int): Identificador único del movimiento
        product_id (int): ID del producto relacionado
        quantity_change (int): Cambio en la cantidad (positivo para entradas, negativo para salidas)
        movement_type (str): Tipo de movimiento ('compra', 'venta', 'ajuste')
        reference (str): Referencia opcional (número de factura, etc.)
        notes (str): Notas o comentarios adicionales
        created_by (int): ID del usuario que realizó el movimiento
        movement_date (datetime): Fecha y hora del movimiento
        product (Product): Relación con el producto
    """
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # + para entrada, - para salida
    movement_type = Column(String(50), nullable=False)  # 'compra', 'venta', 'ajuste'
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    movement_date = Column(DateTime, server_default=func.now())
    
    # Relaciones
    product = relationship("Product", back_populates="movements")
    
    def __repr__(self):
        return f"<StockMovement(id={self.id}, product_id={self.product_id}, change={self.quantity_change})>"


class Sale(Base):
    """
    Modelo para representar ventas completas.
    
    Attributes:
        id (int): Identificador único de la venta
        customer_name (str): Nombre del cliente (opcional)
        total_amount (float): Monto total de la venta
        payment_method (str): Método de pago
        created_by (int): ID del usuario que realizó la venta
        created_at (datetime): Fecha y hora de la venta
        items (list): Relación con los items de la venta
    """
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=True)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Sale(id={self.id}, total={self.total_amount}, date={self.created_at})>"


class SaleItem(Base):
    """
    Modelo para representar items individuales en una venta.
    
    Attributes:
        id (int): Identificador único del item
        sale_id (int): ID de la venta a la que pertenece
        product_id (int): ID del producto vendido
        quantity (int): Cantidad vendida
        unit_price (float): Precio unitario en el momento de la venta
        subtotal (float): Subtotal (cantidad * precio)
        sale (Sale): Relación con la venta
        product (Product): Relación con el producto
    """
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    
    def __repr__(self):
        return f"<SaleItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class Purchase(Base):
    """
    Modelo para representar compras de productos para el inventario.
    
    Attributes:
        id (int): Identificador único de la compra
        supplier_name (str): Nombre del proveedor
        total_amount (float): Monto total de la compra
        reference (str): Número de referencia o factura
        created_by (int): ID del usuario que registró la compra
        created_at (datetime): Fecha y hora de la compra
        items (list): Relación con los items de la compra
    """
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(100), nullable=False)
    total_amount = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, supplier='{self.supplier_name}', total={self.total_amount})>"


class PurchaseItem(Base):
    """
    Modelo para representar items individuales en una compra.
    
    Attributes:
        id (int): Identificador único del item
        purchase_id (int): ID de la compra a la que pertenece
        product_id (int): ID del producto comprado
        quantity (int): Cantidad comprada
        unit_price (float): Precio unitario de compra
        subtotal (float): Subtotal (cantidad * precio)
        purchase (Purchase): Relación con la compra
        product (Product): Relación con el producto
    """
    __tablename__ = "purchase_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relaciones
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<PurchaseItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"