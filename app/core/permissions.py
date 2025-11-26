from typing import TYPE_CHECKING

from app.models.user import UserRole

if TYPE_CHECKING:
    from app.models.user import User


def can_access(user: "User", member_ids: set[int], creator_id: int | None = None) -> bool:
    is_member = user.id in member_ids

    match user.role:
        case UserRole.ADMIN:
            return True
        case UserRole.MANAGER:
            return is_member
        case _:
            if creator_id is None:
                return is_member

            return is_member and user.id == creator_id
