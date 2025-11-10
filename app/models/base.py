from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.core.config import settings
from app.utils.case_converter import camel_case_to_snake_case


class Base(DeclarativeBase):
    """Base class for all models."""

    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )

    @declared_attr.directive
    def __tablename__(self) -> str:
        return f"{camel_case_to_snake_case(self.__name__)}s"

    repr_cols_num = 3
    repr_cols: tuple[str, ...] = ()

    def __repr__(self) -> str:
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"
