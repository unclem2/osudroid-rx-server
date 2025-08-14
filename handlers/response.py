def args_join(args):
    return " ".join([str(x) for x in args])


def Success(*args):
    print(f"SUCCESS\n" + args_join(args))
    return "SUCCESS\n" + args_join(args)


def Failed(*args):
    print("FAILED\n" + args_join(args))
    return "FAILED\n" + args_join(args)


def Failure(*args):
    return "FAILURE\n" + args_join(args)

from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    status: str
    data: T

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls[T](status="success", data=data), 200

    @classmethod
    def not_found(cls, message: T) -> "ApiResponse[T]":
        return cls[T](status="not_found", data=message), 404

    @classmethod
    def bad_request(cls, message: T) -> "ApiResponse[T]":
        return cls[T](status="bad_request", data=message), 400

    @classmethod
    def internal_error(cls, message: T) -> "ApiResponse[T]":
        return cls[T](status="internal_error", data=message), 500
    
    @classmethod
    def forbidden(cls, message: T) -> "ApiResponse[T]":
        return cls[T](status="forbidden", data=message), 403
    
    @classmethod
    def custom(cls, status: str, data: T, code: int) -> "ApiResponse[T]":
        return cls[T](status=status, data=data), code