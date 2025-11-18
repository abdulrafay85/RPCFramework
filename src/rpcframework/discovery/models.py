from pydantic import BaseModel, HttpUrl, Field
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AgentCard(BaseModel):
    """
    AgentCard Model
    Represents the identity, metadata, and capabilities of an AI Agent.
    """
    name: str = Field(..., description="Unique name of the agent (e.g., billing-agent)")
    version: str = Field("1.0.0", description="Agent version identifier")
    endpoint: HttpUrl = Field(..., description="Main RPC endpoint URL of the agent")
    health_url: Optional[HttpUrl] = Field(None, description="Health check URL")
    capabilities: List[str] = Field(..., description="List of functions this agent can perform")
    description: Optional[str] = Field(None, description="Short summary of the agent’s purpose")
    registered_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of registration")
    meta: Optional[dict] = Field(default_factory=dict, description="Additional metadata (optional)")

