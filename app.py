from apscheduler.schedulers.background import BackgroundScheduler
from app.b3scraper import B3Scraper
from flask import send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask
from app.extensions import db
from app.routes import bp as main_bp

def create_app():
    app = Flask(__name__)
    # Configuração do banco de dados (pode ser alterada para PostgreSQL, MySQL, etc)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dados.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Swagger UI config
    SWAGGER_URL = '/swagger'
    API_URL = '/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "API de Coleta de Dados em Tempo Real"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Inicializa extensões
    db.init_app(app)

    # Registra blueprints (rotas)
    app.register_blueprint(main_bp)

    @app.route('/')
    def hello():
        return 'API Flask pronta para coletar dados em tempo real!'

    # Rota para servir o swagger.json
    @app.route('/swagger.json')
    def swagger_json():
        import os
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'swagger.json')

    return app

def agendar_scraping(app):
    from app.models import IbovAtivo
    from app.extensions import db
    from datetime import datetime
    scheduler = BackgroundScheduler()
    def job():
        with app.app_context():
            scraper = B3Scraper()
            ativos = scraper.fetch_ibov_data()
            salvos = 0
            for ativo in ativos:
                existe = IbovAtivo.query.filter_by(codigo=ativo['codigo_acao'], data=datetime.strptime(ativo['data_pregao'], '%Y-%m-%d').date()).first()
                if not existe:
                    novo = IbovAtivo(
                        codigo=ativo['codigo_acao'],
                        nome=ativo['nome_empresa'],
                        tipo=ativo['tipo_acao'],
                        participacao=ativo['percentual_participacao'],
                        data=datetime.strptime(ativo['data_pregao'], '%Y-%m-%d').date()
                    )
                    db.session.add(novo)
                    salvos += 1
            db.session.commit()
            print(f"[APScheduler] IBOV atualizado automaticamente. {salvos} ativos salvos.")
    scheduler.add_job(job, 'cron', hour=6, minute=0)  # Executa todo dia às 6h
    scheduler.start()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    agendar_scraping(app)
    app.run(debug=True)
