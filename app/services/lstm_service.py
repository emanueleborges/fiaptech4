import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import joblib
import logging
import json

from app.models.stock_data_model import StockData
from app.models.lstm_model_info import LSTMModel
from app.utils.extensions import db

logger = logging.getLogger(__name__)


class LSTMService:
    """
    Serviço para criação, treinamento e previsão usando modelos LSTM
    para predição de preços de ações
    """
    
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def preparar_dados(self, symbol: str, sequence_length: int = 60) -> dict:
        """
        Prepara dados para treinamento do modelo LSTM
        
        Args:
            symbol: Símbolo da ação
            sequence_length: Número de dias anteriores para usar como features
        
        Returns:
            dict com dados preparados e informações
        """
        try:
            # Buscar dados do banco
            dados = StockData.query.filter_by(symbol=symbol)\
                .order_by(StockData.date.asc())\
                .all()
            
            if not dados or len(dados) < sequence_length + 50:
                return {
                    'erro': f'Dados insuficientes para {symbol}. Mínimo necessário: {sequence_length + 50} registros'
                }
            
            # Converter para DataFrame
            df = pd.DataFrame([
                {
                    'date': d.date,
                    'close': d.close,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'volume': d.volume
                }
                for d in dados
            ])
            
            df.set_index('date', inplace=True)
            
            # Usar apenas preço de fechamento para simplificar
            data = df[['close']].values
            
            # Normalizar dados
            scaled_data = self.scaler.fit_transform(data)
            
            # Criar sequências
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            
            # Reshape para LSTM [samples, time steps, features]
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            # Dividir em treino e teste (80/20)
            split = int(0.8 * len(X))
            
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # Datas para referência
            train_dates = df.index[:split + sequence_length]
            test_dates = df.index[split + sequence_length:]
            
            return {
                'X_train': X_train,
                'X_test': X_test,
                'y_train': y_train,
                'y_test': y_test,
                'scaler': self.scaler,
                'info': {
                    'total_samples': len(X),
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'sequence_length': sequence_length,
                    'train_start': train_dates[0].strftime('%Y-%m-%d'),
                    'train_end': train_dates[-1].strftime('%Y-%m-%d'),
                    'test_start': test_dates[0].strftime('%Y-%m-%d') if len(test_dates) > 0 else None,
                    'test_end': test_dates[-1].strftime('%Y-%m-%d') if len(test_dates) > 0 else None
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados: {e}")
            return {'erro': f'Erro ao preparar dados: {str(e)}'}
    
    def criar_modelo_lstm(self, sequence_length: int = 60, units: int = 50) -> Sequential:
        """
        Cria arquitetura do modelo LSTM
        
        Args:
            sequence_length: Tamanho da sequência de entrada
            units: Número de unidades LSTM
        
        Returns:
            Modelo LSTM compilado
        """
        model = Sequential([
            # Primeira camada LSTM
            LSTM(units=units, return_sequences=True, input_shape=(sequence_length, 1)),
            Dropout(0.2),
            
            # Segunda camada LSTM
            LSTM(units=units, return_sequences=True),
            Dropout(0.2),
            
            # Terceira camada LSTM
            LSTM(units=units, return_sequences=False),
            Dropout(0.2),
            
            # Camada densa
            Dense(units=25),
            
            # Camada de saída
            Dense(units=1)
        ])
        
        # Compilar modelo
        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def treinar_modelo(self, symbol: str, epochs: int = 50, batch_size: int = 32, 
                      sequence_length: int = 60, units: int = 50) -> dict:
        """
        Treina modelo LSTM para predição de preços
        
        Args:
            symbol: Símbolo da ação
            epochs: Número de épocas de treinamento
            batch_size: Tamanho do batch
            sequence_length: Tamanho da sequência
            units: Número de unidades LSTM
        
        Returns:
            dict com informações do treinamento
        """
        try:
            logger.info(f"Iniciando treinamento LSTM para {symbol}")
            
            # Preparar dados
            data_prep = self.preparar_dados(symbol, sequence_length)
            if 'erro' in data_prep:
                return data_prep
            
            X_train = data_prep['X_train']
            X_test = data_prep['X_test']
            y_train = data_prep['y_train']
            y_test = data_prep['y_test']
            scaler = data_prep['scaler']
            info = data_prep['info']
            
            # Criar modelo
            model = self.criar_modelo_lstm(sequence_length, units)
            
            # Callbacks
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            # Treinar modelo
            logger.info(f"Treinando modelo com {epochs} épocas...")
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                callbacks=[early_stop],
                verbose=1
            )
            
            # Fazer previsões
            test_predict = model.predict(X_test)
            
            # Desnormalizar previsões
            test_predict = scaler.inverse_transform(test_predict)
            y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))
            
            # Calcular métricas
            metrics = self.calcular_metricas(y_test_actual, test_predict)
            
            # Salvar modelo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_name = f'lstm_{symbol}_{timestamp}'
            model_path = os.path.join(self.models_dir, f'{model_name}.h5')
            scaler_path = os.path.join(self.models_dir, f'{model_name}_scaler.pkl')
            
            model.save(model_path)
            joblib.dump(scaler, scaler_path)
            
            # Salvar informações no banco
            lstm_model_info = LSTMModel(
                symbol=symbol,
                model_name=model_name,
                model_path=model_path,
                sequence_length=sequence_length,
                epochs=len(history.history['loss']),
                batch_size=batch_size,
                mae=metrics['mae'],
                rmse=metrics['rmse'],
                mape=metrics['mape'],
                train_start_date=datetime.strptime(info['train_start'], '%Y-%m-%d').date(),
                train_end_date=datetime.strptime(info['train_end'], '%Y-%m-%d').date(),
                test_start_date=datetime.strptime(info['test_start'], '%Y-%m-%d').date() if info['test_start'] else None,
                test_end_date=datetime.strptime(info['test_end'], '%Y-%m-%d').date() if info['test_end'] else None
            )
            
            db.session.add(lstm_model_info)
            db.session.commit()
            
            return {
                'mensagem': 'Modelo treinado com sucesso',
                'symbol': symbol,
                'model_name': model_name,
                'model_path': model_path,
                'parametros': {
                    'sequence_length': sequence_length,
                    'epochs_executadas': len(history.history['loss']),
                    'epochs_solicitadas': epochs,
                    'batch_size': batch_size,
                    'units': units
                },
                'metricas': metrics,
                'dados': info,
                'historico_treinamento': {
                    'loss': [float(x) for x in history.history['loss'][-10:]],
                    'val_loss': [float(x) for x in history.history['val_loss'][-10:]],
                    'mae': [float(x) for x in history.history['mae'][-10:]],
                    'val_mae': [float(x) for x in history.history['val_mae'][-10:]]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo: {e}")
            db.session.rollback()
            return {'erro': f'Erro ao treinar modelo: {str(e)}'}
    
    def calcular_metricas(self, y_true, y_pred) -> dict:
        """
        Calcula métricas de avaliação do modelo
        
        Args:
            y_true: Valores reais
            y_pred: Valores previstos
        
        Returns:
            dict com métricas MAE, RMSE e MAPE
        """
        # MAE - Mean Absolute Error
        mae = np.mean(np.abs(y_true - y_pred))
        
        # RMSE - Root Mean Square Error
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        
        # MAPE - Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape)
        }
    
    def prever_proximos_dias(self, symbol: str, dias: int = 5, model_name: str = None) -> dict:
        """
        Faz previsão dos próximos N dias
        
        Args:
            symbol: Símbolo da ação
            dias: Número de dias para prever
            model_name: Nome do modelo (opcional, usa o mais recente se não especificado)
        
        Returns:
            dict com previsões
        """
        try:
            # Buscar modelo
            if model_name:
                model_info = LSTMModel.query.filter_by(model_name=model_name).first()
            else:
                model_info = LSTMModel.query.filter_by(symbol=symbol, is_active=True)\
                    .order_by(LSTMModel.created_at.desc()).first()
            
            if not model_info:
                return {'erro': f'Nenhum modelo encontrado para {symbol}'}
            
            # Carregar modelo e scaler
            model = load_model(model_info.model_path)
            scaler_path = model_info.model_path.replace('.h5', '_scaler.pkl')
            scaler = joblib.load(scaler_path)
            
            # Buscar dados históricos
            sequence_length = model_info.sequence_length
            dados = StockData.query.filter_by(symbol=symbol)\
                .order_by(StockData.date.desc())\
                .limit(sequence_length)\
                .all()
            
            if len(dados) < sequence_length:
                return {'erro': f'Dados históricos insuficientes para {symbol}'}
            
            # Preparar dados
            dados = list(reversed(dados))
            prices = np.array([d.close for d in dados]).reshape(-1, 1)
            scaled_prices = scaler.transform(prices)
            
            # Fazer previsões
            previsoes = []
            current_sequence = scaled_prices.copy()
            
            for i in range(dias):
                # Preparar input
                x_input = current_sequence[-sequence_length:].reshape(1, sequence_length, 1)
                
                # Prever próximo valor
                next_pred = model.predict(x_input, verbose=0)
                
                # Adicionar à sequência
                current_sequence = np.vstack([current_sequence, next_pred])
                
                # Desnormalizar
                next_price = scaler.inverse_transform(next_pred)[0][0]
                previsoes.append(float(next_price))
            
            # Gerar datas futuras
            ultima_data = dados[-1].date
            datas_futuras = []
            for i in range(1, dias + 1):
                proxima_data = ultima_data + timedelta(days=i)
                # Pular fins de semana
                while proxima_data.weekday() >= 5:
                    proxima_data += timedelta(days=1)
                datas_futuras.append(proxima_data.strftime('%Y-%m-%d'))
            
            # Último preço real
            ultimo_preco = float(dados[-1].close)
            
            return {
                'symbol': symbol,
                'model_name': model_info.model_name,
                'ultimo_preco_real': ultimo_preco,
                'ultima_data': ultima_data.strftime('%Y-%m-%d'),
                'previsoes': [
                    {
                        'data': datas_futuras[i],
                        'preco_previsto': round(previsoes[i], 2),
                        'variacao_percentual': round(((previsoes[i] - ultimo_preco) / ultimo_preco) * 100, 2)
                    }
                    for i in range(dias)
                ],
                'metricas_modelo': {
                    'mae': model_info.mae,
                    'rmse': model_info.rmse,
                    'mape': model_info.mape
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao fazer previsão: {e}")
            return {'erro': f'Erro ao fazer previsão: {str(e)}'}
    
    def listar_modelos(self, symbol: str = None) -> dict:
        """
        Lista modelos LSTM treinados
        
        Args:
            symbol: Símbolo da ação (opcional)
        
        Returns:
            dict com lista de modelos
        """
        try:
            if symbol:
                modelos = LSTMModel.query.filter_by(symbol=symbol)\
                    .order_by(LSTMModel.created_at.desc()).all()
            else:
                modelos = LSTMModel.query.order_by(LSTMModel.created_at.desc()).all()
            
            return {
                'total': len(modelos),
                'modelos': [m.to_dict() for m in modelos]
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return {'erro': f'Erro ao listar modelos: {str(e)}'}
    
    def obter_metricas_modelo(self, model_name: str) -> dict:
        """
        Obtém métricas detalhadas de um modelo
        
        Args:
            model_name: Nome do modelo
        
        Returns:
            dict com métricas do modelo
        """
        try:
            model_info = LSTMModel.query.filter_by(model_name=model_name).first()
            
            if not model_info:
                return {'erro': f'Modelo {model_name} não encontrado'}
            
            return model_info.to_dict()
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
            return {'erro': f'Erro ao obter métricas: {str(e)}'}
