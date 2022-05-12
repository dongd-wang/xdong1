from fastapi import APIRouter
from src.api.v1 import views as api_v1_views

# api route
api_v1_routes = APIRouter()
api_v1_routes.include_router(api_v1_views.router, prefix="/v1")
