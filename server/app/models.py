"""Imports every model so Base.metadata (and Alembic) sees all tables."""
from app.modules.issue.models import Issue  # noqa: F401
from app.modules.measurable.models import Measurable  # noqa: F401
from app.modules.meeting.models import Meeting, MeetingAttendee, MeetingRating  # noqa: F401
from app.modules.milestone.models import Milestone  # noqa: F401
from app.modules.rock.models import Rock  # noqa: F401
from app.modules.score.models import Score  # noqa: F401
from app.modules.team.models import Membership, Team  # noqa: F401
from app.modules.todo.models import Todo  # noqa: F401
from app.modules.user.models import User  # noqa: F401
