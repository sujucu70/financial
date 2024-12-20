from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from typing import Dict
import os
import pandas as pd
import numpy as np
import logging
import json
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    # Placeholder implementation
    monthly_expenses = df.groupby('mes')['importe'].sum()
    last_month_expense = monthly_expenses.iloc[-1]
    predicted_amount = last_month_expense * 1.05  # Example prediction logic
    confidence_level = 0.95  # Example confidence level
    lower_bound = predicted_amount * 0.9
    upper_bound = predicted_amount * 1.1

    return {
        "predicted_amount": predicted_amount,
        "confidence_level": confidence_level,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound
    }

@app.post("/api/register")
async def register(data: dict):
    alias = data.get('alias')
    password = data.get('password')
    sector = data.get('sector')
    comunidad_autonoma = data.get('comunidadAutonoma')

    print(f"Alias: {alias}")
    print(f"Password: {password}")
    print(f"Sector: {sector}")
    print(f"Comunidad Autónoma: {comunidad_autonoma}")

    return {"message": "Registration successful!"}, 200

@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...), sector: str = '', comunidad_autonoma: str = ''):
    try:
        logger.info(f"Iniciando análisis de archivo: {file.filename}")
        contents = await file.read()
        logger.debug("Archivo leído correctamente")
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        logger.debug(f"Columnas en el CSV: {df.columns.tolist()}")
        required_columns = ['fecha', 'categoria', 'concepto', 'importe', 'tipo_gasto']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            error_msg = f"Faltan columnas requeridas: {missing_cols}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        df['fecha'] = pd.to_datetime(df['fecha'])
        df['importe'] = pd.to_numeric(df['importe'], errors='coerce')
        df = df.dropna(subset=['importe'])
        logger.debug(f"Datos procesados: {len(df)} filas válidas")
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        monthly_expenses = df.groupby('mes')['importe'].sum().to_dict()

        ai_analysis = generate_mock_analysis(df, sector, comunidad_autonoma)

        prediction_data = calculate_prediction_with_confidence(df)
        chart_data = [{"month": k, "gastos": float(v)} for k, v in monthly_expenses.items()]
        if chart_data:
            next_month = pd.Timestamp(list(monthly_expenses.keys())[-1]) + pd.DateOffset(months=1)
            chart_data.append({
                "month": next_month.strftime('%Y-%m'),
                "gastos": prediction_data['predicted_amount'],
                "isPrediction": True,
                "lowerBound": prediction_data['lower_bound'],
                "upperBound": prediction_data['upper_bound']
            })

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

def generate_mock_analysis(df: pd.DataFrame, sector: str, comunidad_autonoma: str) -> Dict:
    try:
        # Aggregate data for analysis
        category_stats = df.groupby('categoria')['importe'].agg(['sum', 'mean', 'count']).round(2)
        tipo_gasto_stats = df.groupby('tipo_gasto')['importe'].sum().round(2)

        # Prepare prompt for OpenAI
        prompt = f"""
        Analiza los datos financieros de una PYME del sector '{sector}' en '{comunidad_autonoma}'. teniendo en cuenta patrones estacionales que impacten en los ingresos y gastos del negocio, factores regionales específicos Tendencias de mercado relevantes para el sector {sector} en {comunidad_autonoma}. 
        Genera un informe detallado:
        1. Patrones: Describir patrones de gasto, impacto en el negocio, y severidad (alto/medio/bajo).
        2. Anomalías: Describir anomalías, causas probables, nivel de riesgo (alto/medio/bajo), y acciones inmediatas recomendadas.
        3. Recomendaciones: Comparar con promedios de la industria, identificar brechas de rendimiento, y oportunidades de mejora. Con estos datos, generar listado de 3 acciones recomendadas, impacto esperado, dificultad de implementación (alta/media/baja), plazo estimado (corto/medio/largo), recursos necesarios, y potencial de ROI (alto/medio/bajo).
        La respuesta debe seguir el siguiente formato JSON:
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
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un analista financiero. Responde solo con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        raw_response = response.choices[0].message['content'].strip()
        logger.debug(f"Respuesta de OpenAI: {raw_response}")

        return json.loads(raw_response)

    except Exception as e:
        logger.error(f"Error en análisis: {str(e)}")
        return {
            "patterns": ["Error en análisis", "Revise los datos", "Intente nuevamente"],
            "anomalies": ["No se pudo analizar", "Sistema en modo fallback"],
            "recommendations": ["Verificar datos", "Reintentar más tarde"]
        }

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
