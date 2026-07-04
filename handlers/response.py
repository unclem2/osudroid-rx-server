from fastapi.responses import JSONResponse, HTMLResponse


def _serialize(data):
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    return data


def args_join(args):
    return " ".join([str(x) for x in args])


def Success(*args):
    print(f"SUCCESS\n" + args_join(args))
    return HTMLResponse("SUCCESS\n" + args_join(args))


def Failed(*args):
    print("FAILED\n" + args_join(args))
    return HTMLResponse("FAILED\n" + args_join(args))


def Failure(*args):
    return HTMLResponse("FAILURE\n" + args_join(args))


def success_str(*args):
    return "SUCCESS\n" + args_join(args)


def failed_str(*args):
    return "FAILED\n" + args_join(args)


class ApiResponse:
    @staticmethod
    def ok(data):
        return JSONResponse(
            content={"status": "success", "data": _serialize(data)},
            status_code=200,
        )

    @staticmethod
    def not_found(message):
        return JSONResponse(
            content={"status": "not_found", "data": message},
            status_code=404,
        )

    @staticmethod
    def bad_request(message):
        return JSONResponse(
            content={"status": "bad_request", "data": message},
            status_code=400,
        )

    @staticmethod
    def internal_error(message):
        return JSONResponse(
            content={"status": "internal_error", "data": message},
            status_code=500,
        )

    @staticmethod
    def forbidden(message):
        return JSONResponse(
            content={"status": "forbidden", "data": message},
            status_code=403,
        )

    @staticmethod
    def custom(status, data, code):
        return JSONResponse(
            content={"status": status, "data": data},
            status_code=code,
        )
