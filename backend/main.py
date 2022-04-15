from fastapi import FastAPI, HTTPException
import os
from core import router
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from core import config
from events import events
from response import http_error
from middleware.middleware import init_middlewares
from websocket.websocket import Echo
from middleware.request_limit import init_limit


__author__ = 'ren_mcc'

app = FastAPI(title=config.DOC_TITLE, description="", version=config.DOC_VERSION,
              docs_url=config.DOC_URL, redoc_url=None)

# 加载路由
app.include_router(router.api_router, prefix='/api')

# 启动关闭事件
# app.add_event_handler("startup", events.start_init_db_handler(app))
# app.add_event_handler("shutdown", events.stop_shutdown_db_handler(app))
app.add_event_handler("startup", events.start_init_sys_api_handler(app))

# 异常处理
app.add_exception_handler(HTTPException, http_error.http_error_handler)
app.add_exception_handler(RequestValidationError, http_error.validation_exception_handler)

# 中间件
init_middlewares(app)

# 挂载静态文件资源目录
# app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "static")), name="static")

# webSocket
app.add_websocket_route('/ws', Echo)

# 初始化限速
init_limit(app)

if __name__ == '__main__':
    uvicorn.run(app="main:app", workers=1, host='0.0.0.0', port=8000)
