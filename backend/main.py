from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict

import os
import pandas as pd
import numpy as np
import logging
import json


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_prediction_with_confidence(df: pd.DataFrame) -> Dict:
    """Calcula la predicción y nivel de confianza para el próximo mes"""
    try:
        logger.debug("Iniciando cálculo de predicción")
        
        # Asegurar que la fecha está en el formato correcto
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        
        # Calcular gastos mensuales
        monthly_expenses = df.groupby('mes')['importe'].sum()
        logger.debug(f"Gastos mensuales calculados: {monthly_expenses.to_dict()}")
        
        # Calcular variación mes a mes
        monthly_changes = monthly_expenses.pct_change().fillna(0)
        
        # Calcular predicción base
        if len(monthly_expenses) >= 3:
            base_prediction = monthly_expenses[-3:].mean()
            std_dev = monthly_expenses[-3:].std()
        else:
            base_prediction = monthly_expenses.mean()
            std_dev = monthly_expenses.std()
        
        # Evitar división por cero
        if base_prediction == 0:
            base_prediction = monthly_expenses.mean() if len(monthly_expenses) > 0 else 1000
            
        std_dev = std_dev if not pd.isna(std_dev) else 0
        
        # Calcular nivel de confianza
        variation_coefficient = (std_dev / base_prediction) if base_prediction != 0 else 0
        confidence_level = max(min(1 - variation_coefficient, 0.95), 0.50)
        
        # Calcular rango de predicción
        margin_of_error = std_dev * 1.96
        lower_bound = max(0, base_prediction - margin_of_error)
        upper_bound = base_prediction + margin_of_error
        
        prediction_data = {
            'predicted_amount': float(base_prediction),
            'confidence_level': float(confidence_level),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'trend': 'increasing' if monthly_changes.mean() > 0 else 'decreasing'
        }
        
        logger.debug(f"Predicción calculada: {prediction_data}")
        return prediction_data
        
    except Exception as e:
        logger.error(f"Error en calculate_prediction_with_confidence: {str(e)}")
        raise

def generate_mock_analysis(df: pd.DataFrame) -> Dict:
    try:
        category_stats = df.groupby('categoria')['importe'].agg(['sum', 'mean', 'count']).round(2)
        tipo_gasto_stats = df.groupby('tipo_gasto')['importe'].sum().round(2)
        
        prompt = f"""Genera un análisis financiero en formato JSON:
{{
    "patterns": [
        "describe patrón 1",
        "describe patrón 2",
        "describe patrón 3"
    ],
    "anomalies": [
        "describe anomalía 1",
        "describe anomalía 2"
    ],
    "recommendations": [
        "describe recomendación 1",
        "describe recomendación 2"
    ]
}}

Datos:
{category_stats.to_string()}
{tipo_gasto_stats.to_string()}

IMPORTANTE: Responde SOLO con el JSON válido."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un analista financiero. Responde solo con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        raw_response = response.choices[0].message.content.strip()
        logger.debug(f"Respuesta de OpenAI: {raw_response}")
        
        return json.loads(raw_response)

    except Exception as e:
        logger.error(f"Error en análisis: {str(e)}")
        return {
            "patterns": ["Error en análisis", "Revise los datos", "Intente nuevamente"],
            "anomalies": ["No se pudo analizar", "Sistema en modo fallback"],
            "recommendations": ["Verificar datos", "Reintentar más tarde"]
        }

@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Iniciando análisis de archivo: {file.filename}")
        
        # Leer el archivo CSV
        contents = await file.read()
        logger.debug("Archivo leído correctamente")
        
        # Convertir a DataFrame
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        logger.debug(f"Columnas en el CSV: {df.columns.tolist()}")
        
        # Validar columnas requeridas
        required_columns = ['fecha', 'categoria', 'concepto', 'importe', 'tipo_gasto']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            error_msg = f"Faltan columnas requeridas: {missing_cols}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Convertir fechas y asegurar que importe es numérico
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['importe'] = pd.to_numeric(df['importe'], errors='coerce')
        df = df.dropna(subset=['importe'])
        
        logger.debug(f"Datos procesados: {len(df)} filas válidas")

        # Procesar datos por mes
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        monthly_expenses = df.groupby('mes')['importe'].sum().to_dict()
        
        # Generar análisis
        ai_analysis = generate_mock_analysis(df)
        prediction_data = calculate_prediction_with_confidence(df)
        
        # Preparar datos para el gráfico
        chart_data = [{"month": k, "gastos": float(v)} for k, v in monthly_expenses.items()]
        
        # Añadir predicción
        if chart_data:
            next_month = pd.Timestamp(list(monthly_expenses.keys())[-1]) + pd.DateOffset(months=1)
            chart_data.append({
                "month": next_month.strftime('%Y-%m'),
                "gastos": prediction_data['predicted_amount'],
                "isPrediction": True,
                "lowerBound": prediction_data['lower_bound'],
                "upperBound": prediction_data['upper_bound']
            })

        # Estadísticas básicas
        category_stats = df.groupby('categoria')['importe'].agg(['sum', 'mean']).round(2)
        top_category = category_stats['sum'].idxmax()
        
        stats_analysis = {
            "total_gasto": float(df['importe'].sum()),
            "promedio_mensual": float(df.groupby('mes')['importe'].sum().mean()),
            "maximo_gasto": float(df.groupby('mes')['importe'].sum().max()),
            "minimo_gasto": float(df.groupby('mes')['importe'].sum().min()),
            "num_transacciones": len(df),
            "num_categorias": len(df['categoria'].unique()),
            "num_tipos_gasto": len(df['tipo_gasto'].unique()),
            "categoria_mayor_gasto": {
                "nombre": top_category,
                "total": float(category_stats.loc[top_category, 'sum']),
                "promedio": float(category_stats.loc[top_category, 'mean'])
            }
        }

        response_data = {
            "chartData": chart_data,
            "aiAnalysis": ai_analysis,
            "prediction": prediction_data,
            "predictionMessage": (
                f"Previsión para el próximo mes: {prediction_data['predicted_amount']:,.2f}€\n"
                f"Nivel de confianza: {prediction_data['confidence_level']*100:.1f}%\n"
                f"Rango esperado: {prediction_data['lower_bound']:,.2f}€ - {prediction_data['upper_bound']:,.2f}€"
            ),
            "stats": stats_analysis
        }
        
        logger.info("Análisis completado exitosamente")
        return response_data

    except Exception as e:
        logger.error(f"Error durante el análisis: {str(e)}")
        logger.exception("Traceback completo:")
        raise HTTPException(status_code=500, detail=str(e))

# Montar archivos estáticos después de las rutas API
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

@app.get("/")
async def read_root():
    if os.path.exists("../frontend/dist/index.html"):
        return FileResponse("../frontend/dist/index.html")
    return {"message": "API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))