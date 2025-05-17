from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime

from ..config.db import get_db
from ..models.product import Product, StockMovement, Sale, Purchase
from ..schemas.product import InventorySummary, ProductResponse
from ..models.user import User
from ..routes.auth import get_current_user, get_admin_user  # Import corregido

router = APIRouter()

@router.get("/inventory-summary", response_model=InventorySummary)
async def inventory_summary(
    low_stock_threshold: int = Query(5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_products = db.query(Product).count()
    total_stock_value = db.query(func.sum(Product.price * Product.quantity)).scalar() or 0.0
    low_stock_items = db.query(Product).filter(Product.quantity <= low_stock_threshold).all()
    
    return InventorySummary(
        total_products=total_products,
        total_stock_value=total_stock_value,
        low_stock_items=low_stock_items
    )

@router.get("/sales-report", response_model=List[dict])
async def sales_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale)
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)
        
    sales = query.all()
    return [{
        "id": sale.id,
        "total": sale.total_amount,
        "date": sale.created_at.isoformat(),
        "items": len(sale.items)
    } for sale in sales]

@router.get("/stock-movements-report", response_model=List[dict])
async def stock_movements_report(
    product_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StockMovement)
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if start_date:
        query = query.filter(StockMovement.movement_date >= start_date)
    if end_date:
        query = query.filter(StockMovement.movement_date <= end_date)
        
    movements = query.all()
    return [{
        "id": mov.id,
        "product_id": mov.product_id,
        "quantity": mov.quantity_change,
        "type": mov.movement_type,
        "date": mov.movement_date.isoformat()
    } for mov in movements]