"""
Serviço de Machine Learning
Responsável por refinar dados, treinar modelos e fazer predições
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import logging

from app.models.ibov_model import IbovAtivo
from app.models.dados_refinados_model import DadosRefinados
from app.models.modelo_treinado_model import ModeloTreinado
from app.utils.extensions import db

logger = logging.getLogger(__name__)


class MLService:
    """Serviço de Machine Learning para predição de ações"""
    
    def __init__(self):
        self.modelos_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'modelos')
        os.makedirs(self.modelos_dir, exist_ok=True)
    
    def refinar_dados(self) -> dict:
        """
        ENDPOINT 1: Refinar dados brutos para ML
        
        Pega dados da tabela ibov_ativos e cria features para ML
        Salva na tabela dados_refinados
        """
        try:
            # Busca todos os ativos
            ativos = IbovAtivo.query.all()
            
            if not ativos:
                return {'erro': 'Nenhum dado encontrado na tabela ibov_ativos'}
            
            refinados_salvos = 0
            
            for ativo in ativos:
                # Converte participacao para float
                try:
                    participacao = float(ativo.participacao.replace(',', '.')) if ativo.participacao else 0.0
                except:
                    participacao = 0.0
                
                # Converte quantidade teórica
                try:
                    qtde_str = ativo.theoricalQty.replace('.', '').replace(',', '.')
                    qtde_teorica = float(qtde_str) / 1_000_000  # Normaliza para milhões
                except:
                    qtde_teorica = 0.0
                
                # Classifica tipo
                tipo_on = 1 if 'ON' in ativo.tipo.upper() else 0
                tipo_pn = 1 if 'PN' in ativo.tipo.upper() else 0
                
                # Calcula variação (compara com dia anterior)
                variacao = self._calcular_variacao(ativo.codigo, ativo.data)
                
                # Calcula média móvel e volatilidade
                media_movel = self._calcular_media_movel(ativo.codigo, ativo.data, dias=7)
                volatilidade = self._calcular_volatilidade(ativo.codigo, ativo.data, dias=7)
                
                # Define recomendação (label)
                # Regra simples: se participação > 1% e variação > 0 = COMPRAR (1), senão VENDER (0)
                recomendacao = 1 if (participacao > 1.0 and (variacao or 0) > 0) else 0
                
                # Verifica se já existe
                existe = DadosRefinados.query.filter_by(
                    codigo=ativo.codigo,
                    data_referencia=ativo.data
                ).first()
                
                if not existe:
                    refinado = DadosRefinados(
                        codigo=ativo.codigo,
                        nome=ativo.nome,
                        participacao_pct=participacao,
                        qtde_teorica=qtde_teorica,
                        tipo_on=tipo_on,
                        tipo_pn=tipo_pn,
                        variacao_percentual=variacao,
                        media_movel_7d=media_movel,
                        volatilidade=volatilidade,
                        recomendacao=recomendacao,
                        data_referencia=ativo.data
                    )
                    db.session.add(refinado)
                    refinados_salvos += 1
            
            db.session.commit()
            
            return {
                'mensagem': 'Dados refinados com sucesso!',
                'total_processado': len(ativos),
                'total_salvos': refinados_salvos
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao refinar dados: {e}")
            return {'erro': str(e)}
    
    def treinar_modelo(self, algoritmo='RandomForest') -> dict:
        """
        ENDPOINT 2: Treinar modelo de ML
        
        Treina modelo Random Forest com dados refinados
        Salva o modelo e registra métricas
        """
        try:
            # Busca dados refinados
            dados = DadosRefinados.query.all()
            
            if len(dados) < 10:
                return {'erro': 'Poucos dados para treinar. Mínimo 10 amostras.'}
            
            # Prepara DataFrame
            df = pd.DataFrame([d.to_dict() for d in dados])
            
            # Features (X) e Target (y)
            features = ['participacao_pct', 'qtde_teorica', 'tipo_on', 'tipo_pn']
            X = df[features].fillna(0)
            y = df['recomendacao'].fillna(0)
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Normalização
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Treina modelo
            if algoritmo == 'RandomForest':
                modelo = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
            else:
                return {'erro': f'Algoritmo {algoritmo} não suportado'}
            
            modelo.fit(X_train_scaled, y_train)
            
            # Predições
            y_pred = modelo.predict(X_test_scaled)
            
            # Métricas
            acuracia = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            # Salva modelo
            versao = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f'modelo_ibov_{versao}.pkl'
            caminho_modelo = os.path.join(self.modelos_dir, nome_arquivo)
            
            joblib.dump({
                'modelo': modelo,
                'scaler': scaler,
                'features': features
            }, caminho_modelo)
            
            # Registra no banco
            modelo_db = ModeloTreinado(
                nome='Modelo IBOV',
                versao=versao,
                algoritmo=algoritmo,
                acuracia=float(acuracia),
                precision=float(precision),
                recall=float(recall),
                f1_score=float(f1),
                total_amostras_treino=len(X_train),
                total_amostras_teste=len(X_test),
                features_utilizadas=json.dumps(features),
                caminho_modelo=caminho_modelo,
                ativo=True
            )
            
            # Desativa modelos antigos
            ModeloTreinado.query.update({ModeloTreinado.ativo: False})
            
            db.session.add(modelo_db)
            db.session.commit()
            
            return {
                'mensagem': 'Modelo treinado com sucesso!',
                'versao': versao,
                'metricas': {
                    'acuracia': round(acuracia, 4),
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1, 4)
                },
                'amostras': {
                    'treino': len(X_train),
                    'teste': len(X_test)
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao treinar modelo: {e}")
            return {'erro': str(e)}
    
    def prever(self, codigo: str) -> dict:
        """
        ENDPOINT 3: Fazer predição
        
        Usa modelo treinado para prever se deve COMPRAR ou VENDER
        """
        try:
            # Busca modelo ativo
            modelo_db = ModeloTreinado.query.filter_by(ativo=True).first()
            
            if not modelo_db:
                return {'erro': 'Nenhum modelo treinado disponível'}
            
            # Carrega modelo
            modelo_data = joblib.load(modelo_db.caminho_modelo)
            modelo = modelo_data['modelo']
            scaler = modelo_data['scaler']
            features = modelo_data['features']
            
            # Busca dados refinados mais recentes da ação
            dado = DadosRefinados.query.filter_by(codigo=codigo).order_by(
                DadosRefinados.data_referencia.desc()
            ).first()
            
            if not dado:
                return {'erro': f'Dados não encontrados para {codigo}'}
            
            # Prepara features
            X = np.array([[
                dado.participacao_pct,
                dado.qtde_teorica,
                dado.tipo_on,
                dado.tipo_pn
            ]])
            
            X_scaled = scaler.transform(X)
            
            # Predição
            predicao = modelo.predict(X_scaled)[0]
            probabilidades = modelo.predict_proba(X_scaled)[0]
            
            recomendacao = 'COMPRAR' if predicao == 1 else 'VENDER'
            confianca = max(probabilidades) * 100
            
            return {
                'codigo': codigo,
                'nome': dado.nome,
                'recomendacao': recomendacao,
                'confianca': round(confianca, 2),
                'probabilidades': {
                    'vender': round(probabilidades[0] * 100, 2),
                    'comprar': round(probabilidades[1] * 100, 2)
                },
                'dados_utilizados': {
                    'participacao': dado.participacao_pct,
                    'qtde_teorica': dado.qtde_teorica,
                    'tipo': 'ON' if dado.tipo_on else 'PN'
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao fazer predição: {e}")
            return {'erro': str(e)}
    
    def obter_metricas(self) -> dict:
        """
        ENDPOINT 4: Obter métricas do modelo
        
        Retorna informações sobre o modelo ativo e histórico
        """
        try:
            # Modelo ativo
            modelo_ativo = ModeloTreinado.query.filter_by(ativo=True).first()
            
            if not modelo_ativo:
                return {'erro': 'Nenhum modelo treinado disponível'}
            
            # Histórico de modelos
            historico = ModeloTreinado.query.order_by(
                ModeloTreinado.data_treinamento.desc()
            ).limit(10).all()
            
            # Estatísticas dos dados
            total_dados = DadosRefinados.query.count()
            total_comprar = DadosRefinados.query.filter_by(recomendacao=1).count()
            total_vender = DadosRefinados.query.filter_by(recomendacao=0).count()
            
            return {
                'modelo_ativo': modelo_ativo.to_dict(),
                'historico': [m.to_dict() for m in historico],
                'estatisticas_dados': {
                    'total': total_dados,
                    'comprar': total_comprar,
                    'vender': total_vender,
                    'percentual_comprar': round((total_comprar / total_dados * 100) if total_dados > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
            return {'erro': str(e)}
    
    # ====== Métodos auxiliares ======
    
    def _calcular_variacao(self, codigo: str, data_atual) -> float:
        """Calcula variação percentual em relação ao dia anterior"""
        try:
            dia_anterior = data_atual - timedelta(days=1)
            ativo_anterior = IbovAtivo.query.filter_by(
                codigo=codigo, data=dia_anterior
            ).first()
            
            if ativo_anterior:
                part_atual = float(IbovAtivo.query.filter_by(
                    codigo=codigo, data=data_atual
                ).first().participacao.replace(',', '.'))
                
                part_anterior = float(ativo_anterior.participacao.replace(',', '.'))
                
                return ((part_atual - part_anterior) / part_anterior) * 100
        except:
            pass
        return None
    
    def _calcular_media_movel(self, codigo: str, data_atual, dias=7) -> float:
        """Calcula média móvel de X dias"""
        try:
            data_inicio = data_atual - timedelta(days=dias)
            ativos = IbovAtivo.query.filter(
                IbovAtivo.codigo == codigo,
                IbovAtivo.data >= data_inicio,
                IbovAtivo.data <= data_atual
            ).all()
            
            if ativos:
                participacoes = [float(a.participacao.replace(',', '.')) for a in ativos]
                return sum(participacoes) / len(participacoes)
        except:
            pass
        return None
    
    def _calcular_volatilidade(self, codigo: str, data_atual, dias=7) -> float:
        """Calcula volatilidade (desvio padrão)"""
        try:
            data_inicio = data_atual - timedelta(days=dias)
            ativos = IbovAtivo.query.filter(
                IbovAtivo.codigo == codigo,
                IbovAtivo.data >= data_inicio,
                IbovAtivo.data <= data_atual
            ).all()
            
            if len(ativos) > 1:
                participacoes = [float(a.participacao.replace(',', '.')) for a in ativos]
                return float(np.std(participacoes))
        except:
            pass
        return None
