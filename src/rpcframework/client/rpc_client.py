
import os
import random
# from rpcframework.config.default import discovery_url
from rpcframework.discovery.discovery_client import DiscoveryClient
from rpcframework.client.client import JSONRPCTransport


# Default Discovery URL (agar env variable na mila)
# DISCOVERY_URL = discovery_url

# Env se DISCOVERY_URL read karein warna default use ho
discovery_url: str = os.getenv("DISCOVERY_URL", "http://127.0.0.1:8000")
print(discovery_url)


class RPCClient:
    def __init__(self, discovery_url: str = discovery_url):
        # Discovery service se connect
        self.discovery = DiscoveryClient(discovery_url)

    async def find_agent(self, method: str):
        """
        Discovery service se un agents ki list lao
        jo yeh method support karte hain.
        """
        agents = await self.discovery.find_agents(method)

        if not agents:
            raise RuntimeError(f"No agents found for method: {method}")

        # Simple load balancer — random agent select
        return random.choice(agents)

    async def call(self, method: str, params: dict | list | None = None):
        """
        Public RPC call function.
        Yeh automatically agent choose karega aur uska method call karega.
        """

        # 1. Choose remote agent
        agent = await self.find_agent(method)
        # print(f"Selected agent: {agent}")

        # 2. Transport create using agent endpoint
        # print(f"Agent endpoint: {agent['endpoint']}")
        transport = JSONRPCTransport(agent["endpoint"])

        # 3. Actual RPC call
        # print(f"Calling method: {method} with params: {params}")
        return await transport.call_method(method, params)