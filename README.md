# AgentMesh

> Production-grade Python framework for building distributed AI agent systems with centralized service discovery, subscription management, and JSON-RPC 2.0 communication.

AgentMesh allows developers to register specialized AI agents (text, vision, planning, etc.), discover them, subscribe (free/paid), and call them directly via JSON-RPC 2.0. It blends **FastAPI’s developer-friendly experience** with **service-mesh-inspired architecture**, without the overhead of Kubernetes.

---

## Table of Contents

* [Overview](#overview)
* [Key Features](#key-features)
* [Quickstart](#quickstart)
  * [Server](#server)
  * [Client](#client)
* [How AgentMesh Works](#how-agentmesh-works)
* [Examples](#examples)
* [Upcoming Features](#upcoming-features)
* [License](#license)

---

## Overview

Modern AI applications rely on multiple specialized agents:

* **Text agents** – NLP, summarization, translation
* **Vision agents** – Image analysis and generation
* **Planning agents** – Task orchestration
* **Domain-specific agents** – Specialized problem-solving

AgentMesh solves the challenge of **discovering, managing, and communicating** with distributed agents reliably.

---

## Key Features

* **Developer-Friendly Registration:** Developers register their AI agent by creating a RPCMethodRegistry, decorating agent methods with @register, and optionally enabling auto_register to automatically publish the agent to the discovery service with full metadata and capabilities.
* **Flexible Discovery:** Name-based and semantic search (future) for natural-language queries.
* **Subscription & Monetization:** Free, freemium, paid tiers; API keys, quotas, usage tracking.
* **Reliable RPC Calls:** JSON-RPC 2.0 compliant; direct agent communication; optional smart routing.
* **Production Ready:** Health monitoring, logging, extensible transport (HTTP/SSE), error handling, federated agents.

---

## Quickstart

### Server

```bash
# Run Discovery Service
python -m rpcframework.discovery.discovery_service
```

**Example Agent Registration:**

---

Developers can register their AI agent simply by creating an `RPCMethodRegistry` instance, decorating agent methods with `@register`, and optionally enabling `auto_register` to automatically register the agent with the central discovery service. The registry captures the agent’s **name, endpoint, capabilities, description, parameter types, and version**, allowing immediate introspection and RPC calls.

**Example:**

```python
from rpcframework.server.registry import RPCMethodRegistry, RegistrySettings

# Create agent registry with auto-registration enabled
registry = RPCMethodRegistry(
    name="weather-agent",
    settings=RegistrySettings(auto_register=True)
)

# Register an agent method
@registry.register(description="Fetch weather for a city")
async def get_weather(city: str):
    return {"city": city, "temperature": 22, "condition": "sunny"}

# Run the RPC server (FastAPI + HTTP)
registry.run(host="127.0.0.1", port=8001)
```

**Here the developer only needs to:**

1. Define a registry for their agent.
2. Decorate methods with `@register`.
3. Optionally rely on `auto_register=True` to publish to the discovery service.

---

### Client

```bash
# Run this after your discovery service and agents are running
```

**Example RPC Client Usage:**

---

Developers can interact with registered AI agents by creating an `RPCClient` instance. The client automatically queries the discovery service to find agents that support a specific method and then makes a JSON-RPC call to that agent. This abstracts away endpoint management and load balancing.

**Example:**

```python
from rpcframework.client.rpc_client import RPCClient
import asyncio

async def main():
    # Connect to the discovery service
    client = RPCClient()
    
    # Discover agents supporting the 'get_weather' method
    agents = await client.discover("get_weather")
    print(f"Found {len(agents)} agents")
    
    # Call the method on a selected agent
    result = await client.call("get_weather", params={"city": "London"})
    print(result)

asyncio.run(main())
```

**Here the developer only needs to:**

1. Instantiate `RPCClient`.
2. Call `discover("agent_name")` to find agents providing the required method.
3. Use `call("method_name", params=...)` to execute the RPC method on a discovered agent.
4. Let the client automatically select an agent and handle the JSON-RPC transport.

---

**Key Notes (from context):**

* `RPCClient` uses `DiscoveryClient` internally to query the discovery service.
* `call()` automatically performs **agent selection** (random load balancing) and sets up a `JSONRPCTransport` to communicate with the agent.
* Supports **async calls**, so you can integrate it easily into modern Python async applications.
* Developers do not need to know the actual endpoint of the agent; the discovery service handles it.

---


## How AgentMesh Works – Federated Agents & Centralized Discovery

AgentMesh is a Python framework that manages multiple independent AI agents through a centralized system.

* **Federated Agents:** Each AI agent (text, vision, planning, etc.) runs in its own instance and operates independently.
* **Centralized Discovery:** All agents register their metadata (name, capabilities, version) in a central registry. Clients can easily discover and call them without knowing their exact location.
* **Direct Communication:** Clients make direct JSON-RPC calls to agents, while the system automatically handles load balancing and endpoint management.
* **Subscription & Monetization:** Agents can be free or paid, and usage can be tracked for monetization.

**Flow:**

1. The developer creates an agent → it registers in the central registry with `auto_register=True`.
2. The client discovers the agent → the central discovery selects the best agent.
3. The client calls the agent → direct JSON-RPC communication takes place.
4. The system provides monitoring, logging, and fault-tolerance.

> Simple: Multiple independent agents, centralized registry, easy discovery & monetization, real-time calls.

---

## Examples

The **`examples/` folder** on GitHub contains two files demonstrating a decentralized AI agent network.

### **1. `customer_support_agent.py`**

An AI Customer Support Agent that handles billing, refunds, technical issues, and delivery queries.
Supports multiple languages and automatically registers with the RPC framework.

### **2. `test_customer_support.py`**

A test client that automatically discovers the agent, sends queries, checks agent health,
and shows which expert agent handled each query.

---

## Upcoming Features

We are currently enhancing the RPC client and discovery system with the following updates:

1. **Agent Subscription & Paid Access:**

   * Agent profiles returned by `find` will include a `subscribe` property.
   * Once subscribed, the `paid` flag will be set to `true`, and an **API key** will be issued to call that agent.
   * A new `subscribe` method will handle the subscription process.

2. **Enhanced Load Balancing:**

   * Currently, agents are selected randomly.
   * Future updates will introduce smarter **load-balancing** based on performance and availability.

3. **Semantic Search for Agents:**

   * Agent discovery is currently name-based.
   * We will add **semantic search** so clients can find agents based on capabilities and context, not just exact names.

> These features are in development and will be available in upcoming releases.

---

## License

MIT License © 2025 AgentMesh Contributors

