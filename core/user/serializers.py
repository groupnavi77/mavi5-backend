from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .exeptions import CustomAuthException
User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CustomAuthException(
                detail="Credenciales incorrectas. Verifica tu correo y contraseña.",
                code="invalid_credentials"
            )

        if not user.check_password(password):
            raise CustomAuthException(
                detail="Credenciales incorrectas. Verifica tu correo y contraseña.",
                code="invalid_credentials"
            )

        if not user.is_active:
            raise CustomAuthException(
                detail="Tu cuenta no está activada. Revisa tu correo o solicita un nuevo enlace de activación.",
                code="account_inactive"
            )

        data = super().validate(attrs)
        return data