
from flask import Flask, send_from_directory, Response
from flask_swagger_ui import get_swaggerui_blueprint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import os
from app.utils.extensions import db, metrics
from app.routes.routes import bp as main_bp


# Modelos LSTM - Fase 4
from app.models.stock_data_model import StockData
from app.models.lstm_model_info import LSTMModel


def create_app():
    app = Flask(__name__)
    
    # Inicializa métricas do Prometheus
    metrics.init_app(app)
    
    # Rota Manual de Métricas (Fallback para garantir funcionamento)
    @app.route('/metrics')
    def metrics_manual():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    
    # Informações estáticas da aplicação
    metrics.info('app_info', 'Application info', version='1.0.0')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dados.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    SWAGGER_URL = '/swagger'
    API_URL = '/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "FIAP Tech Challenge Fase 4 - Deep Learning LSTM API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    db.init_app(app)

    app.register_blueprint(main_bp)

    @app.route('/')
    def hello():
        return {
            'mensagem': 'API FIAP Tech Challenge - Fase 4',
            'projeto': 'Deep Learning - Predição de Preços com LSTM',
            'status': 'Funcionando',
            'documentacao': '/swagger',
            'endpoints_principais': {
                'lstm_treinar': '/api/lstm/treinar',
                'lstm_prever': '/api/lstm/prever/<symbol>',
                'stock_data_coletar': '/api/stock-data/coletar'
            }
        }

    @app.route('/swagger.json')
    def swagger_json():
        return send_from_directory(
            os.path.dirname(os.path.abspath(__file__)), 
            'swagger.json'
        )

    return app




if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    # Host 0.0.0.0 permite acesso externo (necessário para o Prometheus no Docker acessar)
    app.run(host='0.0.0.0', debug=True)
