from __future__ import annotations

# # Versison 1
# from typing import Callable, Dict, Any
# from app.errors import METHOD_NOT_FOUND, INVALID_PARAMS, JSONRPCError

# class RPCRegistry:
#     def __init__(self):
#         self._methods: Dict[str, Callable[..., Any]] = {}

#     def register(self, name: str = None):
#         def decorator(fn: Callable[..., Any]):
#             key = name or fn.__name__
#             if key in self._methods:
#                 raise ValueError(f"RPC method {key} already registered")
#             self._methods[key] = fn
#             return fn
#         return decorator

#     async def dispatch(self, method_name: str, params):
#         if method_name not in self._methods:
#             raise METHOD_NOT_FOUND({"method": method_name})
#         fn = self._methods[method_name]
#         try:
#             # Support both positional (list) and keyword (dict) params
#             if params is None:
#                 return await maybe_await(fn)()
#             if isinstance(params, list):
#                 return await maybe_await(fn)(*params)
#             if isinstance(params, dict):
#                 return await maybe_await(fn)(**params)
#             # invalid params type
#             raise INVALID_PARAMS({"reason": "params must be list or dict"})
#         except JSONRPCError:
#             # pass through JSONRPCError for controlled error responses
#             raise
#         except TypeError as e:
#             raise INVALID_PARAMS({"reason": str(e)})
#         except Exception as e:
#             raise JSONRPCError(code=-32001, message="Unhandled server error", data=str(e))

# # small helper to support sync or async functions
# import inspect
# import asyncio
# def maybe_await(fn):
#     if inspect.iscoroutinefunction(fn):
#         return fn
#     # wrap sync function into coroutine
#     async def wrapper(*args, **kwargs):
#         return fn(*args, **kwargs)
#     return wrapper



## Version 2
# -------------------------------------

# jsonrpc_core/server/registry.py (continued)
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Type
import inspect
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# _MethodWrapper – Holds function + metadata
# ──────────────────────────────────────────────────────────────
@dataclass
class _MethodWrapper:
    """
    Wraps an RPC method with rich metadata for introspection, validation, and dispatch.

    This class is callable (behaves like the original function) and stores:
    - Original function
    - Name, description
    - Parameter types (from type hints)
    - Return type
    - Optional JSON schema for params
    """

    fn: Callable[..., Any]
    """Original function to be called."""

    name: str
    """RPC method name (as registered)."""

    description: str | None = None
    """Human-readable description of the method."""

    params_schema: dict | None = None
    """Optional JSON schema for parameter validation."""

    param_types: Dict[str, Type] = field(default_factory=dict)
    """Mapping of parameter name → type (from type hints)."""

    return_type: Optional[Type] = None
    """Return type of the function (from type hints)."""

    # ───── Make it callable (behaves like fn) ─────
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the original function."""
        return self.fn(*args, **kwargs)

    # ───── Helper: Is async? ─────
    @property
    def is_async(self) -> bool:
        """Check if the wrapped function is async."""
        return inspect.iscoroutinefunction(self.fn)

    # ───── Helper: Get signature ─────
    @property
    def signature(self) -> inspect.Signature:
        """Return the function signature."""
        return inspect.signature(self.fn)

    # ───── Validation (future-ready) ─────
    def validate_params(self, params: Any) -> None:
        """
        Validate incoming params against type hints or schema.
        Raise JSONRPCError(INVALID_PARAMS) on failure.
        """
        # from ..errors import INVALID_PARAMS

        if params is None:
            return

        sig = self.signature
        bound = sig.bind_partial(*([] if isinstance(params, list) else []), **({} if isinstance(params, dict) else {}))

        if isinstance(params, list):
            if len(params) > len(sig.parameters):
                raise INVALID_PARAMS({"reason": "too many positional arguments"})
            bound.arguments = dict(zip(sig.parameters.keys(), params))

        elif isinstance(params, dict):
            bound.arguments = params
        else:
            raise INVALID_PARAMS({"reason": "params must be list or dict"})

        # Type checking (optional)
        for name, value in bound.arguments.items():
            param = sig.parameters[name]
            expected_type = self.param_types.get(name)
            if expected_type and not isinstance(value, expected_type):
                raise INVALID_PARAMS({
                    "reason": f"param '{name}' should be {expected_type.__name__}, got {type(value).__name__}"
                })

    # ───── To JSON (for introspection) ─────
    def to_json(self) -> dict:
        """Return method info as JSON-serializable dict."""
        return {
            "name": self.name,
            "description": self.description,
            "params_schema": self.params_schema,
            "param_types": {k: str(v) for k, v in self.param_types.items()},
            "return_type": str(self.return_type) if self.return_type else None,
            "is_async": self.is_async,
        }


# ------------------------------------------
# RPCRegistry
# ------------------------------------------
# jsonrpc_core/server/registry.py

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Literal, get_type_hints
from enum import Enum, auto
import anyio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from rpcframework.schemas import RPCRequest, RPCResponse
from rpcframework.server.dispatcher import RPCDispatcher
from rpcframework.server.errors import PARSE_ERROR, INVALID_REQUEST
from rpcframework.transport.http import HTTPTransport

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
def _configure_registry_logging(level: str | int = "INFO"):
    logger = logging.getLogger("rpcframework")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# ──────────────────────────────────────────────────────────────
# Transport Enum
# ──────────────────────────────────────────────────────────────
class Transport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"

    def __str__(self):
        return self.value


# ──────────────────────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class RegistrySettings:
    warn_on_duplicate: bool = True
    log_level: str | int = "INFO"
    strict_mode: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    mount_path: str | None = None


# ──────────────────────────────────────────────────────────────
# Main Registry Class
# ──────────────────────────────────────────────────────────────
class RPCMethodRegistry:
    def __init__(
        self,
        name: str | None = None,
        settings: dict | None = None,
        **kwargs: Any,
    ):
        self._settings = RegistrySettings(**(settings or {}), **kwargs)
        self._name = name or "RPCRegistry"
        self._methods: Dict[str, _MethodWrapper] = {}
        self._logger = logging.getLogger("jsonrpc.registry")
        self._app: FastAPI | None = None
        self._dispatcher: RPCDispatcher | None = None

        _configure_registry_logging(self._settings.log_level)
        self._logger.info(f"Initialized {self._name}")

    # ───── Properties ─────
    @property
    def name(self) -> str:
        return self._name

    @property
    def methods(self) -> Dict[str, Callable]:
        return {name: wrapper.fn for name, wrapper in self._methods.items()}

    @property
    def settings(self) -> RegistrySettings:
        return self._settings

    # ───── Register Decorator ─────
    def register(
        self,
        name: str | None = None,
        description: str | None = None,
        params_schema: dict | None = None,
    ):
        def decorator(fn: Callable) -> Callable:
            method_name = name or fn.__name__

            if method_name in self._methods and not self._settings.warn_on_duplicate:
                raise ValueError(f"Method '{method_name}' already registered")

            hints = get_type_hints(fn)
            return_hint = hints.pop("return", None)

            wrapper = _MethodWrapper(
                fn=fn,
                name=method_name,
                description=description,
                params_schema=params_schema,
                param_types=hints,
                return_type=return_hint,
            )

            self._methods[method_name] = wrapper
            self._logger.debug(f"Registered: {method_name}")
            return fn
        return decorator

    # ───── Get Method ─────
    def get(self, method_name: str) -> _MethodWrapper:
        try:
            return self._methods[method_name]
        except KeyError:
            self._logger.error(f"Method not found: {method_name}")
            raise METHOD_NOT_FOUND({"method": method_name})

    # ───── Introspection ─────
    def list_methods(self) -> Dict[str, dict]:
        return {
            name: {
                "description": w.description,
                "params_schema": w.params_schema,
                "param_types": {k: str(v) for k, v in w.param_types.items()},
                "return_type": str(w.return_type) if w.return_type else None,
            }
            for name, w in self._methods.items()
        }

    # ───── RUN METHOD (FastMCP Style) ─────
    def run(
        self,
        transport: Transport | str = Transport.HTTP,
        *,
        host: str | None = None,
        port: int | None = None,
        mount_path: str | None = None,
    ) -> None:
        """Run the JSON-RPC server with selected transport."""
        if isinstance(transport, str):
            try:
                transport = Transport(transport)
            except ValueError:
                raise ValueError(f"Invalid transport: {transport}. Choose from: {', '.join(t.value for t in Transport)}")

        host = host or self._settings.host
        port = port or self._settings.port
        mount_path = mount_path or self._settings.mount_path

        match transport:
            case Transport.STDIO:
                print(f"RPC Server starting at http://{host}:{port}/rpc | STDIO")
                anyio.run(self._run_stdio_async)
            case Transport.HTTP:
                print(f"RPC Server starting at http://{host}:{port}/rpc | HTTP")
                anyio.run(self._run_http_async, host, port)  # ← Safe hai!
            case Transport.SSE:
                print(f"RPC Server starting at http://{host}:{port}/rpc | SSE")
                anyio.run(self._run_sse_async, host, port, mount_path)
            case Transport.STREAMABLE_HTTP:
                print(f"RPC Server starting at http://{host}:{port}/rpc | Streamable HTTP")
                anyio.run(self._run_streamable_http_async, host, port)

    # ───── Transport Runners ─────
    async def _run_stdio_async(self):
        import sys, json
        self._logger.info("Running in STDIO mode")
        while True:
            try:
                line = await anyio.to_thread.run_sync(sys.stdin.readline)
                if not line:
                    break
                payload = json.loads(line.strip())
                response = await self._handle_payload(payload)
                if response:
                    print(json.dumps(response))
                    sys.stdout.flush()
            except Exception as e:
                self._logger.error(f"STDIO error: {e}")

    async def _run_http_async(self, host: str, port: int):
        self._setup_fastapi_app()
        config = uvicorn.Config(
            self._app,
            host=host,
            port=port,
            log_level=self._settings.log_level.lower() if isinstance(self._settings.log_level, str) else "info",
        )
        server = uvicorn.Server(config)
        self._logger.info(f"Starting HTTP server at http://{host}:{port}/jsonrpc")
        await server.serve()

    async def _run_sse_async(self, host: str, port: int, mount_path: str | None):
        # Future: SSE transport
        raise NotImplementedError("SSE transport not yet implemented")

    async def _run_streamable_http_async(self, host: str, port: int):
        # Future: Streamable HTTP
        raise NotImplementedError("Streamable HTTP not yet implemented")

    # ───── FastAPI App Setup ─────
    def _setup_fastapi_app(self):
        if self._app is not None:
            return

        self._dispatcher = RPCDispatcher(self)
        transport = HTTPTransport(self._dispatcher)

        app = FastAPI(title=self._name)
        app.post("/jsonrpc")(transport.handle)
        # app.get("/methods")(lambda: self.list_methods())  # Introspection!
        
        # Methods introspection
        async def methods_endpoint():
          return JSONResponse(content={"result": self.list_methods(), "error": None})

        app.get("/methods")(methods_endpoint)

        self._app = app

    # ───── Handle Payload (shared) ─────
    async def _handle_payload(self, payload: dict | list) -> Any:
        if isinstance(payload, list):
            responses = [r for r in [await self._handle_single(p) for p in payload] if r]
            return responses or None
        else:
            return await self._handle_single(payload)

    async def _handle_single(self, item: dict) -> Any:
        try:
            req = RPCRequest.parse_obj(item)
        except Exception as e:
            err = INVALID_REQUEST(str(e))
            return self._make_response(error=err, id=item.get("id"))

        if req.id is None:
            try:
                await self._dispatcher.dispatch(req.method, req.params)
            except:
                pass
            return None

        try:
            result = await self._dispatcher.dispatch(req.method, req.params, req.id)
            return self._make_response(result=result["result"], id=req.id)
        except Exception as e:
            return self._make_response(error=e, id=req.id)

    def _make_response(self, result=None, error=None, id=None):
        return RPCResponse(
            result=result,
            error=error.to_dict() if isinstance(error, Exception) and hasattr(error, "to_dict") else error,
            id=id
        ).dict(exclude_none=True)



