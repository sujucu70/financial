from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import pandas as pd
import numpy as np
from typing import Dict
import logging

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
        logger.debug("Procesando datos...")
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['importe'] = pd.to_numeric(df['importe'], errors='coerce')
        df = df.dropna(subset=['importe'])
        
        # Procesar datos por mes
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        monthly_expenses = df.groupby('mes')['importe'].sum().to_dict()
        
        # Preparar datos para el gráfico
        chart_data = [{"month": k, "gastos": float(v)} for k, v in monthly_expenses.items()]
        
        # Calcular estadísticas básicas
        stats_analysis = {
            "total_gasto": float(df['importe'].sum()),
            "promedio_mensual": float(df['importe'].mean()),
            "maximo_gasto": float(df['importe'].max()),
            "minimo_gasto": float(df['importe'].min()),
            "num_transacciones": len(df)
        }

        logger.info("Análisis completado exitosamente")
        return {
            "chartData": chart_data,
            "stats": stats_analysis
        }

    except Exception as e:
        logger.error(f"Error durante el análisis: {str(e)}")
        logger.exception("Traceback completo:")
        raise HTTPException(status_code=500, detail=str(e))

# Montar archivos estáticos después de las rutas API
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))