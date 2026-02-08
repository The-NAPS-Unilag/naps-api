from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.user_activity import UserActivity


@dataclass
class ActivityResult:
    success: bool
    data: Optional[List[UserActivity]] = None
    error: Optional[str] = None


def create_activity(user_id: int, action: str, description: str) -> ActivityResult:
    try:
        activity = UserActivity(
            user_id=user_id,
            action=action,
            description=description
        )
        db.session.add(activity)
        db.session.commit()
        return ActivityResult(success=True, data=[activity])
    except SQLAlchemyError as e:
        db.session.rollback()
        return ActivityResult(success=False, error=str(e))


def get_user_activity(user_id: int, limit: int = 20, offset: int = 0) -> ActivityResult:
    try:
        activities = (
            UserActivity.query
            .filter_by(user_id=user_id)
            .order_by(UserActivity.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return ActivityResult(success=True, data=activities)
    except SQLAlchemyError as e:
        return ActivityResult(success=False, error=str(e))
