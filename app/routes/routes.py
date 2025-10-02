"""
Routes - Definição das rotas da API IBOV
Apenas mapeia URLs para os controllers (sem lógica de negócio)
"""
from flask import Blueprint
from app.controllers.ibov_controller import IbovController

bp = Blueprint('main', __name__)


@bp.route('/ibov/scrap', methods=['POST'])
def scrap_ibov():
    """Rota para fazer scraping dos dados do IBOVESPA"""
    return IbovController.scrap_ibov()


@bp.route('/ibov/ativos', methods=['GET'])
def listar_ibov_ativos():
    """Rota para listar ativos IBOV salvos"""
    return IbovController.listar_ativos()
