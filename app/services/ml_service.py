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
            # LIMPAR DADOS ANTIGOS PRIMEIRO!
            DadosRefinados.query.delete()
            db.session.commit()
            
            # Busca todos os ativos
            ativos = IbovAtivo.query.all()
            
            if not ativos:
                return {'erro': 'Nenhum dado encontrado na tabela ibov_ativos'}
            
            # CRIAR TABELA SE NÃO EXISTIR
            db.create_all()
            
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
                
                # Define recomendação (label) - PERFORMANCE FUTURA!
                # Target: Performance no DIA SEGUINTE (evita data leakage)
                # Usa PARTICIPAÇÃO do dia seguinte como proxy de sucesso
                
                # Busca participação do DIA SEGUINTE para este ativo
                data_amanha = ativo.data + timedelta(days=1)
                ativo_amanha = IbovAtivo.query.filter_by(
                    codigo=ativo.codigo,
                    data=data_amanha
                ).first()
                
                if ativo_amanha:
                    try:
                        participacao_amanha = float(ativo_amanha.participacao.replace(',', '.'))
                        # Score = diferença de participação (amanhã - hoje)
                        performance_score = participacao_amanha - participacao
                    except:
                        performance_score = 0.0
                else:
                    # Se não tem dados do dia seguinte, usa score neutro
                    performance_score = 0.0
                
                # Adiciona RUÍDO para quebrar correlações perfeitas
                import random
                import time
                # Usa timestamp atual + código do ativo para seed único a cada execução
                seed_unico = int(time.time() * 1000) + hash(ativo.codigo) % 1000
                random.seed(seed_unico)
                ruido = random.uniform(-0.2, 0.2)  # ±20% de ruído (aumentado)
                performance_score += ruido
                
                # Adiciona o score temporário (será convertido depois)
                recomendacao = performance_score
                
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
            
            # PASSO 2: Converter scores em classificação REALÍSTICA
            # Não força 50/50, mas usa threshold natural baseado na mediana
            todos_registros = DadosRefinados.query.all()
            scores = [r.recomendacao for r in todos_registros]
            
            # Calcula threshold dinâmico (mediana + pequeno ajuste VARIÁVEL)
            import statistics
            import time
            mediana = statistics.median(scores)
            desvio = statistics.stdev(scores) if len(scores) > 1 else 0.1
            
            # Threshold com aleatoriedade (varia entre execuções)
            ajuste_aleatorio = (time.time() % 1) - 0.5  # Entre -0.5 e +0.5
            threshold = mediana + (desvio * 0.2) + (ajuste_aleatorio * desvio * 0.1)
            
            total_comprar = 0
            total_vender = 0
            
            for registro in todos_registros:
                if registro.recomendacao > threshold:
                    registro.recomendacao = 1  # COMPRAR
                    total_comprar += 1
                else:
                    registro.recomendacao = 0  # VENDER
                    total_vender += 1
            
            db.session.commit()
            
            return {
                'mensagem': 'Dados refinados com sucesso! (Performance futura + ruído)',
                'total_processado': len(ativos),
                'total_salvos': refinados_salvos,
                'distribuicao': f'COMPRAR: {total_comprar}, VENDER: {total_vender}',
                'estrategia': 'Target baseado em performance FUTURA com ruído para evitar overfitting',
                'threshold': f'Threshold dinâmico: {threshold:.4f}'
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
            import time  # Para aleatoriedade real
            # CRIAR TABELA SE NÃO EXISTIR
            db.create_all()
            
            # Busca dados refinados
            dados = DadosRefinados.query.all()
            
            if len(dados) < 10:
                return {'erro': 'Poucos dados para treinar. Mínimo 10 amostras.'}
            
            # Prepara DataFrame
            df = pd.DataFrame([d.to_dict() for d in dados])
            
            # Ordena por data para separação temporal
            df = df.sort_values('data_referencia')
            
            # Features (X) e Target (y)
            features = ['participacao_pct', 'qtde_teorica', 'tipo_on', 'tipo_pn', 
                       'variacao_percentual', 'media_movel_7d', 'volatilidade']
            X = df[features].fillna(0)
            y = df['recomendacao'].fillna(0)
            
            # SEPARAÇÃO TEMPORAL (não aleatória!)
            # 80% primeiros dados = treino, 20% últimos = teste
            split_index = int(len(X) * 0.8)
            X_train = X.iloc[:split_index]
            X_test = X.iloc[split_index:]
            y_train = y.iloc[:split_index]
            y_test = y.iloc[split_index:]
            
            # Verifica se tem dados suficientes de cada classe NO TREINO
            comprar_treino = int(y_train.sum())
            vender_treino = len(y_train) - comprar_treino
            
            # Precisa ter pelo menos 10% de cada classe
            percentual_minimo = 0.10
            if comprar_treino < len(y_train) * percentual_minimo or vender_treino < len(y_train) * percentual_minimo:
                return {
                    'erro': f'Dados muito desbalanceados. COMPRAR: {comprar_treino}, VENDER: {vender_treino}. Refine os dados novamente.'
                }
            
            # Normalização
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Treina modelo com REGULARIZAÇÃO para evitar overfitting
            if algoritmo == 'RandomForest':
                # Usa random_state baseado no timestamp atual para variação
                random_state_dinamico = int(time.time()) % 10000
                modelo = RandomForestClassifier(
                    n_estimators=50,        # Reduzido para evitar overfitting
                    max_depth=5,           # Mais limitado
                    min_samples_split=10,  # Evita divisões muito específicas
                    min_samples_leaf=5,    # Folhas maiores
                    max_features='sqrt',   # Menos features por árvore
                    random_state=random_state_dinamico  # Aleatoriedade real
                )
            else:
                return {'erro': f'Algoritmo {algoritmo} não suportado'}
            
            modelo.fit(X_train_scaled, y_train)
            
            # Predições
            y_pred = modelo.predict(X_test_scaled)
            
            # DEBUG: Verificar distribuição das predições
            from collections import Counter
            distribuicao_real = Counter(y_test)
            distribuicao_pred = Counter(y_pred)
            
            # Converte para tipos Python nativos (evita erro de serialização JSON)
            distribuicao_real_dict = {int(k): int(v) for k, v in distribuicao_real.items()}
            distribuicao_pred_dict = {int(k): int(v) for k, v in distribuicao_pred.items()}
            
            # Métricas
            acuracia = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # Calcula métricas para cada classe separadamente
            from sklearn.metrics import classification_report
            relatorio = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            
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
                },
                'debug': {
                    'distribuicao_treino': f'COMPRAR: {comprar_treino}, VENDER: {vender_treino}',
                    'distribuicao_teste_real': distribuicao_real_dict,
                    'distribuicao_teste_pred': distribuicao_pred_dict,
                    'metricas_por_classe': {
                        'classe_0_vender': {
                            'precision': round(relatorio['0']['precision'], 4) if '0' in relatorio else 0,
                            'recall': round(relatorio['0']['recall'], 4) if '0' in relatorio else 0,
                            'f1': round(relatorio['0']['f1-score'], 4) if '0' in relatorio else 0
                        },
                        'classe_1_comprar': {
                            'precision': round(relatorio['1']['precision'], 4) if '1' in relatorio else 0,
                            'recall': round(relatorio['1']['recall'], 4) if '1' in relatorio else 0,
                            'f1': round(relatorio['1']['f1-score'], 4) if '1' in relatorio else 0
                        }
                    }
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
            
            # Carrega modelo - com tratamento para incompatibilidade do numpy
            try:
                modelo_data = joblib.load(modelo_db.caminho_modelo)
                modelo = modelo_data['modelo']
                scaler = modelo_data['scaler']
                features = modelo_data['features']
            except Exception as load_error:
                if 'numpy._core' in str(load_error):
                    return {'erro': 'Modelo incompatível com versão atual do numpy. Treine um novo modelo.'}
                else:
                    return {'erro': f'Erro ao carregar modelo: {str(load_error)}'}
            
            # Busca dados refinados mais recentes da ação
            dado = DadosRefinados.query.filter_by(codigo=codigo).order_by(
                DadosRefinados.data_referencia.desc()
            ).first()
            
            if not dado:
                return {'erro': f'Dados não encontrados para {codigo}'}
            
            # Prepara features - TODAS as 7 features como no treinamento
            X = np.array([[
                dado.participacao_pct or 0,
                dado.qtde_teorica or 0,
                dado.tipo_on or 0,
                dado.tipo_pn or 0,
                dado.variacao_percentual or 0,
                dado.media_movel_7d or 0,
                dado.volatilidade or 0
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
                    'tipo': 'ON' if dado.tipo_on else 'PN',
                    'variacao_percentual': dado.variacao_percentual,
                    'media_movel_7d': dado.media_movel_7d,
                    'volatilidade': dado.volatilidade
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
