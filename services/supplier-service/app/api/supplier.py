import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])


@router.get("/shared", response_model=list[SupplierResponse])
async def list_shared_suppliers(
    search: Optional[str] = Query(None),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all shared (global) suppliers."""
    query = select(Supplier).where(Supplier.is_shared == True)  # noqa: E712
    if search:
        query = query.where(
            or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.reg_code.ilike(f"%{search}%"),
                Supplier.vat_code.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}", response_model=list[SupplierResponse])
async def list_company_suppliers(
    company_id: uuid.UUID,
    search: Optional[str] = Query(None),
    include_shared: bool = Query(True),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List suppliers for a company, optionally including shared suppliers."""
    conditions = [Supplier.company_id == company_id]
    if include_shared:
        conditions = [or_(Supplier.company_id == company_id, Supplier.is_shared == True)]  # noqa: E712

    query = select(Supplier).where(*conditions)
    if search:
        query = query.where(
            or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.reg_code.ilike(f"%{search}%"),
                Supplier.vat_code.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{company_id}", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    company_id: uuid.UUID,
    payload: SupplierCreate,
    promote_to_shared: bool = Query(False),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    supplier = Supplier(
        company_id=company_id,
        is_shared=promote_to_shared,
        created_by=current_user_id,
        email=str(payload.email) if payload.email else None,
        **{k: v for k, v in payload.model_dump(exclude={"email"}).items()},
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get("/{company_id}/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    company_id: uuid.UUID,
    supplier_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Supplier).where(
            Supplier.id == supplier_id,
            or_(Supplier.company_id == company_id, Supplier.is_shared == True),  # noqa: E712
        )
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.patch("/{company_id}/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    company_id: uuid.UUID,
    supplier_id: uuid.UUID,
    payload: SupplierUpdate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.company_id == company_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(supplier, field, value)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.delete("/{company_id}/{supplier_id}")
async def delete_supplier(
    company_id: uuid.UUID,
    supplier_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.company_id == company_id)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    await db.delete(supplier)
    await db.commit()
    return {"message": "Supplier deleted"}
