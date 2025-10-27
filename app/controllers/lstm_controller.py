from flask import jsonify, request
from app.services.lstm_service import LSTMService


class LSTMController:
    """
    Controller para treinamento e previsão com modelos LSTM
    """
    
    @staticmethod
    def treinar_modelo():
        """
        Endpoint para treinar modelo LSTM
        POST /api/lstm/treinar
        Body: {
            "symbol": "PETR4.SA",
            "epochs": 50,
            "batch_size": 32,
            "sequence_length": 60,
            "units": 50
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'symbol' not in data:
                return jsonify({
                    'erro': 'Campo obrigatório: symbol'
                }), 400
            
            symbol = data['symbol']
            epochs = data.get('epochs', 50)
            batch_size = data.get('batch_size', 32)
            sequence_length = data.get('sequence_length', 60)
            units = data.get('units', 50)
            
            service = LSTMService()
            resultado = service.treinar_modelo(
                symbol=symbol,
                epochs=epochs,
                batch_size=batch_size,
                sequence_length=sequence_length,
                units=units
            )
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def prever_precos(symbol):
        """
        Endpoint para fazer previsões de preços
        GET /api/lstm/prever/<symbol>?dias=5&model_name=lstm_PETR4_20241026
        """
        try:
            dias = request.args.get('dias', 5, type=int)
            model_name = request.args.get('model_name', None)
            
            if dias < 1 or dias > 30:
                return jsonify({
                    'erro': 'Número de dias deve estar entre 1 e 30'
                }), 400
            
            service = LSTMService()
            resultado = service.prever_proximos_dias(
                symbol=symbol,
                dias=dias,
                model_name=model_name
            )
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def listar_modelos():
        """
        Endpoint para listar modelos treinados
        GET /api/lstm/modelos?symbol=PETR4.SA
        """
        try:
            symbol = request.args.get('symbol', None)
            
            service = LSTMService()
            resultado = service.listar_modelos(symbol)
            
            if 'erro' in resultado:
                return jsonify(resultado), 500
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def obter_metricas(model_name):
        """
        Endpoint para obter métricas de um modelo
        GET /api/lstm/metricas/<model_name>
        """
        try:
            service = LSTMService()
            resultado = service.obter_metricas_modelo(model_name)
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
