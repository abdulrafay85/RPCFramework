# jsonrpc_core/transport/http.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Any, List, Union
import json
from ..schemas import RPCRequest, RPCResponse
from ..server.dispatcher import RPCDispatcher
from rpcframework.server.errors import PARSE_ERROR, INVALID_REQUEST

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
    
    # # Version 1
    # async def _handle_single(self, item: dict) -> Any:
    #     try:
    #         req = RPCRequest.parse_obj(item)
    #     except Exception as e:
    #         if not isinstance(e, JSONRPCError):
    #             e = JSONRPCError(-32000, "Server error", str(e))

    #         return self._make_response(error=e, id=req.id)

    #     if req.id is None:  # notification
    #         try:
    #             await self.dispatcher.dispatch(req.method, req.params)
    #         except:
    #             pass  # ignore errors in notification
    #         return None

    #     try:
    #         result = await self.dispatcher.dispatch(req.method, req.params, req.id)
    #         return self._make_response(result=result["result"], id=req.id)
    #     except Exception as e:
    #         return self._make_response(error=e, id=req.id)

    #  Version 2
    async def _handle_single(self, item: dict) -> Any:
        try:
            req = RPCRequest.parse_obj(item)
        except Exception as e:
            error = JSONRPCError(-32000, "Server error", str(e))
            return self._make_response(error=error, id=item.get('id'))

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
       # normalize error into a dict that RPCResponse expects
      if error:
        if hasattr(error, "to_dict"):
            error_content = error.to_dict()
        elif isinstance(error, dict):
            error_content = error
        else:
            # fallback: generic error object (adjust code/message as per JSON-RPC spec)
            error_content = {"code": -32000, "message": str(error)}
      else:
        error_content = None

      return RPCResponse(result=result, error=error_content, id=id).dict(exclude_none=True)


    def _error_response(self, error, id, status=400):
        return JSONResponse(
            status_code=status,
            content=RPCResponse(error=error.to_dict(), id=id).dict(exclude_none=True)
        )