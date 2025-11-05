# rpcframework

Lightweight JSON-RPC 2.0 framework for Python — built on top of **FastAPI**, **anyio** and **uvicorn**.
Designed for simple, fast development of JSON-RPC services with decorator-based method registration, async support, notifications and batch requests.

---

## Table of contents

* [Overview](#overview)
* [Key features](#key-features)
* [Install](#install)
* [Quickstart — server](#quickstart---server)
* [Quickstart — client](#quickstart---client)
* [Components & architecture](#components--architecture)
* [Examples](#examples)
* [Production readiness checklist](#production-readiness-checklist)
* [Contributing](#contributing)
* [License](#license)

---

## Overview

**rpcframework** makes building JSON-RPC 2.0 services fast, simple and predictable.

* **Register functions as RPC methods:** decorate a Python function and it becomes an RPC method callable by clients — no manual HTTP route wiring required.
* **First-class async & sync support:** both `async def` and regular functions are supported transparently; the framework handles awaiting and invocation semantics for you.
* **Notifications & batch requests:** supports fire-and-forget notifications (`id = null`) and JSON-RPC batch requests to reduce network overhead and improve throughput.
* **Transport-agnostic design:** currently ships with an HTTP transport (FastAPI); architecture allows alternative transports (STDIO, SSE, streamable HTTP) without changing business logic.
* **Introspection:** a `/methods` endpoint exposes available RPC methods and their signatures to help development and discoverability.

**How it simplifies development**

* **Minimal boilerplate:** write your business logic as plain functions and expose them via a decorator — the framework handles parsing, validation and response formatting.
* **Built-in error mapping:** JSON-RPC standard error codes and structured error objects are supported so clients get consistent error responses.
* **Async-ready:** seamless async support enables efficient I/O-bound services.
* **Easy client integration:** an async client (`JSONRPCTransport`) provides `call`, `notify`, and `batch` helpers for straightforward client usage.

---

## Key features

* JSON-RPC 2.0 request/response model (requests, responses, error objects, notifications, batch requests)
* Decorator-based registration via `RPCMethodRegistry.register`
* Async-first design — supports `async` handlers and sync handlers transparently
* Transport-agnostic registry design (HTTP implemented; STDIO/SSE placeholders)
* Built-in introspection (`/methods`) for developer convenience

---

## Install

Create a virtual environment and install dependencies (example `requirements.txt` should include `fastapi`, `uvicorn`, `httpx`, `pydantic`, `anyio`):

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Quickstart — server

Minimal server using the registry and decorator API:

```python
# examples/simple_server.py
from rpcframework.server.registry import RPCMethodRegistry

settings = {"host": "127.0.0.1", "port": 8001, "mount_path": "/jsonrpc"}
rpc = RPCMethodRegistry(name="example", settings=settings)

@rpc.register("add", description="Add two numbers")
def add(a: float, b: float) -> float:
    return a + b

@rpc.register("divide", description="Divide two numbers")
def divide(a: float, b: float) -> float:
    if float(b) == 0:
        raise ValueError("Division by zero")
    return float(a) / float(b)

if __name__ == "__main__":
    rpc.run(host="127.0.0.1", port=8001)
```

Run:

```bash
python examples/simple_server.py
```

Server listens at `http://127.0.0.1:8001/jsonrpc`. Introspection is available at `http://127.0.0.1:8001/methods` (protect in production).

---

## Quickstart — client

Example async client usage via `JSONRPCTransport`:

```python
# examples/simple_client.py
import asyncio
from rpcframework.client.client import JSONRPCTransport

async def main():
    transport = JSONRPCTransport("http://127.0.0.1:8001/jsonrpc")
    try:
        res = await transport.call("add", [3, 5])           # => 8
        print("add:", res)

        res = await transport.call("divide", {"a": 10, "b": 2})
        print("divide:", res)

        # notification (fire-and-forget)
        await transport.notify("some_notification", {"msg": "hello"})

        # batch example
        batch = [
            {"jsonrpc": "2.0", "method": "add", "params": [1,2], "id": "1"},
            {"jsonrpc": "2.0", "method": "divide", "params": {"a": 6,"b": 3}, "id": "2"},
        ]
        batch_resp = await transport.batch(batch)
        print("batch resp:", batch_resp)
    finally:
        await transport.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Components & architecture

Concise description of the main modules included in the repository:

### `schemas.py` (Pydantic models)

Defines the canonical JSON-RPC shapes: `RPCRequest`, `RPCErrorObject`, and `RPCResponse`. Pydantic ensures consistent validation and (de)serialization.

### `errors.py`

Provides the `JSONRPCError` dataclass and helper factories (`PARSE_ERROR`, `INVALID_REQUEST`, `METHOD_NOT_FOUND`, `INVALID_PARAMS`, `INTERNAL_ERROR`, `SERVER_ERROR`) so server-side errors map to standard JSON-RPC error objects.

### `transport.py` (client)

`JSONRPCTransport` is an async httpx wrapper exposing `call`, `notify`, `batch`, and `close` helpers for client communication.

### `_MethodWrapper` (registry internals)

Wraps registered functions, capturing metadata (name, description, param types, return type, optional JSON schema). Provides helpers for introspection and parameter validation.

### `dispatcher.py`

Invokes registered methods (supporting both sync and async handlers) and converts runtime errors into JSON-RPC errors.

### `transport/http.py` (HTTPTransport)

FastAPI handler that parses requests, supports single & batch payloads, handles notifications, and returns structured `RPCResponse` objects.

### `server/registry.py` (`RPCMethodRegistry`)

Primary API: method registration, method listing (introspection), and `run()` with multiple transport options (HTTP and STDIO implemented; SSE/streamable HTTP placeholders).

---

## Examples

* **Minimal**: `examples/simple_server.py` and `examples/simple_client.py` (add/divide demo).
* **Real-world idea**: `examples/invoice_server.py` and `examples/invoice_client.py` to demonstrate invoice creation, listing and asynchronous payment notifications (demo uses in-memory store).

---

## Contributing

Contributions welcome. Suggested first issues:

* Fix parameter binding in `_MethodWrapper.validate_params`.
* Normalize and secure HTTP error responses in `HTTPTransport._make_response`.
* Add `.gitattributes` to normalize line endings and an examples folder.

Workflow: fork → branch `feature/...` → tests → PR.

---

## License

This project is licensed under the **MIT License**.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software, under the following conditions:

* You must include the original copyright notice and this permission notice in all copies or substantial portions of the software.
* The software is provided "as is", without warranty of any kind, express or implied.

For more details, see the [MIT License](https://opensource.org/licenses/MIT).
