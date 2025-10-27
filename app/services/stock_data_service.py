import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

from app.models.stock_data_model import StockData
from app.utils.extensions import db

logger = logging.getLogger(__name__)


class StockDataService:
    """
    Serviço para coleta de dados históricos de ações usando Yahoo Finance (yfinance)
    """
    
    @staticmethod
    def coletar_dados_historicos(symbol: str, start_date: str = None, end_date: str = None, period: str = None) -> dict:
        """
        Coleta dados históricos de uma ação do Yahoo Finance
        
        Args:
            symbol: Símbolo da ação (ex: 'PETR4.SA', 'VALE3.SA', 'AAPL')
            start_date: Data inicial no formato 'YYYY-MM-DD' (opcional se usar period)
            end_date: Data final no formato 'YYYY-MM-DD' (opcional, padrão: hoje)
            period: Período relativo ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        
        Returns:
            dict com informações sobre a coleta
        """
        try:
            # Criar objeto Ticker
            ticker = yf.Ticker(symbol)
            
            # Se usar period, usar método history com period
            if period:
                logger.info(f"Coletando dados de {symbol} com período: {period}")
                df = ticker.history(period=period, auto_adjust=False)
            else:
                # Se não especificar datas, usar período padrão de 2 anos
                if start_date is None and end_date is None:
                    logger.info(f"Coletando dados de {symbol} com período padrão: 2y")
                    df = ticker.history(period='2y', auto_adjust=False)
                else:
                    # Usar datas especificadas
                    if end_date is None:
                        end_date = datetime.now().strftime('%Y-%m-%d')
                    if start_date is None:
                        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
                    
                    logger.info(f"Coletando dados de {symbol} de {start_date} até {end_date}")
                    df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            
            if df is None or df.empty:
                logger.error(f"Nenhum dado retornado para {symbol}")
                return {
                    'erro': f'Nenhum dado encontrado para {symbol}. Verifique se o símbolo está correto (ex: PETR4.SA para ações brasileiras)',
                    'symbol': symbol,
                    'dica': 'Ações brasileiras precisam do sufixo .SA (ex: PETR4.SA, VALE3.SA, ITUB4.SA)'
                }
            
            # Resetar índice para ter a data como coluna
            df.reset_index(inplace=True)
            
            # Determinar período real dos dados coletados
            data_inicio = df['Date'].min().strftime('%Y-%m-%d')
            data_fim = df['Date'].max().strftime('%Y-%m-%d')
            
            registros_inseridos = 0
            registros_duplicados = 0
            
            # Inserir dados no banco
            for _, row in df.iterrows():
                try:
                    # Verificar se já existe
                    existing = StockData.query.filter_by(
                        symbol=symbol,
                        date=row['Date'].date()
                    ).first()
                    
                    if existing:
                        registros_duplicados += 1
                        continue
                    
                    # Criar novo registro
                    stock_data = StockData(
                        symbol=symbol,
                        date=row['Date'].date(),
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']),
                        adj_close=float(row['Adj Close']) if 'Adj Close' in row else float(row['Close'])
                    )
                    
                    db.session.add(stock_data)
                    registros_inseridos += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao inserir registro: {e}")
                    continue
            
            db.session.commit()
            
            logger.info(f"Coleta concluída: {registros_inseridos} inseridos, {registros_duplicados} duplicados")
            
            return {
                'mensagem': 'Dados coletados com sucesso',
                'symbol': symbol,
                'periodo': {
                    'inicio': data_inicio,
                    'fim': data_fim
                },
                'estatisticas': {
                    'total_registros': len(df),
                    'registros_inseridos': registros_inseridos,
                    'registros_duplicados': registros_duplicados
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados: {e}")
            db.session.rollback()
            return {
                'erro': f'Erro ao coletar dados: {str(e)}',
                'symbol': symbol
            }
    
    @staticmethod
    def obter_dados_symbol(symbol: str, limit: int = 100) -> dict:
        """
        Obtém dados históricos de uma ação do banco de dados
        
        Args:
            symbol: Símbolo da ação
            limit: Número máximo de registros (padrão: 100)
        
        Returns:
            dict com os dados
        """
        try:
            dados = StockData.query.filter_by(symbol=symbol)\
                .order_by(StockData.date.desc())\
                .limit(limit)\
                .all()
            
            if not dados:
                return {
                    'erro': f'Nenhum dado encontrado para {symbol}',
                    'symbol': symbol
                }
            
            return {
                'symbol': symbol,
                'total': len(dados),
                'dados': [d.to_dict() for d in reversed(dados)]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados: {e}")
            return {
                'erro': f'Erro ao obter dados: {str(e)}',
                'symbol': symbol
            }
    
    @staticmethod
    def listar_symbols_disponiveis() -> dict:
        """
        Lista todos os símbolos disponíveis no banco de dados
        
        Returns:
            dict com lista de símbolos
        """
        try:
            # Query para obter símbolos únicos e contar registros
            symbols = db.session.query(
                StockData.symbol,
                db.func.count(StockData.id).label('total_registros'),
                db.func.min(StockData.date).label('data_inicio'),
                db.func.max(StockData.date).label('data_fim')
            ).group_by(StockData.symbol).all()
            
            return {
                'total_symbols': len(symbols),
                'symbols': [
                    {
                        'symbol': s.symbol,
                        'total_registros': s.total_registros,
                        'periodo': {
                            'inicio': s.data_inicio.strftime('%Y-%m-%d'),
                            'fim': s.data_fim.strftime('%Y-%m-%d')
                        }
                    }
                    for s in symbols
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar símbolos: {e}")
            return {
                'erro': f'Erro ao listar símbolos: {str(e)}'
            }
    
    @staticmethod
    def deletar_dados_symbol(symbol: str) -> dict:
        """
        Deleta todos os dados de um símbolo
        
        Args:
            symbol: Símbolo da ação
        
        Returns:
            dict com informações sobre a deleção
        """
        try:
            count = StockData.query.filter_by(symbol=symbol).count()
            
            if count == 0:
                return {
                    'erro': f'Nenhum dado encontrado para {symbol}',
                    'symbol': symbol
                }
            
            StockData.query.filter_by(symbol=symbol).delete()
            db.session.commit()
            
            return {
                'mensagem': f'Dados de {symbol} deletados com sucesso',
                'symbol': symbol,
                'registros_deletados': count
            }
            
        except Exception as e:
            logger.error(f"Erro ao deletar dados: {e}")
            db.session.rollback()
            return {
                'erro': f'Erro ao deletar dados: {str(e)}',
                'symbol': symbol
            }
    
    @staticmethod
    def obter_info_empresa(symbol: str) -> dict:
        """
        Obtém informações sobre a empresa usando yfinance
        
        Args:
            symbol: Símbolo da ação
        
        Returns:
            dict com informações da empresa
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'nome': info.get('longName', 'N/A'),
                'setor': info.get('sector', 'N/A'),
                'industria': info.get('industry', 'N/A'),
                'pais': info.get('country', 'N/A'),
                'moeda': info.get('currency', 'N/A'),
                'website': info.get('website', 'N/A'),
                'descricao': info.get('longBusinessSummary', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da empresa: {e}")
            return {
                'erro': f'Erro ao obter informações: {str(e)}',
                'symbol': symbol
            }
