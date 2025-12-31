from sqlalchemy import String, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class FlowRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowRun(Base):
    __tablename__ = "flow_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    flow_id: Mapped[int] = mapped_column(ForeignKey("flows.id", ondelete="CASCADE"), index=True, nullable=False)
    
    status: Mapped[FlowRunStatus] = mapped_column(SQLEnum(FlowRunStatus), nullable=False, default=FlowRunStatus.PENDING)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    flow = relationship("Flow", back_populates="runs")

