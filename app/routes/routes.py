"""
Routes - Definição das rotas da API
Mapeia URLs para os controllers (sem lógica de negócio)
"""
from flask import Blueprint, jsonify, request
from app.controllers.ibov_controller import IbovController
import random
from datetime import datetime

bp = Blueprint('main', __name__)


# ========== ROTAS IBOV (Scraping) ==========

@bp.route('/ibov/scrap', methods=['POST'])
def scrap_ibov():
    """Rota para fazer scraping dos dados do IBOVESPA"""
    return IbovController.scrap_ibov()


@bp.route('/ibov/ativos', methods=['GET'])
def listar_ibov_ativos():
    """Rota para listar ativos IBOV salvos"""
    return IbovController.listar_ativos()


@bp.route('/ibov/scrap-historico', methods=['POST'])
def scrap_historico():
    """Rota para coletar dados históricos (6 meses)"""
    return IbovController.scrap_historico(meses=6)


# ========== ROTAS ML (REAL) ==========

@bp.route('/ml/refinar', methods=['POST'])
def refinar_dados():
    """Rota para refinar dados usando MLService real"""
    from app.controllers.ml_controller import MLController
    return MLController.refinar_dados()

@bp.route('/ml/dados-refinados', methods=['GET'])
def listar_dados_refinados():
    """Rota para listar dados refinados REAIS do banco"""
    from app.models.dados_refinados_model import DadosRefinados
    
    try:
        dados = DadosRefinados.query.order_by(DadosRefinados.data_processamento.desc()).all()
        
        if not dados:
            return jsonify({
                "dados_refinados": [],
                "total": 0,
                "message": "Nenhum dado refinado encontrado. Execute o refinamento primeiro."
            }), 200
        
        # Converter para dicionário
        dados_dict = []
        for dado in dados:
            dados_dict.append({
                "id": dado.id,
                "codigo": dado.codigo,
                "nome": dado.nome[:30],
                "participacao_pct": round(dado.participacao_pct, 3),
                "qtde_teorica": round(dado.qtde_teorica, 4),
                "tipo_on": dado.tipo_on,
                "tipo_pn": dado.tipo_pn,
                "variacao_percentual": round(dado.variacao_percentual or 0, 2),
                "recomendacao": "COMPRAR" if dado.recomendacao == 1 else "VENDER",
                "data_processamento": dado.data_processamento.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return jsonify({
            "dados_refinados": dados_dict,
            "total": len(dados_dict)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar dados refinados: {str(e)}"}), 500

@bp.route('/ml/treinar', methods=['POST'])
def treinar_modelo():
    """Rota para treinar modelo usando MLService real"""
    from app.controllers.ml_controller import MLController
    return MLController.treinar_modelo()

@bp.route('/ml/prever', methods=['POST'])
def prever():
    """Rota para fazer predições usando MLService real"""
    from app.controllers.ml_controller import MLController
    data = request.get_json() or {}
    
    # Suporta tanto código único quanto múltiplos códigos
    codigo = data.get('codigo')
    codigos = data.get('codigos')
    
    if not codigo and not codigos:
        return jsonify({"error": "Campo 'codigo' ou 'codigos' obrigatório"}), 400
    
    # Se for código único
    if codigo:
        return MLController.prever(codigo)
    
    # Se forem múltiplos códigos
    if codigos:
        try:
            from app.services.ml_service import MLService
            ml_service = MLService()
            predicoes = []
            
            for cod in codigos:
                resultado = ml_service.prever(cod.upper())
                
                # Se não tem erro, adiciona à lista
                if 'erro' not in resultado:
                    predicoes.append({
                        'codigo': resultado['codigo'],
                        'predicao': resultado['recomendacao'],
                        'confianca': resultado['confianca'],
                        'probabilidade': resultado['probabilidades']['comprar'] / 100
                    })
            
            return jsonify({"predicoes": predicoes}), 200
            
        except Exception as e:
            return jsonify({"error": f"Erro ao processar predições: {str(e)}"}), 500

@bp.route('/ml/metricas', methods=['GET'])
def obter_metricas():
    """Rota para obter métricas do modelo real"""
    from app.controllers.ml_controller import MLController
    return MLController.obter_metricas()


# ========== STATUS DA API ==========

@bp.route('/', methods=['GET'])
def status():
    """Rota de status da API"""
    return {
        "status": "API IBOVESPA funcionando",
        "version": "1.0",
        "funcionalidades": {
            "scraping": "✅ Funcionando",
            "ml": "✅ Funcionando (Real)"
        },
        "endpoints": {
            "scraping": "/ibov/scrap (POST)",
            "listar": "/ibov/ativos (GET)",
            "ml_refinar": "/ml/refinar (POST)",
            "ml_treinar": "/ml/treinar (POST)", 
            "ml_prever": "/ml/prever (POST)",
            "swagger": "/swagger"
        }
    }