from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

db = SQLAlchemy()
# metrics = PrometheusMetrics(app=None) # Removido para evitar conflito
metrics = PrometheusMetrics(app=None, path=None) # path=None para não criar rota automática, usar a manual

