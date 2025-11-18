from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime
import sqlite3
import json

# Pydantic model for Agent information
class AgentCard(BaseModel):
    name: str = Field(..., description="Unique name of the agent (e.g., billing-agent)")
    version: str = Field("1.0.0", description="Agent version identifier")
    endpoint: HttpUrl = Field(..., description="Main RPC endpoint URL of the agent")
    health_url: Optional[HttpUrl] = Field(None, description="Health check URL")
    capabilities: List[str] = Field(..., description="List of functions this agent can perform")
    description: Optional[str] = Field(None, description="Short summary of what this agent does")
    registered_at: datetime = Field(default_factory=datetime.utcnow,
                                   description="Auto timestamp when registered")
    meta: Optional[dict] = Field(default_factory=dict,
                                 description="Additional metadata or labels for discovery")

# Initialize FastAPI app
app = FastAPI(title="Service Discovery", description="Central registry for agent discovery")

# Setup SQLite for persistent storage
conn = sqlite3.connect("discovery.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    version TEXT,
    endpoint TEXT,
    health_url TEXT,
    capabilities TEXT,
    description TEXT,
    registered_at TEXT,
    meta TEXT
)""")
conn.commit()

@app.post("/register", response_model=AgentCard, status_code=201)
async def register_agent(agent: AgentCard):
    """
    Register a new agent with its AgentCard.
    """
    try:
        # method = method.lower()
        # cursor.execute(
        #     "SELECT * FROM agents WHERE capabilities LIKE ?",
        #     (f"%{method}%",)
        # )
        # Insert or replace the agent record in SQLite
        cursor.execute(
            """
            INSERT OR REPLACE INTO agents 
            (name, version, endpoint, health_url, capabilities, description, registered_at, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent.name,
                agent.version,
                str(agent.endpoint),
                str(agent.health_url) if agent.health_url else None,
                json.dumps(agent.capabilities),
                agent.description,
                agent.registered_at.isoformat(),
                json.dumps(agent.meta),
            )
        )
        conn.commit()
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register agent: {e}")

@app.get("/discover", response_model=List[AgentCard])
async def discover_agent(method: str):
    """
    Discover agents that have the given method in their capabilities.
    """
    cursor.execute("SELECT * FROM agents")
    rows = cursor.fetchall()
    results = []
    for row in rows:
        caps = json.loads(row[4])
        if method in caps:
            results.append(AgentCard(
                name=row[0],
                version=row[1],
                endpoint=row[2],
                health_url=row[3] if row[3] else None,
                capabilities=caps,
                description=row[5],
                registered_at=datetime.fromisoformat(row[6]),
                meta=json.loads(row[7]) if row[7] else {}
            ))
    if not results:
        # If no agent found, return 404
        raise HTTPException(status_code=404, detail=f"No agent found providing '{method}'")
    return results

@app.get("/agents", response_model=List[AgentCard])
async def list_agents():
    """
    List all registered agents.
    """
    cursor.execute("SELECT * FROM agents")
    rows = cursor.fetchall()
    agents = []
    for row in rows:
        agents.append(AgentCard(
            name=row[0],
            version=row[1],
            endpoint=row[2],
            health_url=row[3] if row[3] else None,
            capabilities=json.loads(row[4]),
            description=row[5],
            registered_at=datetime.fromisoformat(row[6]),
            meta=json.loads(row[7]) if row[7] else {}
        ))
    return agents

@app.delete("/deregister/{agent_name}")
async def deregister_agent(agent_name: str):
    """
    Deregister an agent by name.
    """
    cursor.execute("DELETE FROM agents WHERE name = ?", (agent_name,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return JSONResponse(status_code=204, content=None)

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
