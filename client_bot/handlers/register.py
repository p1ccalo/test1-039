from aiogram import Dispatcher
from .common import register_common
from .profile import register_profile
from .program import register_program
from .products import register_products
from .services import register_services
from .settings import register_settings
from .start_session import register_handlers
from .client import register_handlers_client

def register_all(dp: Dispatcher):
    register_common(dp)
    register_profile(dp)
    register_program(dp)
    register_products(dp)
    register_services(dp)
    register_settings(dp)
    register_handlers(dp)
    register_handlers_client(dp)
