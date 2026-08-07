import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse, AppCode

logger = logging.getLogger(__name__)

HTTP_TO_APP_CODE = {
    status.HTTP_400_BAD_REQUEST: AppCode.BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED: AppCode.UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN: AppCode.FORBIDDEN,
    status.HTTP_404_NOT_FOUND: AppCode.NOT_FOUND,
    status.HTTP_409_CONFLICT: AppCode.CONFLICT,
    status.HTTP_413_CONTENT_TOO_LARGE: AppCode.PAYLOAD_TOO_LARGE,
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: AppCode.UNSUPPORTED_MEDIA_TYPE,
    status.HTTP_422_UNPROCESSABLE_CONTENT: AppCode.UNPROCESSABLE_ENTITY,
    status.HTTP_500_INTERNAL_SERVER_ERROR: AppCode.INTERNAL_SERVER_ERROR,
    status.HTTP_502_BAD_GATEWAY: AppCode.BAD_GATEWAY,
}


def error_response(status_code: int, message: str) -> JSONResponse:
    """将 HTTP 状态码映射为统一的业务错误响应。"""
    app_code = HTTP_TO_APP_CODE.get(status_code, AppCode.INTERNAL_SERVER_ERROR)
    payload = ApiResponse.fail(code=int(app_code), message=message)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一返回结构化错误响应。"""
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return error_response(exc.status_code, detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc.errors()))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # 对客户端隐藏内部错误细节，但在服务端保留完整堆栈便于排查。
        logger.exception(
            "Unhandled error while processing %s %s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"
        )
