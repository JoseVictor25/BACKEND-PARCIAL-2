# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from venta.models import Venta
from django.db.models import Sum
from datetime import datetime

# views.py
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
import os



######################################################################################################################################################################3
#################################################################################################################################################################
####################################################################################################################################################
class VentasHistoricas(APIView):
    def get(self, request):
        # Obtener las ventas por período (por ejemplo, por mes)
        ventas = Venta.objects.values('fecha__month', 'fecha__year').annotate(
            total_ventas=Sum('total')
        ).order_by('fecha__year', 'fecha__month')

        # Transformar los datos para enviarlos al frontend
        data = [{
            'mes': f"{venta['fecha__month']}-{venta['fecha__year']}",
            'total_ventas': venta['total_ventas']
        } for venta in ventas]

        return Response(data, status=status.HTTP_200_OK)

##########################################################################################################################################################
###########################################################################################################################################################
#############################################################################################################################################################


class PrediccionesVentas(APIView):
    def get(self, request):
        # Cuántos meses predecir (opcional, default 6)
        try:
            meses_a_predecir = int(request.query_params.get('meses', 6))
            if meses_a_predecir < 1:
                meses_a_predecir = 6
        except:
            meses_a_predecir = 6

        # Obtener ventas históricas
        ventas = Venta.objects.values('fecha__year', 'fecha__month').annotate(total_ventas=Sum('total')).order_by('fecha__year', 'fecha__month')
        if not ventas:
            return Response({"error": "No hay datos históricos de ventas."}, status=400)

        data = pd.DataFrame(list(ventas))
        data.rename(columns={'fecha__year': 'año', 'fecha__month': 'mes'}, inplace=True)

        X = data[['año', 'mes']]
        y = data['total_ventas']

        modelo_path = 'modelo_ventas.pkl'

        # Usar modelo existente o entrenar
        if os.path.exists(modelo_path):
            model = joblib.load(modelo_path)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            model.ultimo_mes = data['mes'].max()
            model.ultimo_año = data['año'].max()
            joblib.dump(model, modelo_path)

        # Preparar fechas futuras
        ultimo_año = data['año'].max()
        ultimo_mes = data['mes'].max()
        future_dates = []
        mes_actual = ultimo_mes
        año_actual = ultimo_año
        for _ in range(meses_a_predecir):
            mes_actual += 1
            if mes_actual > 12:
                mes_actual = 1
                año_actual += 1
            future_dates.append({'año': año_actual, 'mes': mes_actual})
        future_df = pd.DataFrame(future_dates)

        predictions = model.predict(future_df)

        prediccion_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": round(pred, 2)}
            for row, pred in zip(future_df.itertuples(index=False), predictions)
        ]

        return Response(prediccion_data, status=200)
    


    
################################################################################################################################################################################
###############################################################################################################################################################################
###############################################################################################################################################################################


class VentasHistoricoYPredicciones(APIView):
    def get(self, request):
        # 1️⃣ Parámetro opcional: cuántos meses futuros predecir
        try:
            meses_a_predecir = int(request.query_params.get('meses', 6))
            if meses_a_predecir < 1:
                meses_a_predecir = 6
        except:
            meses_a_predecir = 6

        # 2️⃣ Obtener ventas históricas agregadas por mes
        ventas = (
            Venta.objects.values('fecha__year', 'fecha__month')
            .annotate(total_ventas=Sum('total'))
            .order_by('fecha__year', 'fecha__month')
        )

        if not ventas:
            return Response({"error": "No hay datos históricos de ventas."}, status=400)

        # 3️⃣ Convertir a DataFrame
        data = pd.DataFrame(list(ventas))
        data.rename(columns={'fecha__year': 'año', 'fecha__month': 'mes'}, inplace=True)

        # 4️⃣ Variables de entrenamiento
        X = data[['año', 'mes']]
        y = data['total_ventas']

        # 5️⃣ Preparar ruta del modelo
        modelo_path = 'modelo_ventas.pkl'

        # 6️⃣ Verificar si existe el modelo y si necesita actualización
        actualizar_modelo = False
        if os.path.exists(modelo_path):
            model = joblib.load(modelo_path)
            
            # Comprobar si los datos históricos cambiaron (ejemplo simple: último mes)
            ultimo_mes_modelo = getattr(model, 'ultimo_mes', None)
            ultimo_año_modelo = getattr(model, 'ultimo_año', None)
            ultimo_mes_data = data['mes'].max()
            ultimo_año_data = data['año'].max()
            if (ultimo_mes_modelo != ultimo_mes_data) or (ultimo_año_modelo != ultimo_año_data):
                actualizar_modelo = True
        else:
            actualizar_modelo = True

        # 7️⃣ Entrenar y guardar el modelo si es necesario
        if actualizar_modelo:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Guardar información adicional para saber si el modelo está actualizado
            model.ultimo_mes = data['mes'].max()
            model.ultimo_año = data['año'].max()
            
            joblib.dump(model, modelo_path)

        # 8️⃣ Preparar fechas futuras
        ultimo_año = data['año'].max()
        ultimo_mes = data['mes'].max()
        future_dates = []
        mes_actual = ultimo_mes
        año_actual = ultimo_año
        for _ in range(meses_a_predecir):
            mes_actual += 1
            if mes_actual > 12:
                mes_actual = 1
                año_actual += 1
            future_dates.append({'año': año_actual, 'mes': mes_actual})
        future_df = pd.DataFrame(future_dates)

        # 9️⃣ Realizar predicciones
        predictions = model.predict(future_df)

        # 🔹 Formatear datos históricos
        historico_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": row.total_ventas}
            for row in data.itertuples(index=False)
        ]

        # 🔹 Formatear datos predicción
        prediccion_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": round(pred, 2)}
            for row, pred in zip(future_df.itertuples(index=False), predictions)
        ]

        # 10️⃣ Combinar histórico + predicción
        resultado = {
            "historico": historico_data,
            "predicciones": prediccion_data
        }

        return Response(resultado, status=status.HTTP_200_OK)
