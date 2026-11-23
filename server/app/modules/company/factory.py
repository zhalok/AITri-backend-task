from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.company.repository import CompanyRepository
from app.modules.company.service import CompanyService


def get_company_repository(session: Session = Depends(get_session)) -> CompanyRepository:
    return CompanyRepository(session)


def get_company_service(repo: CompanyRepository = Depends(get_company_repository)) -> CompanyService:
    return CompanyService(repo)
