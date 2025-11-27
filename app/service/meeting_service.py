from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors.exceptions import (
    ForbiddenAccessError,
    InvalidMeetingParticipantError,
    MeetingTimeConflictError,
    ObjectNotFoundError,
)
from app.models import Meeting, Team, User
from app.models.association import meeting_participants
from app.schemas.meeting import MeetingCreate


class MeetingService:
    """Service for managing meetings."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize meeting service.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session

    async def _check_time_conflict(
        self,
        start_time: datetime,
        end_time: datetime,
        participant_ids: list[int],
    ) -> bool:
        """
        Check if meeting time conflicts with existing meetings for any participant.

        Returns True if there's a conflict, False otherwise.
        """
        stmt = select(
            exists().where(
                Meeting.id == meeting_participants.c.meeting_id,
                meeting_participants.c.user_id.in_(participant_ids),
                and_(
                    Meeting.start_time < end_time,
                    Meeting.end_time > start_time,
                ),
            ),
        )

        return bool(await self.session.scalar(stmt))

    async def _validate_participants(self, team_id: int, participant_ids: list[int]) -> Sequence[User]:
        """Validate that all participants are from the same team."""
        if not participant_ids:
            return []

        query = select(User).join(User.teams).where(User.id.in_(participant_ids), Team.id == team_id)

        result = await self.session.execute(query)
        valid_users = result.scalars().all()

        if len(valid_users) != len(participant_ids):
            raise InvalidMeetingParticipantError

        return valid_users

    async def create_meeting(
        self,
        meeting_data: MeetingCreate,
        organizer_id: int,
    ) -> Meeting:
        """Create a new meeting."""
        team = await self.session.get(Team, meeting_data.team_id)
        if not team:
            msg = "Team"
            raise ObjectNotFoundError(msg)

        all_participant_ids = list({*meeting_data.participant_ids, organizer_id})
        participants = await self._validate_participants(meeting_data.team_id, all_participant_ids)

        has_conflict = await self._check_time_conflict(
            meeting_data.start_time,
            meeting_data.end_time,
            all_participant_ids,
        )

        if has_conflict:
            raise MeetingTimeConflictError

        meeting = Meeting(
            title=meeting_data.title,
            description=meeting_data.description,
            start_time=meeting_data.start_time,
            end_time=meeting_data.end_time,
            team_id=meeting_data.team_id,
            organizer_id=organizer_id,
            participants=list(participants),
        )

        self.session.add(meeting)
        await self.session.commit()
        await self.session.refresh(meeting)

        return meeting

    async def get_meeting(self, meeting_id: int, user_id: int) -> Meeting:
        """Get meeting by ID."""
        query = select(Meeting).options(selectinload(Meeting.participants)).where(Meeting.id == meeting_id)

        result = await self.session.execute(query)
        meeting = result.scalar_one_or_none()

        if not meeting:
            msg = "Meeting"
            raise ObjectNotFoundError(msg)

        participant_ids = [p.id for p in meeting.participants]
        if user_id not in participant_ids and user_id != meeting.organizer_id:
            raise ForbiddenAccessError

        return meeting

    async def get_user_meetings(
        self,
        user_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Meeting]:
        """Get all meetings for a user within optional date range."""
        query = (
            select(Meeting)
            .join(Meeting.participants)
            .options(selectinload(Meeting.participants))
            .where(User.id == user_id)
        )

        if start_date:
            query = query.where(Meeting.end_time >= start_date)
        if end_date:
            query = query.where(Meeting.start_time <= end_date)

        query = query.order_by(Meeting.start_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def cancel_meeting(self, meeting_id: int, user_id: int) -> None:
        """Cancel (delete) a meeting."""
        meeting = await self.get_meeting(meeting_id, user_id)

        # Only organizer can cancel
        if meeting.organizer_id != user_id:
            raise ForbiddenAccessError

        await self.session.delete(meeting)
        await self.session.commit()
