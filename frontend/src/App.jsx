import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import { Upload, AlertTriangle, Brain } from 'lucide-react';
import axios from 'axios';

// Definir CustomTooltip fuera del componente principal
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    return (
      <div className="bg-white p-3 border rounded shadow">
        <p className="font-semibold">{label}</p>
        {dataPoint.isPrediction ? (
          <>
            <p className="text-green-600">
              Previsión: {payload[0].value.toFixed(2)}€
            </p>
            <div className="text-sm text-gray-600 mt-1">
              <p>Rango de previsión:</p>
              <p>Mín: {dataPoint.lowerBound.toFixed(2)}€</p>
              <p>Máx: {dataPoint.upperBound.toFixed(2)}€</p>
            </div>
          </>
        ) : (
          <p className="text-blue-600">
            Gastos: {payload[0].value.toFixed(2)}€
          </p>
        )}
      </div>
    );
  }
  return null;
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setData(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error al procesar el archivo');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Análisis Financiero PYME</h1>

      {/* File Upload */}
      <div className="mb-6 p-6 border-2 border-dashed rounded-lg">
        <label className="flex flex-col items-center cursor-pointer">
          <Upload className="w-12 h-12 text-gray-400" />
          <span className="mt-2 text-sm">Subir archivo CSV</span>
          <input
            type="file"
            className="hidden"
            accept=".csv"
            onChange={handleFileUpload}
            disabled={loading}
          />
        </label>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-4">
          <p>Procesando archivo...</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 p-4 rounded-lg mb-6">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Stats Section */}
      {data?.stats && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4">Estadísticas Generales</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded">
              <p className="text-sm text-gray-600">Gasto Total</p>
              <p className="text-lg font-bold">{data.stats.total_gasto.toFixed(2)}€</p>
            </div>
            <div className="p-4 bg-green-50 rounded">
              <p className="text-sm text-gray-600">Promedio Mensual</p>
              <p className="text-lg font-bold">{data.stats.promedio_mensual.toFixed(2)}€</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded">
              <p className="text-sm text-gray-600">Gasto Máximo</p>
              <p className="text-lg font-bold">{data.stats.maximo_gasto.toFixed(2)}€</p>
            </div>
            <div className="p-4 bg-purple-50 rounded">
              <p className="text-sm text-gray-600">Transacciones</p>
              <p className="text-lg font-bold">{data.stats.num_transacciones}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chart Section */}
      {data && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4">Gastos Mensuales y Previsión</h2>
          <BarChart width={600} height={300} data={data.chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar 
              dataKey="gastos"
              name={data.chartData.some(item => item.isPrediction) ? "Gastos Reales" : "Gastos"}
              fill="#8884d8"
            />
            {data.chartData.some(item => item.isPrediction) && (
              <Bar
                dataKey={(entry) => entry.isPrediction ? entry.gastos : null}
                name="Previsión"
                fill="#82ca9d"
              />
            )}
            {data.chartData.map((entry, index) => {
              if (entry.isPrediction) {
                return (
                  <React.Fragment key={`prediction-${index}`}>
                    <ReferenceLine
                      y={entry.lowerBound}
                      stroke="#82ca9d"
                      strokeDasharray="3 3"
                      label={{ value: 'Mín', position: 'right' }}
                    />
                    <ReferenceLine
                      y={entry.upperBound}
                      stroke="#82ca9d"
                      strokeDasharray="3 3"
                      label={{ value: 'Máx', position: 'right' }}
                    />
                  </React.Fragment>
                );
              }
              return null;
            })}
          </BarChart>
        </div>
      )}

      {/* Prediction Section */}
      {data?.prediction && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-6 h-6" />
            Previsión Presupuestaria
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-green-50 rounded">
              <h3 className="font-medium mb-2">Predicción para el Próximo Mes</h3>
              <p className="text-2xl font-bold text-green-700">
                {data.prediction.predicted_amount.toFixed(2)}€
              </p>
              <p className="text-sm text-gray-600 mt-2">
                Nivel de confianza: {(data.prediction.confidence_level * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-4 bg-blue-50 rounded">
              <h3 className="font-medium mb-2">Rango de Predicción</h3>
              <p className="text-sm">Mínimo esperado: <span className="font-bold">{data.prediction.lower_bound.toFixed(2)}€</span></p>
              <p className="text-sm">Máximo esperado: <span className="font-bold">{data.prediction.upper_bound.toFixed(2)}€</span></p>
              <p className="text-xs text-gray-600 mt-2">
                Basado en el análisis de tendencias históricas
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-600 whitespace-pre-line">
            {data.predictionMessage}
          </p>
        </div>
      )}

      {/* AI Analysis Section */}
      {data?.aiAnalysis && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-6 h-6" />
            Análisis IA
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium mb-2">Patrones Detectados</h3>
              <ul className="space-y-2">
                {data.aiAnalysis.patterns.map((pattern, idx) => (
                  <li key={idx} className="bg-blue-50 p-2 rounded">{pattern}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Anomalías</h3>
              <ul className="space-y-2">
                {data.aiAnalysis.anomalies.map((anomaly, idx) => (
                  <li key={idx} className="bg-red-50 p-2 rounded">{anomaly}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Recomendaciones</h3>
              <ul className="space-y-2">
                {data.aiAnalysis.recommendations.map((rec, idx) => (
                  <li key={idx} className="bg-green-50 p-2 rounded">{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;