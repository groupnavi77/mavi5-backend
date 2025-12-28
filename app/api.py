# [mi_proyecto]/api.py

from ninja_extra import NinjaExtraAPI # ⬅️ Úsalo para definir la API principal
from core.product_base.api.endpoints import router as product_base_router
from core.product_ins.api.endpoints import router as product_ins_router
from core.tag.api.endpoints import router as tag_router
from core.user.api.endpoints import router as user_router
from core.campaing.api.endpoints import router as campaing_router
from core.user.api.endpoints_advanced import advanced_router
from core.category.api.endpoints import router as category_router
from core.configuration.api.endpoints import router as configuration_router 

api = NinjaExtraAPI(
   
    title="Mavi API",
    version="1.0.0",
    description="API para Mavi Store con autenticación JWT y Social Auth",
)

# Registrar routers
api.add_router("/configuration/", configuration_router, tags=["Configuración"])  # Agrega el router de configuración si existe
api.add_router("/campaings/", campaing_router, tags=["Campañas"])
api.add_router("/products_ins/", product_ins_router, tags=["Productos inspirados"])
api.add_router("/categories/", category_router, tags=["Categorías"])
api.add_router("/products_base/", product_base_router, tags=["Productos Base"])
api.add_router("/tags/", tag_router, tags=["Etiquetas"])
api.add_router("/auth/", user_router, tags=["Autenticación"])
api.add_router("/auth/advanced/", advanced_router, tags=["Auth Avanzado"])