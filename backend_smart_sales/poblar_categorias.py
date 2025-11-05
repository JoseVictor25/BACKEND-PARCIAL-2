# poblar_categorias.py
import django
import os

# Configura el entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tu_proyecto.settings")
django.setup()

from categoria.models import Categoria
# 🧩 Lista de categorías iniciales
CATEGORIAS = [
    {"nombre": "Smartphones", "descripcion": "Teléfonos inteligentes y accesorios"},
    {"nombre": "Laptops", "descripcion": "Computadoras portátiles de distintas marcas"},
    {"nombre": "Televisores", "descripcion": "Pantallas LED, OLED y Smart TV"},
    {"nombre": "Audio", "descripcion": "Parlantes, auriculares y equipos de sonido"},
    {"nombre": "Electrodomésticos", "descripcion": "Productos para el hogar y cocina"},
    {"nombre": "Gaming", "descripcion": "Consolas, controles y accesorios gamer"},
]

def poblar_categorias():
    for cat in CATEGORIAS:
        obj, created = Categoria.objects.get_or_create(
            nombre=cat["nombre"],
            defaults={
                "descripcion": cat["descripcion"],
                "estado": True,
            },
        )
        if created:
            print(f"✅ Creada categoría: {obj.nombre}")
        else:
            print(f"⚠️ Ya existía: {obj.nombre}")

if __name__ == "__main__":
    poblar_categorias()
