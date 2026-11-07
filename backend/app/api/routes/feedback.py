"""FR12 / NFR02–03: authenticated optional CSAT, one latest response per user."""
from fastapi import APIRouter,Depends
from pydantic import Field,StrictInt
from sqlalchemy.dialects.postgresql import insert
from app.api.deps import get_current_user,get_db,require_csrf,settings_dep
from app.models.feedback import SatisfactionFeedback
from app.schemas.models import ApiModel
from app.time_utils import utcnow,iso_manila
router=APIRouter(tags=['feedback'])
class SatisfactionInput(ApiModel):
    rating:StrictInt=Field(ge=1,le=5)
@router.post('/feedback/csat',dependencies=[Depends(require_csrf)])
def satisfaction(payload:SatisfactionInput,user=Depends(get_current_user),db=Depends(get_db),settings=Depends(settings_dep)):
    now=utcnow()
    statement=insert(SatisfactionFeedback).values(user_id=user.id,rating=payload.rating,mode=settings.assistant_mode,updated_at=now)
    db.execute(statement.on_conflict_do_update(index_elements=['user_id'],set_={'rating':payload.rating,'mode':settings.assistant_mode,'updated_at':now}))
    db.commit()
    return {'rating':payload.rating,'mode':settings.assistant_mode,'updated_at':iso_manila(now)}
