"""
Controller de Machine Learning
Gerencia endpoints de ML: refinamento, treinamento, predição e métricas
"""
from flask import jsonify, request
from app.services.ml_service import MLService
from app.models.dados_refinados_model import DadosRefinados


class MLController:
    """Controller para operações de Machine Learning"""
    
    def __init__(self):
        self.ml_service = MLService()
    
    def refinar_dados(self):
        """
        POST /ml/refinar
        Refina dados brutos e prepara features para ML
        """
        try:
            resultado = self.ml_service.refinar_dados()
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    def listar_dados_refinados(self):
        """
        GET /ml/dados-refinados
        Lista todos os dados refinados salvos no banco SQLite
        """
        try:
            dados = DadosRefinados.query.all()
            
            resultado = [{
                'codigo': d.codigo,
                'nome': d.nome,
                'participacao_pct': round(d.participacao_pct, 2) if d.participacao_pct else None,
                'qtde_teorica': d.qtde_teorica,
                'variacao_percentual': round(d.variacao_percentual, 2) if d.variacao_percentual else None,
                'media_movel_7d': round(d.media_movel_7d, 2) if d.media_movel_7d else None,
                'volatilidade': round(d.volatilidade, 2) if d.volatilidade else None,
                'recomendacao': 'COMPRAR' if d.recomendacao == 1 else 'VENDER',
                'data_atualizacao': d.data_atualizacao.strftime('%Y-%m-%d %H:%M:%S') if d.data_atualizacao else None
            } for d in dados]
            
            return jsonify({
                'total': len(resultado),
                'dados': resultado
            }), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    def treinar_modelo(self):
        """
        POST /ml/treinar
        Treina novo modelo de Machine Learning
        """
        try:
            # Pode receber parâmetros no body
            data = request.get_json() or {}
            algoritmo = data.get('algoritmo', 'RandomForest')
            
            resultado = self.ml_service.treinar_modelo(algoritmo=algoritmo)
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    def prever(self):
        """
        POST /ml/prever
        Faz predição para uma ou múltiplas ações
        
        Body (individual): {"codigo": "PETR4"}
        Body (lote):       {"codigos": ["PETR4", "VALE3", "ITUB4"]}
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({'erro': 'Body JSON é obrigatório'}), 400
            
            # Caso 1: Predição individual
            if 'codigo' in data:
                codigo = data['codigo']
                resultado = self.ml_service.prever(codigo.upper())
                
                if 'erro' in resultado:
                    return jsonify(resultado), 404
                
                return jsonify(resultado), 200
            
            # Caso 2: Predição em lote
            elif 'codigos' in data:
                codigos = data['codigos']
                if not isinstance(codigos, list):
                    return jsonify({'erro': '"codigos" deve ser uma lista'}), 400
                
                resultados = []
                for codigo in codigos:
                    resultado = self.ml_service.prever(codigo.upper())
                    resultados.append(resultado)
                
                return jsonify({
                    'total': len(codigos),
                    'predicoes': resultados
                }), 200
            
            else:
                return jsonify({
                    'erro': 'Forneça "codigo" (string) ou "codigos" (lista)'
                }), 400
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    def obter_metricas(self):
        """
        GET /ml/metricas
        Retorna métricas do modelo ativo e estatísticas
        """
        try:
            resultado = self.ml_service.obter_metricas()
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
