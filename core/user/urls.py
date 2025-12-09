# core/user/urls.py

from django.urls import path, include
# ⬅️ Importamos el router de Ninja
from .api.endpoints import router as user_router 


urlpatterns = [
    # 1. Endpoints de Djoser (Registro, activación, reseteo de contraseña)
    path('', include('djoser.urls')), 
    
    # 2. Endpoints de Autenticación JWT de Django Ninja (Login, Refresh, Verify, Logout)
    path('', user_router.urls), 
]