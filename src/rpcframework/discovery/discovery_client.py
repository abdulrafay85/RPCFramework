import httpx
import logging

class DiscoveryClient:
    """
    Client for interacting with the central Discovery Service.
    Handles agent registration and discovery lookups.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5.0)
        self.logger = logging.getLogger("DiscoveryClient")

    async def register_agent(self, agent_card: dict) -> None:
        """
        Register this agent by sending its AgentCard to the discovery service.
        """
        try:
            self.logger.debug(f"Registering agent: {agent_card.get('name')}")
            resp = await self.client.post(f"{self.base_url}/register", json=agent_card)
            resp.raise_for_status()
            self.logger.info(f"Registered agent {agent_card.get('name')}.")
        except httpx.RequestError as e:
            self.logger.error(f"Network error during agent registration: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during agent registration: {e}")
            raise

    async def find_agents(self, method: str) -> list[dict]:
        """
        Discover agents that provide a specific RPC method (capability).
        """
        try:
            self.logger.debug(f"Finding agents for method: {method}")
            resp = await self.client.get(f"{self.base_url}/discover", params={"method": method})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"No agents found providing: {method}")
                return []
            self.logger.error(f"HTTP error during discovery: {e}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Network error during discovery: {e}")
            raise
