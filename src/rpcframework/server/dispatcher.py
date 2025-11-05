# jsonrpc_core/server/dispatcher.py
import inspect
from typing import Any, Optional
from rpcframework.server.errors import INVALID_PARAMS, JSONRPCError
from typing import Callable, Any, Optional
from typing import TYPE_CHECKING
# from ..server.registry import RPCMethodRegistry

if TYPE_CHECKING:
    from rpcframework.server.registry import RPCMethodRegistry

async def _call_fn(fn: Callable, params: Optional[Any]):
    if params is None:
        return await _maybe_await(fn)()
    elif isinstance(params, list):
        return await _maybe_await(fn)(*params)
    elif isinstance(params, dict):
        return await _maybe_await(fn)(**params)
    else:
        raise INVALID_PARAMS({"reason": "params must be list or dict"})

def _maybe_await(fn):
    if inspect.iscoroutinefunction(fn):
        return fn
    async def wrapper(*a, **kw):
        return fn(*a, **kw)
    return wrapper

class RPCDispatcher:
    def __init__(self, registry: "RPCMethodRegistry"):
        self.registry = registry

    async def dispatch(self, method: str, params: Optional[Any], request_id: Any = None):
        fn = self.registry.get(method)
        try:
            result = await _call_fn(fn, params)
            return {"result": result, "id": request_id}
        except JSONRPCError:
            raise
        except TypeError as e:
            raise INVALID_PARAMS({"reason": str(e)})
        except Exception as e:
            raise JSONRPCError(-32000, "Server error", str(e))