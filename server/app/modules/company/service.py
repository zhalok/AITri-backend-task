from app.core.base import BaseService
from app.modules.company.models import Company


class CompanyService(BaseService[Company]):
    entity_name = "Company"
