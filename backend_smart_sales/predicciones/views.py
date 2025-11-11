# views.py
import joblib
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from venta.models import Venta
from django.db.models import Sum


class VentasHistoricas(APIView):
    def get(self, request):
        # Obtener las ventas por período (por ejemplo, por mes)
        ventas = Venta.objects.values('fecha__month', 'fecha__year').annotate(
            total_ventas=Sum('total')
        ).order_by('fecha__year', 'fecha__month')

        # Transformar los datos para enviarlos al frontend
        data = [{
            'mes': f"{venta['fecha__month']}-{venta['fecha__year']}",
            'total_ventas': float(venta['total_ventas'])
        } for venta in ventas]

        return Response(data, status=status.HTTP_200_OK)


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
        ventas = (
            Venta.objects.values('fecha__year', 'fecha__month')
            .annotate(total_ventas=Sum('total'))
            .order_by('fecha__year', 'fecha__month')
        )
        
        if not ventas:
            return Response({"error": "No hay datos históricos de ventas."}, status=400)

        # Convertir a DataFrame
        data = pd.DataFrame(list(ventas))
        data.rename(columns={'fecha__year': 'año', 'fecha__month': 'mes'}, inplace=True)

        # Crear variable temporal continua
        primer_año = data['año'].min()
        primer_mes = data['mes'].min()
        
        data['meses_desde_inicio'] = (data['año'] - primer_año) * 12 + (data['mes'] - primer_mes)
        data['mes_sin'] = np.sin(2 * np.pi * data['mes'] / 12)
        data['mes_cos'] = np.cos(2 * np.pi * data['mes'] / 12)

        X = data[['meses_desde_inicio', 'mes_sin', 'mes_cos']]
        y = data['total_ventas']

        modelo_path = 'modelo_ventas.pkl'

        # Usar modelo existente o entrenar
        if os.path.exists(modelo_path):
            model = joblib.load(modelo_path)
            
            ultimo_mes_modelo = getattr(model, 'ultimo_mes', None)
            ultimo_año_modelo = getattr(model, 'ultimo_año', None)
            ultimo_mes_data = data['mes'].max()
            ultimo_año_data = data['año'].max()
            
            primer_año = getattr(model, 'primer_año', primer_año)
            primer_mes = getattr(model, 'primer_mes', primer_mes)
            
            if (ultimo_mes_modelo != ultimo_mes_data) or (ultimo_año_modelo != ultimo_año_data):
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)
                model.ultimo_mes = ultimo_mes_data
                model.ultimo_año = ultimo_año_data
                model.primer_año = primer_año
                model.primer_mes = primer_mes
                joblib.dump(model, modelo_path)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            model.ultimo_mes = data['mes'].max()
            model.ultimo_año = data['año'].max()
            model.primer_año = primer_año
            model.primer_mes = primer_mes
            joblib.dump(model, modelo_path)

        # Preparar fechas futuras DESDE EL ÚLTIMO MES
        ultimo_año = data['año'].max()
        ultimo_mes = data['mes'].max()
        ultimo_meses_desde_inicio = data['meses_desde_inicio'].max()
        
        future_dates = []
        mes_actual = ultimo_mes
        año_actual = ultimo_año
        meses_desde_inicio_actual = ultimo_meses_desde_inicio
        
        for i in range(1, meses_a_predecir + 1):
            mes_actual += 1
            meses_desde_inicio_actual += 1
            
            if mes_actual > 12:
                mes_actual = 1
                año_actual += 1
            
            future_dates.append({
                'año': año_actual,
                'mes': mes_actual,
                'meses_desde_inicio': meses_desde_inicio_actual,
                'mes_sin': np.sin(2 * np.pi * mes_actual / 12),
                'mes_cos': np.cos(2 * np.pi * mes_actual / 12)
            })
        
        future_df = pd.DataFrame(future_dates)
        X_future = future_df[['meses_desde_inicio', 'mes_sin', 'mes_cos']]
        predictions = model.predict(X_future)

        prediccion_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": round(float(pred), 2)}
            for row, pred in zip(future_df.itertuples(index=False), predictions)
        ]

        return Response(prediccion_data, status=200)


class VentasHistoricoYPredicciones(APIView):
    def get(self, request):
        try:
            meses_a_predecir = int(request.query_params.get('meses', 6))
            if meses_a_predecir < 1:
                meses_a_predecir = 6
        except:
            meses_a_predecir = 6

        ventas = (
            Venta.objects.values('fecha__year', 'fecha__month')
            .annotate(total_ventas=Sum('total'))
            .order_by('fecha__year', 'fecha__month')
        )

        if not ventas:
            return Response({"error": "No hay datos históricos de ventas."}, status=400)

        data = pd.DataFrame(list(ventas))
        data.rename(columns={'fecha__year': 'año', 'fecha__month': 'mes'}, inplace=True)

        # Crear variable temporal continua
        primer_año = data['año'].min()
        primer_mes = data['mes'].min()
        
        data['meses_desde_inicio'] = (data['año'] - primer_año) * 12 + (data['mes'] - primer_mes)
        data['mes_sin'] = np.sin(2 * np.pi * data['mes'] / 12)
        data['mes_cos'] = np.cos(2 * np.pi * data['mes'] / 12)

        X = data[['meses_desde_inicio', 'mes_sin', 'mes_cos']]
        y = data['total_ventas']

        modelo_path = 'modelo_ventas.pkl'

        actualizar_modelo = False
        if os.path.exists(modelo_path):
            model = joblib.load(modelo_path)
            
            ultimo_mes_modelo = getattr(model, 'ultimo_mes', None)
            ultimo_año_modelo = getattr(model, 'ultimo_año', None)
            ultimo_mes_data = data['mes'].max()
            ultimo_año_data = data['año'].max()
            
            primer_año = getattr(model, 'primer_año', primer_año)
            primer_mes = getattr(model, 'primer_mes', primer_mes)
            
            if (ultimo_mes_modelo != ultimo_mes_data) or (ultimo_año_modelo != ultimo_año_data):
                actualizar_modelo = True
        else:
            actualizar_modelo = True

        if actualizar_modelo:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            model.ultimo_mes = data['mes'].max()
            model.ultimo_año = data['año'].max()
            model.primer_año = primer_año
            model.primer_mes = primer_mes
            joblib.dump(model, modelo_path)

        # Preparar fechas futuras
        ultimo_año = data['año'].max()
        ultimo_mes = data['mes'].max()
        ultimo_meses_desde_inicio = data['meses_desde_inicio'].max()
        
        future_dates = []
        mes_actual = ultimo_mes
        año_actual = ultimo_año
        meses_desde_inicio_actual = ultimo_meses_desde_inicio
        
        for i in range(1, meses_a_predecir + 1):
            mes_actual += 1
            meses_desde_inicio_actual += 1
            
            if mes_actual > 12:
                mes_actual = 1
                año_actual += 1
            
            future_dates.append({
                'año': año_actual,
                'mes': mes_actual,
                'meses_desde_inicio': meses_desde_inicio_actual,
                'mes_sin': np.sin(2 * np.pi * mes_actual / 12),
                'mes_cos': np.cos(2 * np.pi * mes_actual / 12)
            })
        
        future_df = pd.DataFrame(future_dates)
        X_future = future_df[['meses_desde_inicio', 'mes_sin', 'mes_cos']]
        predictions = model.predict(X_future)

        historico_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": float(row.total_ventas)}
            for row in data.itertuples(index=False)
        ]

        prediccion_data = [
            {"mes": f"{row.mes}-{row.año}", "ventas": round(float(pred), 2)}
            for row, pred in zip(future_df.itertuples(index=False), predictions)
        ]

        resultado = {
            "historico": historico_data,
            "predicciones": prediccion_data
        }

        return Response(resultado, status=status.HTTP_200_OK)