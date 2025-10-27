
from flask import Blueprint, jsonify, request
from app.controllers.ibov_controller import IbovController

# LSTM imports - desabilitado temporariamente até instalar TensorFlow
try:
    from app.controllers.stock_data_controller import StockDataController
    from app.controllers.lstm_controller import LSTMController
    LSTM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LSTM não disponível: {e}")
    print("⚠️  Instale TensorFlow: pip install tensorflow==2.15.0")
    LSTM_AVAILABLE = False

import random
from datetime import datetime

bp = Blueprint('main', __name__)



@bp.route('/ibov/scrap', methods=['POST'])
def scrap_ibov():
    return IbovController.scrap_ibov()


@bp.route('/ibov/ativos', methods=['GET'])
def listar_ibov_ativos():
    return IbovController.listar_ativos()


@bp.route('/ibov/scrap-historico', methods=['POST'])
def scrap_historico():
    return IbovController.scrap_historico(meses=6)



@bp.route('/ml/refinar', methods=['POST'])
def refinar_dados():
    from app.controllers.ml_controller import MLController
    return MLController.refinar_dados()

@bp.route('/ml/dados-refinados', methods=['GET'])
def listar_dados_refinados():
    from app.models.dados_refinados_model import DadosRefinados
    
    try:
        dados = DadosRefinados.query.order_by(DadosRefinados.data_processamento.desc()).all()
        
        if not dados:
            return jsonify({
                "dados_refinados": [],
                "total": 0,
                "message": "Nenhum dado refinado encontrado. Execute o refinamento primeiro."
            }), 200
        
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
    from app.controllers.ml_controller import MLController
    return MLController.treinar_modelo()

@bp.route('/ml/prever', methods=['POST'])
def prever():
    from app.controllers.ml_controller import MLController
    data = request.get_json() or {}
    
    codigo = data.get('codigo')
    codigos = data.get('codigos')
    
    if not codigo and not codigos:
        return jsonify({"error": "Campo 'codigo' ou 'codigos' obrigatório"}), 400
    
    if codigo:
        return MLController.prever(codigo)
    
    if codigos:
        try:
            from app.services.ml_service import MLService
            from app.models.dados_refinados_model import DadosRefinados
            from app.models.ibov_model import IbovAtivo
            
            total_ativos = IbovAtivo.query.with_entities(IbovAtivo.codigo).distinct().count()
            total_refinados = DadosRefinados.query.with_entities(DadosRefinados.codigo).distinct().count()
            
            print(f"DEBUG - Total de ativos únicos no banco ibov_ativos: {total_ativos}")
            print(f"DEBUG - Total de códigos únicos com dados refinados: {total_refinados}")
            
            codigos_com_dados = DadosRefinados.query.with_entities(DadosRefinados.codigo).distinct().all()
            codigos_unicos = [c[0] for c in codigos_com_dados]
            
            print(f"DEBUG - Códigos únicos com dados refinados: {len(codigos_unicos)}")
            
            ml_service = MLService()
            predicoes = []
            codigos_com_erro = []
            
            for cod in codigos_unicos:
                try:
                    resultado = ml_service.prever(cod.upper())
                    
                    if 'erro' not in resultado:
                        predicoes.append({
                            'codigo': resultado['codigo'],
                            'predicao': resultado['recomendacao'],
                            'confianca': resultado['confianca'],
                            'probabilidade': resultado['probabilidades']['comprar'] / 100
                        })
                    else:
                        codigos_com_erro.append(f"{cod}: {resultado['erro']}")
                except Exception as e:
                    codigos_com_erro.append(f"{cod}: {str(e)}")
                    continue
            
            print(f"DEBUG - Total de predições realizadas: {len(predicoes)}")
            print(f"DEBUG - Total de códigos com erro: {len(codigos_com_erro)}")
            if codigos_com_erro:
                print(f"DEBUG - Primeiros 5 erros: {codigos_com_erro[:5]}")
            
            return jsonify({"predicoes": predicoes}), 200
            
        except Exception as e:
            return jsonify({"error": f"Erro ao processar predições: {str(e)}"}), 500

@bp.route('/ml/metricas', methods=['GET'])
def obter_metricas():
    from app.controllers.ml_controller import MLController
    return MLController.obter_metricas()



@bp.route('/', methods=['GET'])
def status():
    lstm_status = "✅ Funcionando (Fase 4)" if LSTM_AVAILABLE else "⚠️ TensorFlow não instalado"
    return {
        "status": "API FIAP Tech Challenge - Fase 4",
        "version": "2.0",
        "projeto": "Deep Learning - Predição de Preços com LSTM",
        "funcionalidades": {
            "scraping_ibovespa": "✅ Funcionando (Fase 3)",
            "ml_tradicional": "✅ Funcionando (Fase 3)",
            "lstm_deep_learning": lstm_status,
            "yahoo_finance": "✅ Integrado (yfinance)" if LSTM_AVAILABLE else "⚠️ Requer TensorFlow"
        },
        "endpoints": {
            "fase_3": {
                "scraping": "/ibov/scrap (POST)",
                "listar": "/ibov/ativos (GET)",
                "ml_refinar": "/ml/refinar (POST)",
                "ml_treinar": "/ml/treinar (POST)",
                "ml_prever": "/ml/prever (POST)"
            },
            "fase_4": {
                "stock_data": {
                    "coletar": "/api/stock-data/coletar (POST)",
                    "listar_symbols": "/api/stock-data/symbols (GET)",
                    "obter_dados": "/api/stock-data/<symbol> (GET)",
                    "info_empresa": "/api/stock-data/<symbol>/info (GET)",
                    "deletar": "/api/stock-data/<symbol> (DELETE)"
                } if LSTM_AVAILABLE else "⚠️ Requer TensorFlow",
                "lstm": {
                    "treinar": "/api/lstm/treinar (POST)",
                    "prever": "/api/lstm/prever/<symbol> (GET)",
                    "listar_modelos": "/api/lstm/modelos (GET)",
                    "metricas": "/api/lstm/metricas/<model_name> (GET)"
                } if LSTM_AVAILABLE else "⚠️ Requer TensorFlow"
            },
            "documentacao": "/swagger",
            "instalacao_tensorflow": "pip install tensorflow==2.15.0 protobuf==3.20.3" if not LSTM_AVAILABLE else None
        }
    }


# ========================================
# ROTAS FASE 4 - LSTM e Stock Data
# ========================================

if LSTM_AVAILABLE:
    # Stock Data Routes
    @bp.route('/api/stock-data/coletar', methods=['POST'])
    def coletar_dados_stock():
        """Coleta dados históricos de ações usando yfinance"""
        return StockDataController.coletar_dados()

    @bp.route('/api/stock-data/symbols', methods=['GET'])
    def listar_symbols():
        """Lista todos os símbolos disponíveis"""
        return StockDataController.listar_symbols()

    @bp.route('/api/stock-data/<symbol>', methods=['GET'])
    def obter_dados_stock(symbol):
        """Obtém dados históricos de um símbolo"""
        return StockDataController.obter_dados(symbol)

    @bp.route('/api/stock-data/<symbol>/info', methods=['GET'])
    def obter_info_empresa(symbol):
        """Obtém informações da empresa"""
        return StockDataController.obter_info_empresa(symbol)

    @bp.route('/api/stock-data/<symbol>', methods=['DELETE'])
    def deletar_dados_stock(symbol):
        """Deleta dados de um símbolo"""
        return StockDataController.deletar_dados(symbol)

    # LSTM Routes
    @bp.route('/api/lstm/treinar', methods=['POST'])
    def treinar_lstm():
        """Treina modelo LSTM para predição de preços"""
        return LSTMController.treinar_modelo()

    @bp.route('/api/lstm/prever/<symbol>', methods=['GET'])
    def prever_lstm(symbol):
        """Faz previsões de preços usando LSTM"""
        return LSTMController.prever_precos(symbol)

    @bp.route('/api/lstm/modelos', methods=['GET'])
    def listar_modelos_lstm():
        """Lista modelos LSTM treinados"""
        return LSTMController.listar_modelos()

    @bp.route('/api/lstm/metricas/<model_name>', methods=['GET'])
    def obter_metricas_lstm(model_name):
        """Obtém métricas de um modelo LSTM"""
        return LSTMController.obter_metricas(model_name)
else:
    # Rotas stub quando LSTM não está disponível
    @bp.route('/api/stock-data/coletar', methods=['POST'])
    def coletar_dados_stock():
        return jsonify({"erro": "TensorFlow não instalado. Execute: pip install tensorflow==2.15.0 protobuf==3.20.3"}), 503

    @bp.route('/api/lstm/treinar', methods=['POST'])
    def treinar_lstm():
        return jsonify({"erro": "TensorFlow não instalado. Execute: pip install tensorflow==2.15.0 protobuf==3.20.3"}), 503