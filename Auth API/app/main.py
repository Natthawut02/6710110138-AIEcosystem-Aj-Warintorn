from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from app.db.database import engine, Base
from app.routers import auth, users

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Auth & Authorization API",
    description="Authentication & Authorization System with JWT, SQLAlchemy, and Role-Based Access Control",
    version="1.0.0",
    docs_url=None
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/")
def root():
    return {
        "message": "FastAPI Auth API is running!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

