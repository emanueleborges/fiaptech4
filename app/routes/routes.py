from flask import Blueprint, request
bp = Blueprint('main', __name__)
from app.controllers.stock_data_controller import StockDataController
from app.controllers.lstm_controller import LSTMController

bp = Blueprint('main', __name__)

# Rotas Fase 4 - Stock Data
@bp.route('/api/stock-data/coletar', methods=['POST'])
def coletar_dados_stock():
    return StockDataController.coletar_dados()

@bp.route('/api/stock-data/symbols', methods=['GET'])
def listar_symbols():
    return StockDataController.listar_symbols()

@bp.route('/api/stock-data/<symbol>', methods=['GET'])
def obter_dados_stock(symbol):
    return StockDataController.obter_dados(symbol)

@bp.route('/api/stock-data/<symbol>', methods=['DELETE'])
def deletar_dados_stock(symbol):
    return StockDataController.deletar_dados(symbol)

# Rotas Fase 4 - LSTM
@bp.route('/api/lstm/treinar', methods=['POST'])
def treinar_lstm():
    return LSTMController.treinar_modelo()

@bp.route('/api/lstm/prever/<symbol>', methods=['GET'])
def prever_lstm(symbol):
    return LSTMController.prever_precos(symbol)

@bp.route('/api/lstm/modelos', methods=['GET'])
def listar_modelos_lstm():
    return LSTMController.listar_modelos()
