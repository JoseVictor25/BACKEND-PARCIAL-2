import django
import os
from random import choice, randint
from faker import Faker
from datetime import datetime
from django.utils import timezone

# Configura el entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_smart_sales.settings")
django.setup()

# Importar modelos
from django.contrib.auth import get_user_model
from producto.models import Producto
from marca.models import Marca
from categoria.models import Categoria
from venta.models import Venta, DetalleVenta

fake = Faker()

# 🧩 Datos base
CATEGORIA_LIST = [
    "Electrodomésticos",
    "Televisores",
    "Audio",
    "Gaming",
    "Smartphones",
    "Laptops"
]

PRODUCTOS = {
    "Electrodomésticos": ["Refrigerador", "Microondas", "Aspiradora", "Lavadora"],
    "Televisores": ["Televisor"],
    "Audio": ["Auriculares"],
    "Gaming": ["Consola"],
    "Smartphones": ["Smartphone"],
    "Laptops": ["Laptop"]
}

MARCAS_LIST = {
    "Electrodomésticos": ["Samsung", "LG", "Whirlpool", "Bosch"],
    "Televisores": ["Samsung", "Sony", "LG", "Philips"],
    "Audio": ["Sony", "Philips"],
    "Gaming": ["Sony"],
    "Smartphones": ["Samsung", "LG"],
    "Laptops": ["Samsung", "LG"]
}

ESTADO_VENTA_CHOICES = ["entregado"]


# 1. Crear Marcas
def crear_marcas():
    todas_las_marcas = {marca for marcas in MARCAS_LIST.values() for marca in marcas}
    for marca in todas_las_marcas:
        obj, created = Marca.objects.get_or_create(
            nombre=marca,
            defaults={"descripcion": f"Marca de productos {marca}", "estado": True}
        )
        if created:
            print(f"✅ Creada marca: {obj.nombre} - poblar.py:61")
        else:
            print(f"⚠️ Ya existía la marca: {obj.nombre} - poblar.py:63")


# 2. Crear Categorías
def crear_categorias():
    for categoria in CATEGORIA_LIST:
        obj, created = Categoria.objects.get_or_create(
            nombre=categoria,
            defaults={"descripcion": f"Categoría de productos para {categoria}", "estado": True}
        )
        if created:
            print(f"✅ Creada categoría: {obj.nombre} - poblar.py:74")
        else:
            print(f"⚠️ Ya existía la categoría: {obj.nombre} - poblar.py:76")


# 3. Crear Productos
def crear_productos():
    for categoria_nombre in PRODUCTOS.keys():
        categoria = Categoria.objects.get(nombre=categoria_nombre)
        marcas = MARCAS_LIST[categoria_nombre]
        for producto_nombre in PRODUCTOS[categoria_nombre]:
            marca = Marca.objects.get(nombre=choice(marcas))
            producto_obj, created = Producto.objects.get_or_create(
                nombre=producto_nombre,
                marca=marca,
                categoria=categoria,
                defaults={
                    "descripcion": f"Descripción del producto {producto_nombre}",
                    "precio": randint(100, 1500),
                    "stock": randint(1, 100),
                    "imagen": fake.image_url(),
                    "estado": True,
                    "fecha_creacion": timezone.now()
                }
            )
            if created:
                print(f"✅ Creado producto: {producto_obj.nombre} - poblar.py:100")
            else:
                print(f"⚠️ Ya existía el producto: {producto_obj.nombre} - poblar.py:102")


# 4. Crear Usuarios
def crear_usuarios():
    User = get_user_model()
    for _ in range(100):
        username = fake.user_name()
        email = fake.email()
        user = User.objects.create_user(
            username=username,
            email=email,
            password="password123"
        )
        print(f"✅ Creado usuario: {username} - poblar.py:116")


# 5. Crear Ventas
def crear_ventas():
    usuarios = get_user_model().objects.all()
    productos = Producto.objects.all()

    for _ in range(1000):
        usuario = choice(usuarios)
        total = 0
        venta = Venta.objects.create(
            usuario=usuario,
            total=0,
            estado=choice(ESTADO_VENTA_CHOICES),
            fecha=timezone.now()
        )

        for _ in range(randint(1, 5)):
            producto = choice(productos)
            cantidad = randint(1, 3)
            subtotal = producto.precio * cantidad
            total += subtotal

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal
            )

        venta.total = total
        venta.save()
        print(f"✅ Creada venta ID {venta.id} | Total: {venta.total} - poblar.py:150")


# 🧩 Ejecutar el poblamiento completo
def poblar_datos():
    print("Creando marcas... - poblar.py:155")
    crear_marcas()
    print("Creando categorías... - poblar.py:157")
    crear_categorias()
    print("Creando productos... - poblar.py:159")
    crear_productos()
    print("Creando usuarios... - poblar.py:161")
    crear_usuarios()
    print("Creando ventas... - poblar.py:163")
    crear_ventas()


if __name__ == "__main__":
    poblar_datos()
