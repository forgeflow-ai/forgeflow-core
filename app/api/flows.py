from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.flow import Flow
from app.models.flow_run import FlowRun, FlowRunStatus

router = APIRouter(tags=["flows"])


# Request/Response Models
class ProjectCreate(BaseModel):
    """Project creation request model."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")


class ProjectResponse(BaseModel):
    """Project response model."""
    id: int = Field(..., description="Project ID")
    owner_id: int = Field(..., description="Owner user ID")
    name: str = Field(..., description="Project name")
    created_at: str = Field(..., description="ISO 8601 timestamp in UTC")
    updated_at: str = Field(..., description="ISO 8601 timestamp in UTC")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "owner_id": 1,
                "name": "My Project",
                "created_at": "2025-12-31T00:00:00Z",
                "updated_at": "2025-12-31T00:00:00Z"
            }
        }


class FlowCreate(BaseModel):
    """Flow creation request model."""
    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., min_length=1, max_length=200, description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")


class FlowResponse(BaseModel):
    """Flow response model."""
    id: int = Field(..., description="Flow ID")
    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    created_at: str = Field(..., description="ISO 8601 timestamp in UTC")
    updated_at: str = Field(..., description="ISO 8601 timestamp in UTC")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "project_id": 1,
                "name": "My Flow",
                "description": "Flow description",
                "created_at": "2025-12-31T00:00:00Z",
                "updated_at": "2025-12-31T00:00:00Z"
            }
        }


class FlowRunResponse(BaseModel):
    """Flow run response model."""
    id: int = Field(..., description="Flow run ID")
    flow_id: int = Field(..., description="Flow ID")
    status: str = Field(..., description="Flow run status")
    created_at: str = Field(..., description="ISO 8601 timestamp in UTC")
    started_at: Optional[str] = Field(None, description="ISO 8601 timestamp in UTC")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp in UTC")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "flow_id": 1,
                "status": "pending",
                "created_at": "2025-12-31T00:00:00Z",
                "started_at": None,
                "completed_at": None
            }
        }


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Create a new project.
    
    Requires authentication via API key.
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    project = Project(
        owner_id=current_user.id,
        name=project_data.name
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner_id,
        name=project.name,
        created_at=project.created_at.isoformat() + "Z",
        updated_at=project.updated_at.isoformat() + "Z"
    )


@router.post("/flows", response_model=FlowResponse, status_code=201)
def create_flow(
    flow_data: FlowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FlowResponse:
    """
    Create a new flow in a project.
    
    Requires authentication via API key.
    Project must exist and belong to the authenticated user.
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == flow_data.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found or access denied"
        )
    
    flow = Flow(
        project_id=flow_data.project_id,
        name=flow_data.name,
        description=flow_data.description
    )
    
    db.add(flow)
    db.commit()
    db.refresh(flow)
    
    return FlowResponse(
        id=flow.id,
        project_id=flow.project_id,
        name=flow.name,
        description=flow.description,
        created_at=flow.created_at.isoformat() + "Z",
        updated_at=flow.updated_at.isoformat() + "Z"
    )


@router.post("/flows/{flow_id}/run", response_model=FlowRunResponse, status_code=201)
def run_flow(
    flow_id: int = Path(..., description="Flow ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FlowRunResponse:
    """
    Create a flow run (execution record) for a flow.
    
    Requires authentication via API key.
    Flow must exist and belong to a project owned by the authenticated user.
    For now, this only creates a run record without actual execution.
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    # Verify flow exists and belongs to user's project
    flow = db.query(Flow).join(Project).filter(
        Flow.id == flow_id,
        Project.owner_id == current_user.id
    ).first()
    
    if flow is None:
        raise HTTPException(
            status_code=404,
            detail="Flow not found or access denied"
        )
    
    # Create flow run
    flow_run = FlowRun(
        flow_id=flow_id,
        status=FlowRunStatus.PENDING
    )
    
    db.add(flow_run)
    db.commit()
    db.refresh(flow_run)
    
    return FlowRunResponse(
        id=flow_run.id,
        flow_id=flow_run.flow_id,
        status=flow_run.status.value,
        created_at=flow_run.created_at.isoformat() + "Z",
        started_at=flow_run.started_at.isoformat() + "Z" if flow_run.started_at else None,
        completed_at=flow_run.completed_at.isoformat() + "Z" if flow_run.completed_at else None
    )

