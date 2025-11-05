# app/errors.py
from typing import Any
from dataclasses import dataclass

@dataclass
class JSONRPCError(Exception):
    code: int
    message: str
    data: Any = None

    def to_dict(self):
        base = {"code": self.code, "message": self.message}
        if self.data is not None:
            base["data"] = self.data
        return base

# Some common JSON-RPC 2.0 error codes (extend as needed)
PARSE_ERROR = lambda d=None: JSONRPCError(-32700, "Parse error", d)
INVALID_REQUEST = lambda d=None: JSONRPCError(-32600, "Invalid Request", d)
METHOD_NOT_FOUND = lambda d=None: JSONRPCError(-32601, "Method not found", d)
INVALID_PARAMS = lambda d=None: JSONRPCError(-32602, "Invalid params", d)
INTERNAL_ERROR = lambda d=None: JSONRPCError(-32603, "Internal error", d)
SERVER_ERROR = lambda code= -32000, d=None: JSONRPCError(code, "Server error", d)
