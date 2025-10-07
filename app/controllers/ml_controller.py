
from flask import jsonify, request
from app.services.ml_service import MLService
from app.models.dados_refinados_model import DadosRefinados


class MLController:
    
    @staticmethod
    def refinar_dados():
       
        try:
            ml_service = MLService()
            resultado = ml_service.refinar_dados()
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    def listar_dados_refinados(self):
        
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
    
    @staticmethod
    def treinar_modelo():
       
        try:
            # Pode receber parâmetros no body
            data = request.get_json() or {}
            algoritmo = data.get('algoritmo', 'RandomForest')
            
            ml_service = MLService()
            resultado = ml_service.treinar_modelo(algoritmo=algoritmo)
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def prever(codigo):
        
        try:
            ml_service = MLService()
            resultado = ml_service.prever(codigo.upper())
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def obter_metricas():
        
        try:
            ml_service = MLService()
            resultado = ml_service.obter_metricas()
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
