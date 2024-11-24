# app/routes/__init__.py
from .main import router as main_router
from .properties import router as properties_router
from .admin import router as admin_router

# If you want to keep the current import style in main.py:
main = main_router
properties = properties_router
admin = admin_router
