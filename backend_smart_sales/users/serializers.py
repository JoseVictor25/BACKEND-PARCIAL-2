from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import CustomUser, PasswordResetToken
from roles.models import Rol
from roles.serializers import RolSerializer

class UserSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source='rol',
        write_only=True
    )
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefono",
            "direccion",
            "rol",
            "rol_nombre",
            "rol_id",
            "password",  # ✅ se añade aquí
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)  # ✅ encripta la contraseña
        user.save()
        return user






class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Credenciales inválidas.")
        else:
            raise serializers.ValidationError("Debe ingresar usuario y contraseña.")
        data["user"] = user
        return data
    




class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=6)
