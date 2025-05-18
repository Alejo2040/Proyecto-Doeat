from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Esquema base para productos"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)

class ProductCreate(ProductBase):
    """Esquema para crear productos"""
    quantity: int = Field(0, ge=0)

class ProductResponse(ProductBase):
    """Esquema para respuestas con datos de producto"""
    id: int
    quantity: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    """Esquema para actualizar productos"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)

# Esquemas para movimientos de stock
class StockMovementBase(BaseModel):
    """Esquema base para movimientos de stock"""
    product_id: int
    quantity_change: int
    movement_type: str = Field(..., min_length=1, max_length=50)
    reference: Optional[str] = None
    notes: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    """Esquema para crear movimientos de stock"""
    pass

class StockMovementResponse(StockMovementBase):
    """Esquema para respuestas con datos de movimiento de stock"""
    id: int
    movement_date: datetime
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True

# Esquemas para ventas
class SaleItemBase(BaseModel):
    """Esquema base para items de venta"""
    product_id: int
    quantity: int = Field(..., gt=0)

class SaleItemCreate(SaleItemBase):
    """Esquema para crear items de venta"""
    pass

class SaleItemResponse(SaleItemBase):
    """Esquema para respuestas con datos de item de venta"""
    id: int
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    """Esquema base para ventas"""
    customer_name: Optional[str] = None
    payment_method: str = Field(..., min_length=1, max_length=50)
    items: List[SaleItemCreate]

class SaleCreate(SaleBase):
    """Esquema para crear ventas"""
    pass

class SaleResponse(BaseModel):
    """Esquema para respuestas con datos de venta"""
    id: int
    customer_name: Optional[str] = None
    total_amount: float
    payment_method: str
    created_by: int
    created_at: datetime
    items: List[SaleItemResponse]
    
    class Config:
        from_attributes = True

# Esquemas para compras
class PurchaseItemBase(BaseModel):
    """Esquema base para items de compra"""
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)

class PurchaseItemCreate(PurchaseItemBase):
    """Esquema para crear items de compra"""
    pass

class PurchaseItemResponse(PurchaseItemBase):
    """Esquema para respuestas con datos de item de compra"""
    id: int
    subtotal: float
    
    class Config:
        from_attributes = True

class PurchaseBase(BaseModel):
    """Esquema base para compras"""
    supplier_name: str = Field(..., min_length=1, max_length=100)
    reference: Optional[str] = None
    items: List[PurchaseItemCreate]

class PurchaseCreate(PurchaseBase):
    """Esquema para crear compras"""
    pass

class PurchaseResponse(BaseModel):
    """Esquema para respuestas con datos de compra"""
    id: int
    supplier_name: str
    total_amount: float
    reference: Optional[str] = None
    created_by: int
    created_at: datetime
    items: List[PurchaseItemResponse]
    
    class Config:
        from_attributes = True

# Esquemas para dashboard e informes
class InventorySummary(BaseModel):
    """Esquema para resumen de inventario"""
    total_products: int
    total_stock_value: float
    low_stock_items: List[ProductResponse]