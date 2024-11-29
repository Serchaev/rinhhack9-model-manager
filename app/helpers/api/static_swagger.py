from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from starlette.staticfiles import StaticFiles


def add_swagger_static_router(
    app: FastAPI,
    static_path: str,
    swagger_js_url: str = "swagger-ui-bundle.js",
    swagger_css_url: str = "swagger-ui.css",
    redoc_js_url: str = "redoc.standalone.js",
):
    """
    Меняет источники для swagger на статичные данные, обязательно указать app = FastAPI(docs_url=None, redoc_url=None)
    """

    app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url=f"/static/{swagger_js_url}",
            swagger_css_url=f"/static/{swagger_css_url}",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url=f"/static/{redoc_js_url}",
        )
