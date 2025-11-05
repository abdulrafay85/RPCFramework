# --------------------------------------
# Version 1
# --------------------------------------
# # # client/client.py
# # import asyncio
# # import httpx
# # import uuid
# # from typing import Any, List

# # SERVER_URL = "http://127.0.0.1:8000/jsonrpc"

# # async def send_rpc(method: str, params: Any = None, id=None):
# #     if id is None:
# #         id = str(uuid.uuid4())
# #     payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": id}
# #     async with httpx.AsyncClient(timeout=10.0) as client:
# #         r = await client.post(SERVER_URL, json=payload)
# #         r.raise_for_status()
# #         return r.json()

# # async def send_notification(method: str, params: Any = None):
# #     payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": None}
# #     async with httpx.AsyncClient(timeout=10.0) as client:
# #         # server expected to return 204 (no content) for notifications in our implementation
# #         r = await client.post(SERVER_URL, json=payload)
# #         return r.status_code

# # async def send_batch(requests: List[dict]):
# #     async with httpx.AsyncClient(timeout=10.0) as client:
# #         r = await client.post(SERVER_URL, json=requests)
# #         r.raise_for_status()
# #         return r.json()

# # async def main():
# #     # Single request example
# #     print("Single RPC: add(3,4)")
# #     resp = await send_rpc("add", [3, 4])
# #     print(resp)

# #     # error example: divide by zero
# #     print("Error example: divide(5,0)")
# #     resp = await send_rpc("divide", {"a": 5, "b": 0})
# #     print(resp)

# #     # Notification example (no response expected)
# #     print("Sending notification: echo('hello-notify')")
# #     status = await send_notification("echo", {"message": "hello-notify"})
# #     print("Notification HTTP status:", status)

# #     # Batch example (multiple requests)
# #     batch = [
# #         {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": "1"},
# #         {"jsonrpc": "2.0", "method": "echo", "params": {"message": "hi"}, "id": "2"},
# #         {"jsonrpc": "2.0", "method": "divide", "params": {"a": 10, "b": 2}, "id": "3"},
# #         # notification in batch:
# #         {"jsonrpc": "2.0", "method": "echo", "params": {"message": "batch-notify"}, "id": None},
# #     ]
# #     print("Batch call")
# #     bresp = await send_batch(batch)
# #     print(bresp)

# # if __name__ == "__main__":
# #     asyncio.run(main())

# --------------------------------------
# Version 2
# --------------------------------------

# app/transport.py
import json
import httpx
from typing import Any, Optional, List, Union
from rpcframework.schemas import RPCRequest, RPCResponse
from rpcframework.errors import JSONRPCError

class JSONRPCTransport:
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def call_method(self, method: str, params: Any = None, id: Optional[str] = None) -> Any:
        """Simple call with response"""
        req = RPCRequest(method=method, params=params, id=id or "1")
        resp = await self.client.post(self.url, json=req.dict(exclude_none=True))
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            raise JSONRPCError(code=err["code"], message=err["message"], data=err.get("data"))
        return data["result"]


    async def notify(self, method: str, params: Any = None) -> None:
        """Notification (no response)"""
        req = RPCRequest(method=method, params=params, id=None)
        resp = await self.client.post(self.url, json=req.dict(exclude_none=True))
        # 204 = No Content → success
        if resp.status_code != 204:
            print(f"Warning: Notification failed with {resp.status_code}")

    async def batch(self, calls: List[dict]) -> List[Any]:
        """Batch calls"""
        # calls = [{"method": "add", "params": [1,2], "id": "1"}, ...]
        resp = await self.client.post(self.url, json=calls)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


# --------------------------------------
# Version 3
# --------------------------------------

# jsonrpc_core/transport/http.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
# from schemas import RPCRequest, RPCResponse
from typing import Any, List, Union
import json
from ..schemas import RPCRequest, RPCResponse
from ..server.dispatcher import RPCDispatcher
from errors import PARSE_ERROR, INVALID_REQUEST

class HTTPTransport:
    def __init__(self, dispatcher: RPCDispatcher):
        self.dispatcher = dispatcher

    async def handle(self, request: Request) -> Response:
        raw = await request.body()
        if not raw:
            return self._error_response(INVALID_REQUEST("empty body"), None, 400)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            return self._error_response(PARSE_ERROR(str(e)), None, 400)

        if isinstance(payload, list):
            responses = [r for r in [await self._handle_single(item) for item in payload] if r]
            return JSONResponse(responses) if responses else Response(status_code=204)
        else:
            resp = await self._handle_single(payload)
            return Response(status_code=204) if resp is None else JSONResponse(resp)

    async def _handle_single(self, item: dict) -> Any:
        try:
            req = RPCRequest.parse_obj(item)
        except Exception as e:
            err = INVALID_REQUEST(str(e))
            return self._make_response(error=err, id=item.get("id"))

        if req.id is None:  # notification
            try:
                await self.dispatcher.dispatch(req.method, req.params)
            except:
                pass  # ignore errors in notification
            return None

        try:
            result = await self.dispatcher.dispatch(req.method, req.params, req.id)
            return self._make_response(result=result["result"], id=req.id)
        except Exception as e:
            return self._make_response(error=e, id=req.id)

    def _make_response(self, result=None, error=None, id=None):
        return RPCResponse(result=result, error=error.to_dict() if error else None, id=id).dict(exclude_none=True)

    def _error_response(self, error, id, status=400):
        return JSONResponse(
            status_code=status,
            content=RPCResponse(error=error.to_dict(), id=id).dict(exclude_none=True)
        )