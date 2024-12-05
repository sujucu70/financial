import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import { Upload, AlertTriangle, Brain } from 'lucide-react';
import axios from 'axios';
import 'tailwindcss/tailwind.css';

// Define CustomTooltip outside the main component
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
  const [alias, setAlias] = useState('');
  const [password, setPassword] = useState('');
  const [sector, setSector] = useState('');
  const [comunidadAutonoma, setComunidadAutonoma] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ alias, password, sector, comunidadAutonoma }),
    });

    if (response.ok) {
      alert('Registration successful!');
    } else {
      alert('Registration failed');
    }
  };

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
      <h1 className="text-2xl font-bold mb-6 text-center">Análisis Financiero PYME</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* File Upload */}
        <div className="mb-6 p-6 border-2 border-dashed rounded-lg flex justify-center items-center">
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

        {/* Registration Form */}
        <div className="mb-6 p-6 border-2 border-dashed rounded-lg">
          <h1 className="text-xl font-bold mb-4">Registro de Usuario</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Alias:</label>
              <input
                type="text"
                value={alias}
                onChange={(e) => setAlias(e.target.value)}
                required
                className="mt-1 block w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Contraseña:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1 block w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Sector:</label>
              <input
                type="text"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                required
                className="mt-1 block w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Comunidad Autónoma:</label>
              <input
                type="text"
                value={comunidadAutonoma}
                onChange={(e) => setComunidadAutonoma(e.target.value)}
                required
                className="mt-1 block w-full p-2 border rounded"
              />
            </div>
            <div>
              <button type="submit" className="w-full p-2 bg-blue-500 text-white rounded">Registrar</button>
            </div>
          </form>
        </div>
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
