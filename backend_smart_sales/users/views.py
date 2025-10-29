from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import logout
from .models import CustomUser
from .serializers import LoginSerializer, UserSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from bitacora.models import Bitacora

from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetToken
from roles.models import Rol

# ==========================
# FUNCION AUXILIAR: obtener IP del cliente
# ==========================
def get_client_ip(request):
    """Extrae la IP del cliente desde el request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


# ==========================
# LOGIN
# ==========================
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            # Registrar en bitácora
            Bitacora.objects.create(
                usuario=user,
                accion="Inicio de sesión",
                ip=get_client_ip(request),
                estado=True
            )

            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================
# LOGOUT
# ==========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        tokens = OutstandingToken.objects.filter(user=user)

        # Invalidar todos los tokens activos del usuario
        for token in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except TokenError:
                pass

        # Registrar en bitácora
        Bitacora.objects.create(
            usuario=user,
            accion="Cierre de sesión (token invalidado)",
            ip=get_client_ip(request),
            estado=True
        )

        logout(request)
        return Response(
            {"message": "Sesión cerrada y tokens invalidados correctamente."},
            status=status.HTTP_200_OK
        )

# ==========================
# REGISTRO (para pruebas y administración)
# ==========================
''' class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = CustomUser.objects.create_user(
                username=request.data["username"],
                email=request.data["email"],
                password=request.data["password"],
                first_name=request.data.get("first_name", ""),
                last_name=request.data.get("last_name", ""),
                telefono=request.data.get("telefono", ""),
                direccion=request.data.get("direccion", ""),
                rol=request.data.get("rol", "Cliente")
            )

            # Registrar en bitácora
            Bitacora.objects.create(
                usuario=user,
                accion="Registro de nuevo usuario",
                ip=get_client_ip(request),
                estado=True
            )

            return Response({"message": "Usuario creado exitosamente."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
'''
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # 🔹 Crear usuario base
            user = CustomUser.objects.create_user(
                username=request.data["username"],
                email=request.data["email"],
                password=request.data["password"],
                first_name=request.data.get("first_name", ""),
                last_name=request.data.get("last_name", ""),
                telefono=request.data.get("telefono", ""),
                direccion=request.data.get("direccion", "")
            )

            # 🔹 Asignar rol por defecto ("Cliente")
            rol_defecto = Rol.objects.filter(nombre__iexact="Cliente").first()
            if rol_defecto:
                user.rol = rol_defecto
                user.save()
                rol_nombre = rol_defecto.nombre
            else:
                rol_nombre = "Sin rol (rol 'Cliente' no existe)"

            # 🔹 Registrar en Bitácora
            Bitacora.objects.create(
                usuario=user,
                accion=f"Registro de nuevo usuario con rol {rol_nombre}",
                ip=get_client_ip(request),
                estado=True
            )

            return Response(
                {"message": f"Usuario creado exitosamente con rol '{rol_nombre}'."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# ==========================
# SOLICITAR RECUPERACIÓN
# ==========================
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({"error": "No existe un usuario con ese correo."}, status=404)

            # Crear token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Opcional: enviar correo (solo se muestra en consola)
            reset_link = f"http://localhost:5173/reset-password/{reset_token.token}"
            send_mail(
                subject="Recuperación de contraseña - SmartSales365",
                message=f"Tu token de recuperación es: {reset_token.token}\n\nO usa este enlace: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

            return Response(
                {"message": "Se envió un enlace de recuperación al correo.", "token": str(reset_token.token)},
                status=200,
            )
        return Response(serializer.errors, status=400)


# ==========================
# CONFIRMAR NUEVA CONTRASEÑA
# ==========================
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token_str = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            try:
                token = PasswordResetToken.objects.get(token=token_str)
            except PasswordResetToken.DoesNotExist:
                return Response({"error": "Token inválido."}, status=400)

            if not token.is_valid():
                token.delete()
                return Response({"error": "El token ha expirado."}, status=400)

            user = token.user
            user.set_password(new_password)
            user.save()
            token.delete()

            # Registrar en bitácora
            Bitacora.objects.create(
                usuario=user,
                accion="Recuperación de contraseña",
                ip=get_client_ip(request),
                estado=True
            )

            return Response({"message": "Contraseña restablecida correctamente."}, status=200)

        return Response(serializer.errors, status=400)
    
# ==========================
# ASIGNAR ROL (solo admin)
# ==========================
class AsignarRolView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # ✅ Validar que quien realiza la acción sea administrador o superusuario
        if not request.user.is_superuser:
            return Response(
                {"error": "Solo los administradores pueden asignar roles."},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user_id")
        rol_id = request.data.get("rol_id")

        if not user_id or not rol_id:
            return Response(
                {"error": "Debe enviar 'user_id' y 'rol_id'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=404)

        try:
            rol = Rol.objects.get(id=rol_id)
        except Rol.DoesNotExist:
            return Response({"error": "Rol no encontrado."}, status=404)

        # ✅ Asignar el rol al usuario
        user.rol = rol
        user.save()

        # Registrar en Bitácora
        Bitacora.objects.create(
            usuario=request.user,
            accion=f"Asignó el rol '{rol.nombre}' al usuario '{user.username}'",
            ip=get_client_ip(request),
            estado=True
        )

        return Response(
            {"message": f"Rol '{rol.nombre}' asignado correctamente al usuario '{user.username}'."},
            status=200
        )    