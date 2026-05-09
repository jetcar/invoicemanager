import uuid
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.company import Company, CompanyMember, CompanyStatus, Organization, OrganizationMember, UserRole
from app.schemas.company import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    CompanyMemberAdd,
    CompanyMemberResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMemberAdd,
)
from app.core.auth import get_current_user, get_current_superadmin

router = APIRouter(tags=["companies"])


# ──────────────────────────────────────────────
# Organizations
# ──────────────────────────────────────────────
@router.post("/api/v1/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = Organization(name=payload.name, description=payload.description, created_by=current_user_id)
    db.add(org)
    await db.flush()
    # Add creator as admin member
    db.add(OrganizationMember(organization_id=org.id, user_id=current_user_id, role="admin"))
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/api/v1/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == current_user_id)
    )
    return result.scalars().all()


@router.post("/api/v1/organizations/{org_id}/members")
async def add_organization_member(
    org_id: uuid.UUID,
    payload: OrganizationMemberAdd,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user_id,
            OrganizationMember.role == "admin",
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    member = OrganizationMember(organization_id=org_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    await db.commit()
    return {"message": "Member added"}


# ──────────────────────────────────────────────
# Companies
# ──────────────────────────────────────────────
@router.post("/api/v1/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key = secrets.token_urlsafe(32)
    company = Company(
        name=payload.name,
        reg_code=payload.reg_code,
        vat_code=payload.vat_code,
        address=payload.address,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        iban=payload.iban,
        organization_id=payload.organization_id,
        created_by=current_user_id,
        api_key=api_key,
    )
    db.add(company)
    await db.flush()
    db.add(CompanyMember(company_id=company.id, user_id=current_user_id, role=UserRole.ADMIN))
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/api/v1/companies", response_model=list[CompanyResponse])
async def list_companies(
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == current_user_id)
    )
    return result.scalars().all()


@router.get("/api/v1/companies/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await _get_company_with_access(company_id, current_user_id, db)
    return company


@router.patch("/api/v1/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await _get_company_with_role(company_id, current_user_id, UserRole.ADMIN, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return company


@router.post("/api/v1/companies/{company_id}/regenerate-api-key")
async def regenerate_api_key(
    company_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await _get_company_with_role(company_id, current_user_id, UserRole.ADMIN, db)
    company.api_key = secrets.token_urlsafe(32)
    await db.commit()
    return {"api_key": company.api_key}


# ──────────────────────────────────────────────
# Company verification (superadmin)
# ──────────────────────────────────────────────
@router.get("/api/v1/companies/pending", response_model=list[CompanyResponse])
async def list_pending_companies(
    admin_user_id: uuid.UUID = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.status == CompanyStatus.PENDING))
    return result.scalars().all()


@router.post("/api/v1/companies/{company_id}/verify")
async def verify_company(
    company_id: uuid.UUID,
    admin_user_id: uuid.UUID = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.status = CompanyStatus.VERIFIED
    company.verified_by = admin_user_id
    company.verified_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Company verified"}


@router.post("/api/v1/companies/{company_id}/reject")
async def reject_company(
    company_id: uuid.UUID,
    admin_user_id: uuid.UUID = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.status = CompanyStatus.REJECTED
    await db.commit()
    return {"message": "Company rejected"}


# ──────────────────────────────────────────────
# Company members
# ──────────────────────────────────────────────
@router.get("/api/v1/companies/{company_id}/members", response_model=list[CompanyMemberResponse])
async def list_members(
    company_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_company_with_access(company_id, current_user_id, db)
    result = await db.execute(select(CompanyMember).where(CompanyMember.company_id == company_id))
    return result.scalars().all()


@router.post("/api/v1/companies/{company_id}/members", response_model=CompanyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    company_id: uuid.UUID,
    payload: CompanyMemberAdd,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_company_with_role(company_id, current_user_id, UserRole.ADMIN, db)
    member = CompanyMember(company_id=company_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/api/v1/companies/{company_id}/members/{user_id}")
async def remove_member(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_company_with_role(company_id, current_user_id, UserRole.ADMIN, db)
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id, CompanyMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await db.delete(member)
    await db.commit()
    return {"message": "Member removed"}


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────
async def _get_company_with_access(company_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(Company.id == company_id, CompanyMember.user_id == user_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found or access denied")
    return company


async def _get_company_with_role(
    company_id: uuid.UUID, user_id: uuid.UUID, required_role: UserRole, db: AsyncSession
) -> Company:
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(
            Company.id == company_id,
            CompanyMember.user_id == user_id,
            CompanyMember.role == required_role,
        )
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{required_role.value} access required",
        )
    return company
