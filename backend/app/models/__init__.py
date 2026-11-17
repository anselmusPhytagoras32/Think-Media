"""Model package exports (import order matters for metadata)."""

from app.models.audit import AuditEvent
from app.models.base import Base
from app.models.profiles import CompanyProfile, InstructorProfile, StudentProfile
from app.models.session import SessionToken
from app.models.user import User

__all__ = [
    "LearningContent",
    "LearningSubmission",
    "LearningReview",
    "QuizQuestion",
    "QuizAttempt",
    "ContentState",
    "ModerationReport",
    "ContentEvent",
    "Listing",
    "Application",
    "ApplicationStatusHistory",
    "MarketplaceEvent",
    "AttachmentRetentionEvent",
    "AuditEvent",
    "Base",
    "CompanyProfile",
    "InstructorProfile",
    "SessionToken",
    "StudentProfile",
    "User",
]

from app.models.learning import (
    ContentEvent,
    ContentState,
    LearningContent,
    ModerationReport,
    QuizAttempt,
    QuizQuestion,
)
from app.models.learning_submission import LearningReview, LearningSubmission
from app.models.marketplace import (
    Application,
    ApplicationStatusHistory,
    AttachmentRetentionEvent,
    Listing,
    MarketplaceEvent,
)
from app.models.recommendations import Interaction
__all__.append('Interaction')

from app.models.feedback import SatisfactionFeedback
