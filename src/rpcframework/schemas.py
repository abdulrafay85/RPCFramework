# app/schemas.py
from typing import Any, Optional, Union, List
from pydantic import BaseModel, Field

JSONValue = Union[str, int, float, bool, None, dict, list]

class RPCRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    method: str
    params: Optional[Union[List[Any], dict]] = None
    id: Optional[Union[int, str, None]] = None  # None => notification (no response expected)

class RPCErrorObject(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class RPCResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    result: Optional[Any] = None
    error: Optional[RPCErrorObject] = None
    id: Optional[Union[int, str, None]]
