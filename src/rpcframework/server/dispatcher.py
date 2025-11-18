# jsonrpc_core/server/dispatcher.py
import inspect
import os
from rpcframework.config.default import DISCOVERY_URL  # default constant

import httpx
from typing import Any, Optional
from rpcframework.server.errors import INVALID_PARAMS, JSONRPCError, METHOD_NOT_FOUND
from typing import Callable, Any, Optional
from typing import TYPE_CHECKING
from rpcframework.discovery.discovery_client import DiscoveryClient
# from ..server.registry import RPCMethodRegistry

if TYPE_CHECKING:
    from rpcframework.server.registry import RPCMethodRegistry
# Version 1
# async def _call_fn(fn: Callable, params: Optional[Any]):
#     if params is None:
#         return await _maybe_await(fn)()
#     elif isinstance(params, list):
#         return await _maybe_await(fn)(*params)
#     elif isinstance(params, dict):
#         return await _maybe_await(fn)(**params)
#     else:
#         raise INVALID_PARAMS({"reason": "params must be list or dict"})

# def _maybe_await(fn):
#     if inspect.iscoroutinefunction(fn):
#         return fn
#     async def wrapper(*a, **kw):
#         return fn(*a, **kw)
#     return wrapper

# Version 2

async def _call_fn(fn: Callable, params: Optional[Any]):
    """
    Call `fn` (sync or async) with params (None | list | dict).
    Always return concrete result (never a coroutine).
    Raises INVALID_PARAMS if params type is wrong.
    """
    try:
        if params is None:
            result = fn() if not inspect.iscoroutinefunction(fn) else await fn()
        elif isinstance(params, list):
            result = fn(*params) if not inspect.iscoroutinefunction(fn) else await fn(*params)
        elif isinstance(params, dict):
            result = fn(**params) if not inspect.iscoroutinefunction(fn) else await fn(**params)
        else:
            raise INVALID_PARAMS({"reason": "params must be list or dict or null"})
    except TypeError as e:
        # likely wrong signature / bad params
        raise INVALID_PARAMS({"reason": str(e)})

    # If the function (sync) returned an awaitable, await it.
    if inspect.isawaitable(result):
        return await result
    return result


# ----------------------
## Version 1
# ----------------------

# class RPCDispatcher:
#     def __init__(self, registry: "RPCMethodRegistry"):
#         self.registry = registry
#         self.discovery_client = DiscoveryClient("http://localhost:8000")

#     async def dispatch(self, method: str, params: Optional[Any], request_id: Any = None):
#         fn = self.registry.get(method)
#         try:
#             result = await _call_fn(fn, params)
#             return {"result": result, "id": request_id}
#         except JSONRPCError:
#             raise
#         except TypeError as e:
#             raise INVALID_PARAMS({"reason": str(e)})
#         except Exception as e:
#             raise JSONRPCError(-32000, "Server error", str(e))

#         # ----------------------
#         # 2. DISCOVERY LOOKUP
#         # ----------------------
#         agents = await self.discovery_client.find_agents(method)
#         if not agents:
#             raise METHOD_NOT_FOUND({"method": method})



# ----------------------
## Version 2
# ----------------------

discovery_url: str = os.getenv("DISCOVERY_URL", DISCOVERY_URL)

class RPCDispatcher:
    def __init__(self, registry: "RPCMethodRegistry"):
        self.registry = registry
        self.discovery_client = DiscoveryClient(discovery_url)
        self.remote_call_timeout = 5
        self.retry_count = 2

        # round-robin pointer for load balancing
        self.agent_index = {}

    async def dispatch(self, method: str, params: Optional[Any], request_id: Any = None):
        # ----------------------
        # 1. TRY LOCAL FIRST
        # ----------------------
        try:
            fn = self.registry.get(method)  # raises if not found
            # print(f"funtion: {fn}")
            result = await _call_fn(fn, params)
            return {"result": result, "id": request_id}

        # except JSONRPCError:
        #     raise
        except Exception as e:
            # Wrap ANY python error into JSONRPCError
            raise JSONRPCError(-32000, "Server error", {"exception": str(e)})



    # #     # ----------------------
    # #     # 2. DISCOVER REMOTE AGENTS
    # #     # ----------------------
    #     agents = await self.discovery_client.find_agents(method)
    #     if not agents:
    #         raise METHOD_NOT_FOUND({"method": method})


    # # -----------------------------------------
    # # REMOTE CALL HANDLER
    # # -----------------------------------------
    # async def _call_remote_agent(self, agent, method, params, request_id):

    #     try:
    #         async with httpx.AsyncClient(timeout=self.remote_call_timeout) as client:
    #             payload = {
    #               "jsonrpc": "2.0",
    #               "method": method,
    #               "params": params,
    #               "id": request_id,
    #         }
    #         resp = await client.post(agent["endpoint"], json=payload)
    #         resp.raise_for_status()
    #         return resp.json()
    #     except Exception as e:
    #         raise JSONRPCError(-32050, "Remote agent request failed", str(e))
    