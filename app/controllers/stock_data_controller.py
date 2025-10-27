from flask import jsonify, request
from app.services.stock_data_service import StockDataService


class StockDataController:
    """
    Controller para gerenciamento de dados históricos de ações
    """
    
    @staticmethod
    def coletar_dados():
        """
        Endpoint para coletar dados históricos de ações
        POST /api/stock-data/coletar
        Body: {"symbol": "PETR4.SA", "period": "2y"} OU
              {"symbol": "PETR4.SA", "start_date": "2023-01-01", "end_date": "2025-10-26"}
        """
        try:
            data = request.get_json()
            
            if not data or 'symbol' not in data:
                return jsonify({
                    'erro': 'Campo obrigatório: symbol',
                    'exemplo1': '{"symbol": "PETR4.SA", "period": "2y"}',
                    'exemplo2': '{"symbol": "PETR4.SA", "start_date": "2023-01-01"}',
                    'periodos_validos': ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
                }), 400
            
            symbol = data['symbol'].upper()
            period = data.get('period', None)
            start_date = data.get('start_date', None)
            end_date = data.get('end_date', None)
            
            # Se não especificar nada, usar período padrão de 2 anos
            if not period and not start_date:
                period = '2y'
            
            service = StockDataService()
            resultado = service.coletar_dados_historicos(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            
            if 'erro' in resultado:
                return jsonify(resultado), 400
            
            return jsonify(resultado), 201
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def obter_dados(symbol):
        """
        Endpoint para obter dados históricos armazenados
        GET /api/stock-data/<symbol>?limit=100
        """
        try:
            limit = request.args.get('limit', 100, type=int)
            
            service = StockDataService()
            resultado = service.obter_dados_symbol(symbol, limit)
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def listar_symbols():
        """
        Endpoint para listar todos os símbolos disponíveis
        GET /api/stock-data/symbols
        """
        try:
            service = StockDataService()
            resultado = service.listar_symbols_disponiveis()
            
            if 'erro' in resultado:
                return jsonify(resultado), 500
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def deletar_dados(symbol):
        """
        Endpoint para deletar dados de um símbolo
        DELETE /api/stock-data/<symbol>
        """
        try:
            service = StockDataService()
            resultado = service.deletar_dados_symbol(symbol)
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
    
    @staticmethod
    def obter_info_empresa(symbol):
        """
        Endpoint para obter informações da empresa
        GET /api/stock-data/<symbol>/info
        """
        try:
            service = StockDataService()
            resultado = service.obter_info_empresa(symbol)
            
            if 'erro' in resultado:
                return jsonify(resultado), 404
            
            return jsonify(resultado), 200
            
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
