from rest_framework.exceptions import APIException

class CustomAuthException(APIException):
    status_code = 401
    default_detail = "Credenciales incorrectas. Verifica tu correo y contraseña."
    default_code = "invalid_credentials"

    def __init__(self, detail=None, code=None):
        self.detail = {
            "code": code or self.default_code,
            "message": detail or self.default_detail
        }
