
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from config.db import get_db
from schemas.product import (
    ProductCreate, ProductResponse, ProductUpdate, 
    StockMovementCreate, StockMovementResponse,
    SaleCreate, SaleResponse,
    PurchaseCreate, PurchaseResponse,
    InventorySummary
)
from models.user import User
from models.product import Product, StockMovement, Sale, SaleItem, Purchase, PurchaseItem
from routes.auth import get_current_user, get_admin_user

# Crear router
router = APIRouter()

# Rutas para productos

@router.post(
    "/", 
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo producto",
    description="Añade un producto al inventario"
)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar si ya existe un producto con ese nombre
    existing_product = db.query(Product).filter(Product.name == product_data.name).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un producto con ese nombre"
        )
    
    # Crear producto
    db_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        quantity=product_data.quantity
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Registrar movimiento inicial si hay stock
    if product_data.quantity > 0:
        stock_movement = StockMovement(
            product_id=db_product.id,
            quantity_change=product_data.quantity,
            movement_type="inventario_inicial",
            created_by=current_user.id,
            notes="Inventario inicial al crear el producto"
        )
        db.add(stock_movement)
        db.commit()
    
    return db_product

@router.get(
    "/", 
    response_model=List[ProductResponse],
    summary="Lista todos los productos",
    description="Obtiene la lista de todos los productos en el inventario"
)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, description="Búsqueda por nombre o descripción"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)
    
    # Filtrar por término de búsqueda
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | 
            (Product.description.ilike(f"%{search}%"))
        )
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get(
    "/{product_id}", 
    response_model=ProductResponse,
    summary="Obtiene un producto por ID",
    description="Obtiene los detalles de un producto específico"
)
async def get_product(
    product_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

@router.put(
    "/{product_id}", 
    response_model=ProductResponse,
    summary="Actualiza un producto",
    description="Actualiza la información de un producto"
)
async def update_product(
    product_id: int = Path(..., ge=1),
    product_data: ProductUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buscar producto
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Verificar si se está cambiando el nombre y si ya existe
    if product_data.name and product_data.name != product.name:
        existing_product = db.query(Product).filter(Product.name == product_data.name).first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con ese nombre"
            )
    
    # Registrar movimiento de stock si se está actualizando la cantidad
    old_quantity = product.quantity
    
    # Actualizar datos
    product_data_dict = product_data.dict(exclude_unset=True)
    for key, value in product_data_dict.items():
        setattr(product, key, value)
    
    # Si se cambia la cantidad, registrar movimiento
    if "quantity" in product_data_dict and product_data.quantity != old_quantity:
        quantity_change = product_data.quantity - old_quantity
        if quantity_change != 0:
            stock_movement = StockMovement(
                product_id=product.id,
                quantity_change=quantity_change,
                movement_type="ajuste",
                created_by=current_user.id,
                notes=f"Ajuste manual: {old_quantity} -> {product_data.quantity}"
            )
            db.add(stock_movement)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete(
    "/{product_id}", 
    status_code=status.HTTP_200_OK,
    summary="Elimina un producto",
    description="Elimina un producto del inventario"
)
async def delete_product(
    product_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo administradores
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Eliminar el producto (las relaciones se eliminarán en cascada)
    db.delete(product)
    db.commit()
    
    return {"message": "Producto eliminado exitosamente"}

# Rutas para movimientos de stock

@router.post(
    "/stock-movements", 
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un movimiento de stock",
    description="Añade un movimiento de entrada o salida de stock"
)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que el producto existe
    product = db.query(Product).filter(Product.id == movement_data.product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Verificar si es una salida y hay suficiente stock
    if movement_data.quantity_change < 0 and (product.quantity + movement_data.quantity_change) < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay suficiente stock para realizar esta operación"
        )
    
    # Crear movimiento
    db_movement = StockMovement(
        product_id=movement_data.product_id,
        quantity_change=movement_data.quantity_change,
        movement_type=movement_data.movement_type,
        reference=movement_data.reference,
        notes=movement_data.notes,
        created_by=current_user.id
    )
    
    # Actualizar stock del producto
    product.quantity += movement_data.quantity_change
    
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    
    return db_movement

@router.get(
    "/stock-movements", 
    response_model=List[StockMovementResponse],
    summary="Lista movimientos de stock",
    description="Obtiene el historial de movimientos de stock"
)
async def get_stock_movements(
    product_id: Optional[int] = Query(None, description="Filtrar por ID de producto"),
    movement_type: Optional[str] = Query(None, description="Filtrar por tipo de movimiento"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StockMovement)
    
    # Aplicar filtros
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    # Ordenar por fecha descendente
    query = query.order_by(StockMovement.movement_date.desc())
    
    movements = query.offset(skip).limit(limit).all()
    return movements

# Rutas para ventas

@router.post(
    "/sales", 
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra una venta",
    description="Crea un registro de venta y actualiza el inventario"
)
async def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que haya al menos un item
    if not sale_data.items or len(sale_data.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La venta debe tener al menos un producto"
        )
    
    # Crear venta
    db_sale = Sale(
        customer_name=sale_data.customer_name,
        payment_method=sale_data.payment_method,
        total_amount=0,  # Se calculará después
        created_by=current_user.id
    )
    
    db.add(db_sale)
    db.flush()  # Para obtener el ID de la venta
    
    total_amount = 0
    
    # Procesar cada item
    for item_data in sale_data.items:
        # Verificar que el producto existe
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if product is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {item_data.product_id} no encontrado"
            )
        
        # Verificar stock
        if product.quantity < item_data.quantity:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para el producto '{product.name}'"
            )
        
        # Calcular subtotal
        subtotal = product.price * item_data.quantity
        total_amount += subtotal
        
        # Crear item de venta
        sale_item = SaleItem(
            sale_id=db_sale.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=product.price,
            subtotal=subtotal
        )
        
        db.add(sale_item)
        
        # Actualizar stock
        product.quantity -= item_data.quantity
        
        # Registrar movimiento de stock
        stock_movement = StockMovement(
            product_id=product.id,
            quantity_change=-item_data.quantity,
            movement_type="venta",
            reference=f"Venta #{db_sale.id}",
            created_by=current_user.id
        )
        
        db.add(stock_movement)
    
    # Actualizar total
    db_sale.total_amount = total_amount
    
    db.commit()
    db.refresh(db_sale)
    
    return db_sale

@router.get(
    "/sales", 
    response_model=List[SaleResponse],
    summary="Lista ventas",
    description="Obtiene la lista de ventas registradas"
)
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale)
    
    # Aplicar filtros de fecha
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)
    
    # Ordenar por fecha descendente
    query = query.order_by(Sale.created_at.desc())
    
    sales = query.offset(skip).limit(limit).all()
    return sales

@router.get(
    "/sales/{sale_id}", 
    response_model=SaleResponse,
    summary="Obtiene una venta por ID",
    description="Obtiene los detalles de una venta específica"
)
async def get_sale(
    sale_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if sale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    return sale

# Rutas para compras

@router.post(
    "/purchases", 
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra una compra",
    description="Crea un registro de compra y actualiza el inventario"
)
async def create_purchase(
    purchase_data: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que haya al menos un item
    if not purchase_data.items or len(purchase_data.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La compra debe tener al menos un producto"
        )
    
    # Crear compra
    db_purchase = Purchase(
        supplier_name=purchase_data.supplier_name,
        reference=purchase_data.reference,
        total_amount=0,  # Se calculará después
        created_by=current_user.id
    )
    
    db.add(db_purchase)
    db.flush()  # Para obtener el ID de la compra
    
    total_amount = 0
    
    # Procesar cada item
    for item_data in purchase_data.items:
        # Verificar que el producto existe
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if product is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {item_data.product_id} no encontrado"
            )
        
        # Calcular subtotal
        subtotal = item_data.unit_price * item_data.quantity
        total_amount += subtotal
        
        # Crear item de compra
        purchase_item = PurchaseItem(
            purchase_id=db_purchase.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            subtotal=subtotal
        )
        
        db.add(purchase_item)
        
        # Actualizar stock
        product.quantity += item_data.quantity
        
        # Registrar movimiento de stock
        stock_movement = StockMovement(
            product_id=product.id,
            quantity_change=item_data.quantity,
            movement_type="compra",
            reference=f"Compra #{db_purchase.id}",
            created_by=current_user.id
        )
        
        db.add(stock_movement)
    
    # Actualizar total
    db_purchase.total_amount = total_amount
    
    db.commit()
    db.refresh(db_purchase)
    
    return db_purchase

@router.get(
    "/purchases", 
    response_model=List[PurchaseResponse],
    summary="Lista compras",
    description="Obtiene la lista de compras registradas"
)
async def get_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Purchase)
    
    # Aplicar filtros de fecha
    if start_date:
        query = query.filter(Purchase.created_at >= start_date)
    if end_date:
        query = query.filter(Purchase.created_at <= end_date)
    
    # Ordenar por fecha descendente
    query = query.order_by(Purchase.created_at.desc())
    
    purchases = query.offset(skip).limit(limit).all()
    return purchases

@router.get(
    "/purchases/{purchase_id}", 
    response_model=PurchaseResponse,
    summary="Obtiene una compra por ID",
    description="Obtiene los detalles de una compra específica"
)
async def get_purchase(
    purchase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if purchase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compra no encontrada"
        )
    return purchase

# Ruta para obtener resumen de inventario
@router.get(
    "/summary", 
    response_model=InventorySummary,
    summary="Resumen de inventario",
    description="Obtiene un resumen del estado actual del inventario"
)
async def get_inventory_summary(
    low_stock_threshold: int = Query(5, description="Umbral para considerar bajo stock"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Contar productos
    total_products = db.query(Product).count()
    
    # Calcular valor total del inventario
    total_stock_value = db.query(
        db.func.sum(Product.price * Product.quantity)
    ).scalar() or 0
    
    # Productos con bajo stock
    low_stock_items = db.query(Product).filter(
        Product.quantity <= low_stock_threshold
    ).all()
    
    return {
        "total_products": total_products,
        "total_stock_value": total_stock_value,
        "low_stock_items": low_stock_items
    }