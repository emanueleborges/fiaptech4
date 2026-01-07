from flask import Blueprint, request
from app.controllers.stock_data_controller import StockDataController
from app.controllers.lstm_controller import LSTMController
from app.utils.extensions import metrics

bp = Blueprint('main', __name__)

# Rotas Fase 4 - Stock Data
@bp.route('/api/stock-data/coletar', methods=['POST'])
@metrics.counter('stock_data_coletar_calls', 'Número de coletas de dados realizadas')
def coletar_dados_stock():
    return StockDataController.coletar_dados()

@bp.route('/api/stock-data/symbols', methods=['GET'])
@metrics.counter('stock_data_list_symbols_calls', 'Total de solicitacoes para listar simbolos disponiveis')
def listar_symbols():
    return StockDataController.listar_symbols()

@bp.route('/api/stock-data/<symbol>', methods=['GET'])
@metrics.counter('stock_data_get_calls', 'Total de solicitacoes de dados de uma acao', labels={'symbol': lambda: request.view_args['symbol']})
def obter_dados_stock(symbol):
    return StockDataController.obter_dados(symbol)

@bp.route('/api/stock-data/<symbol>', methods=['DELETE'])
@metrics.counter('stock_data_delete_calls', 'Total de solicitacoes para deletar dados')
def deletar_dados_stock(symbol):
    return StockDataController.deletar_dados(symbol)

# Rotas Fase 4 - LSTM
@bp.route('/api/lstm/treinar', methods=['POST'])
@metrics.summary('lstm_treinar_seconds', 'Duração do treinamento do modelo LSTM')
def treinar_lstm():
    return LSTMController.treinar_modelo()

@bp.route('/api/lstm/prever/<symbol>', methods=['GET'])
@metrics.counter('lstm_prever_calls', 'Número de previsões solicitadas', labels={'symbol': lambda: request.view_args['symbol']})
def prever_lstm(symbol):
    return LSTMController.prever_precos(symbol)

@bp.route('/api/lstm/modelos', methods=['GET'])
@metrics.counter('lstm_list_models_calls', 'Total de solicitacoes para listar modelos treinados')
def listar_modelos_lstm():
    return LSTMController.listar_modelos()
