"""FR12 optional explicit satisfaction feedback; no conversation/PII payload."""
import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint,DateTime,ForeignKey,Integer,String,Uuid
from sqlalchemy.orm import Mapped,mapped_column
from app.models.base import Base
from app.time_utils import utcnow

class SatisfactionFeedback(Base):
    __tablename__='satisfaction_feedback'
    user_id:Mapped[uuid.UUID]=mapped_column(Uuid,ForeignKey('users.id',ondelete='CASCADE'),primary_key=True)
    rating:Mapped[int]=mapped_column(Integer)
    mode:Mapped[str]=mapped_column(String(20))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(CheckConstraint('rating BETWEEN 1 AND 5',name='rating_range'),CheckConstraint("mode IN ('disabled','retrieval')",name='mode_allowed'))
