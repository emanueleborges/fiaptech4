"""
Aplicação Flask - API de Coleta de Dados do IBOVESPA
Código reorganizado seguindo boas práticas de arquitetura
"""
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import os

# Imports da aplicação (estrutura reorganizada)
from app.services.b3_scraper_service import B3Scraper
from app.utils.extensions import db
from app.routes.routes import bp as main_bp

# Importar modelos para criar tabelas
from app.models.ibov_model import IbovAtivo
from app.models.dados_refinados_model import DadosRefinados
from app.models.modelo_treinado_model import ModeloTreinado


def create_app():
    """Factory para criar e configurar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração do banco de dados
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dados.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Swagger UI config
    SWAGGER_URL = '/swagger'
    API_URL = '/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "API de Coleta de Dados em Tempo Real"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Inicializa extensões
    db.init_app(app)

    # Registra blueprints (rotas)
    app.register_blueprint(main_bp)

    @app.route('/')
    def hello():
        return 'API Flask pronta para coletar dados em tempo real!'

    @app.route('/swagger.json')
    def swagger_json():
        return send_from_directory(
            os.path.dirname(os.path.abspath(__file__)), 
            'swagger.json'
        )

    return app


def agendar_scraping(app):
    """
    Configura o agendamento automático do scraping IBOV
    Executa todo dia às 6h da manhã
    """
    from app.models.ibov_model import IbovAtivo
    from datetime import datetime
    
    scheduler = BackgroundScheduler()
    
    def job():
        with app.app_context():
            scraper = B3Scraper()
            ativos = scraper.fetch_ibov_data()
            salvos = 0
            
            for ativo in ativos:
                # FIX: usar os campos corretos retornados pelo scraper
                existe = IbovAtivo.query.filter_by(
                    codigo=ativo['cod'],  # Era 'codigo_acao' - ERRADO
                    data=datetime.now().date()
                ).first()
                
                if not existe:
                    novo = IbovAtivo(
                        codigo=ativo['cod'],  # Corrigido
                        nome=ativo['asset'],  # Corrigido
                        tipo=ativo['type'],  # Corrigido
                        participacao=ativo['part'],  # Corrigido
                        theoricalQty=ativo['theoricalQty'],  # Adicionado
                        data=datetime.now().date()
                    )
                    db.session.add(novo)
                    salvos += 1
                    
            db.session.commit()
            print(f"[APScheduler] IBOV atualizado automaticamente. {salvos} ativos salvos.")
    
    # Executa todo dia às 6h
    scheduler.add_job(job, 'cron', hour=6, minute=0)
    scheduler.start()


if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    agendar_scraping(app)
    app.run(debug=True)
