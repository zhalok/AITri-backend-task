from app.core.base import BaseRepository
from app.modules.company.models import Company


class CompanyRepository(BaseRepository[Company]):
    model = Company
