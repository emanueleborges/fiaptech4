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
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import GridSearchCV
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
                
                # Calcula features principais (existentes na tabela)
                variacao = self._calcular_variacao(ativo.codigo, ativo.data)
                media_movel_7d = self._calcular_media_movel(ativo.codigo, ativo.data, dias=7)
                volatilidade = self._calcular_volatilidade(ativo.codigo, ativo.data, dias=7)
                
                # Features AVANÇADAS técnicas
                # 1. Score de liquidez (baseado em participação + volume)
                score_liquidez = (participacao * 100) + (min(qtde_teorica, 5.0) * 0.1)
                
                # 2. Score de momentum (variação recente)
                score_momentum = (variacao or 0) * 10 if variacao else 0
                
                # 3. Score de estabilidade (inverso da volatilidade)
                score_estabilidade = 1.0 / (1.0 + (volatilidade or 0.1))
                
                # 4. Score de tendência (média móvel vs participação atual)
                if media_movel_7d and participacao > 0:
                    score_tendencia = (participacao - media_movel_7d) / participacao * 100
                else:
                    score_tendencia = 0
                
                # 5. Score de tipo com peso maior para ON
                score_tipo = 1.5 if tipo_on else 0.7
                
                # 6. Score composto de qualidade
                score_qualidade = (score_liquidez * 0.3 + 
                                 score_estabilidade * 0.2 + 
                                 abs(score_tendencia) * 0.1 + 
                                 score_tipo * 0.1)
                
                # Target SOFISTICADO multi-período
                # Analisa performance em múltiplos horizontes
                
                # Performance D+1 (peso 40%)
                data_amanha = ativo.data + timedelta(days=1)
                ativo_amanha = IbovAtivo.query.filter_by(
                    codigo=ativo.codigo, data=data_amanha
                ).first()
                
                score_d1 = 0.0
                if ativo_amanha:
                    try:
                        part_amanha = float(ativo_amanha.participacao.replace(',', '.'))
                        score_d1 = (part_amanha - participacao) / participacao if participacao > 0 else 0
                    except:
                        score_d1 = 0.0
                
                # Performance D+3 (peso 30%)
                data_3dias = ativo.data + timedelta(days=3)
                ativo_3dias = IbovAtivo.query.filter_by(
                    codigo=ativo.codigo, data=data_3dias
                ).first()
                
                score_d3 = 0.0
                if ativo_3dias:
                    try:
                        part_3dias = float(ativo_3dias.participacao.replace(',', '.'))
                        score_d3 = (part_3dias - participacao) / participacao if participacao > 0 else 0
                    except:
                        score_d3 = 0.0
                
                # Score técnico (peso 30%)
                score_tecnico = (
                    score_momentum * 0.4 +
                    score_tendencia * 0.3 +
                    score_qualidade * 0.2 +
                    score_estabilidade * 0.1
                ) * 0.01  # Normaliza
                
                # Score final composto
                performance_score = (
                    score_d1 * 0.4 +
                    score_d3 * 0.3 +
                    score_tecnico * 0.3
                )
                
                # Ruído mínimo para evitar overfitting
                import random
                import time
                seed_unico = int(time.time() * 1000) + hash(ativo.codigo) % 1000
                random.seed(seed_unico)
                ruido = random.uniform(-0.02, 0.02)  # ±2% de ruído
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
                        media_movel_7d=media_movel_7d,
                        volatilidade=volatilidade,
                        recomendacao=performance_score,  # Score temporário
                        data_referencia=ativo.data
                    )
                    db.session.add(refinado)
                    refinados_salvos += 1
            
            db.session.commit()
            
            # PASSO 2: Converter scores em classificação com 3 CLASSES
            # COMPRAR (2), MANTER (1), VENDER (0)
            todos_registros = DadosRefinados.query.all()
            scores = [r.recomendacao for r in todos_registros]
            
            # Calcula thresholds para 3 classes (tercios)
            import statistics
            import numpy as np
            scores_sorted = sorted(scores)
            
            # Divide em terços (33% cada classe)
            tamanho = len(scores_sorted)
            threshold_baixo = scores_sorted[tamanho // 3] if tamanho > 3 else min(scores)
            threshold_alto = scores_sorted[2 * tamanho // 3] if tamanho > 3 else max(scores)
            
            print(f"DEBUG - Thresholds: Baixo={threshold_baixo:.4f}, Alto={threshold_alto:.4f}")
            
            total_comprar = 0
            total_manter = 0
            total_vender = 0
            
            for registro in todos_registros:
                if registro.recomendacao >= threshold_alto:
                    registro.recomendacao = 2  # COMPRAR (top 33%)
                    total_comprar += 1
                elif registro.recomendacao >= threshold_baixo:
                    registro.recomendacao = 1  # MANTER (middle 33%)
                    total_manter += 1
                else:
                    registro.recomendacao = 0  # VENDER (bottom 33%)
                    total_vender += 1
            
            db.session.commit()
            
            return {
                'mensagem': 'Dados refinados com sucesso! (3 classes: COMPRAR, MANTER, VENDER)',
                'total_processado': len(ativos),
                'total_salvos': refinados_salvos,
                'distribuicao': f'COMPRAR: {total_comprar}, MANTER: {total_manter}, VENDER: {total_vender}',
                'estrategia': 'Target baseado em performance FUTURA com 3 classes (terços)',
                'thresholds': f'Baixo: {threshold_baixo:.4f}, Alto: {threshold_alto:.4f}'
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
            
            # Verifica se tem dados suficientes de cada classe NO TREINO (3 classes)
            from collections import Counter
            distribuicao_treino = Counter(y_train)
            
            vender_treino = distribuicao_treino.get(0, 0)      # Classe 0 = VENDER
            manter_treino = distribuicao_treino.get(1, 0)      # Classe 1 = MANTER
            comprar_treino = distribuicao_treino.get(2, 0)     # Classe 2 = COMPRAR
            
            print(f"DEBUG - Distribuição treino: VENDER={vender_treino}, MANTER={manter_treino}, COMPRAR={comprar_treino}")
            
            # Precisa ter pelo menos 5% de cada classe (mais flexível para 3 classes)
            percentual_minimo = 0.05
            total_treino = len(y_train)
            
            if (vender_treino < total_treino * percentual_minimo or 
                manter_treino < total_treino * percentual_minimo or 
                comprar_treino < total_treino * percentual_minimo):
                return {
                    'erro': f'Dados desbalanceados. VENDER: {vender_treino}, MANTER: {manter_treino}, COMPRAR: {comprar_treino}. Refine os dados novamente.'
                }
            
            # Normalização AVANÇADA com RobustScaler (mais resistente a outliers)
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # ENSEMBLE AVANÇADO com múltiplos algoritmos otimizados
            random_state_dinamico = int(time.time()) % 10000
            
            # 1. RandomForest otimizado
            rf = RandomForestClassifier(
                n_estimators=200,  # Mais árvores
                max_depth=12,      # Mais profundidade
                min_samples_split=8,
                min_samples_leaf=3,
                max_features='sqrt',
                class_weight='balanced',
                bootstrap=True,
                random_state=random_state_dinamico,
                n_jobs=-1
            )
            
            # 2. Extra Trees (mais diversidade)
            from sklearn.ensemble import ExtraTreesClassifier
            et = ExtraTreesClassifier(
                n_estimators=150,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=4,
                max_features='sqrt',
                class_weight='balanced',
                bootstrap=False,
                random_state=random_state_dinamico,
                n_jobs=-1
            )
            
            # 3. Gradient Boosting otimizado
            gb = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.05,  # Menor para melhor convergência
                max_depth=8,
                min_samples_split=15,
                min_samples_leaf=6,
                subsample=0.8,  # Adiciona aleatoriedade
                random_state=random_state_dinamico
            )
            
            # Ensemble com pesos otimizados
            modelo = VotingClassifier(
                estimators=[
                    ('rf', rf),      # Peso implícito = 1
                    ('et', et),      # Peso implícito = 1  
                    ('gb', gb)       # Peso implícito = 1
                ],
                voting='soft',       # Usa probabilidades
                n_jobs=-1
            )
            
            # DEBUG: Verificar dados antes do treinamento
            print(f"🔍 DEBUG - Formato X_train: {X_train_scaled.shape}")
            print(f"🔍 DEBUG - Formato y_train: {y_train.shape}")
            print(f"🔍 DEBUG - Primeiros 5 valores de y_train: {y_train.iloc[:5].tolist()}")
            print(f"🔍 DEBUG - Valores únicos em y_train: {sorted(y_train.unique())}")
            
            # Treina o modelo
            print("🤖 Treinando modelo RandomForest otimizado...")
            modelo.fit(X_train_scaled, y_train)
            
            # Predições
            print("🔮 Fazendo predições no conjunto de teste...")
            y_pred = modelo.predict(X_test_scaled)
            
            # DEBUG: Verificar distribuição das predições
            from collections import Counter
            distribuicao_real = Counter(y_test)
            distribuicao_pred = Counter(y_pred)
            
            print(f"🔍 DEBUG - Distribuição real (teste): {dict(distribuicao_real)}")
            print(f"🔍 DEBUG - Distribuição predita: {dict(distribuicao_pred)}")
            print(f"🔍 DEBUG - Primeiros 10 valores reais: {y_test.iloc[:10].tolist()}")
            print(f"🔍 DEBUG - Primeiros 10 valores preditos: {y_pred[:10].tolist()}")
            
            # Converte para tipos Python nativos (evita erro de serialização JSON)
            distribuicao_real_dict = {int(k): int(v) for k, v in distribuicao_real.items()}
            distribuicao_pred_dict = {int(k): int(v) for k, v in distribuicao_pred.items()}
            
            # Métricas AVANÇADAS
            acuracia = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # Relatório detalhado por classe
            relatorio = classification_report(y_test, y_pred, output_dict=True, zero_division=0,
                                            target_names=['VENDER', 'MANTER', 'COMPRAR'])
            
            # Feature Importance (se disponível)
            feature_importance = {}
            try:
                if hasattr(modelo, 'feature_importances_'):
                    importances = modelo.feature_importances_
                elif hasattr(modelo, 'estimators_') and hasattr(modelo.estimators_[0], 'feature_importances_'):
                    # Para VotingClassifier, pega do RandomForest
                    importances = modelo.estimators_[0].feature_importances_
                else:
                    importances = [1/len(features)] * len(features)  # Uniform se não disponível
                
                feature_importance = dict(zip(features, [float(imp) for imp in importances]))
            except:
                feature_importance = dict(zip(features, [1/len(features)] * len(features)))
            
            # Análise de confiança das predições
            try:
                y_proba = modelo.predict_proba(X_test_scaled)
                confianca_media = float(np.mean(np.max(y_proba, axis=1)))
                confianca_std = float(np.std(np.max(y_proba, axis=1)))
            except:
                confianca_media = 0.5
                confianca_std = 0.0
            
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
                'mensagem': '🎯 Modelo treinado com sucesso!',
                'versao': versao,
                'algoritmo': 'Ensemble Multi-Algoritmo' if algoritmo == 'RandomForest' else algoritmo,
                'metricas_gerais': {
                    'acuracia': round(acuracia, 4),
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1, 4),
                    'confianca_media': round(confianca_media, 4),
                    'desvio_confianca': round(confianca_std, 4)
                },
                'metricas_por_classe': {
                    'VENDER': {
                        'precision': round(relatorio.get('VENDER', {}).get('precision', 0), 4),
                        'recall': round(relatorio.get('VENDER', {}).get('recall', 0), 4),
                        'f1': round(relatorio.get('VENDER', {}).get('f1-score', 0), 4)
                    },
                    'MANTER': {
                        'precision': round(relatorio.get('MANTER', {}).get('precision', 0), 4),
                        'recall': round(relatorio.get('MANTER', {}).get('recall', 0), 4),
                        'f1': round(relatorio.get('MANTER', {}).get('f1-score', 0), 4)
                    },
                    'COMPRAR': {
                        'precision': round(relatorio.get('COMPRAR', {}).get('precision', 0), 4),
                        'recall': round(relatorio.get('COMPRAR', {}).get('recall', 0), 4),
                        'f1': round(relatorio.get('COMPRAR', {}).get('f1-score', 0), 4)
                    }
                },
                'feature_importance': feature_importance,
                'distribuicoes': {
                    'teste_real': distribuicao_real_dict,
                    'teste_pred': distribuicao_pred_dict
                },
                'amostras': {
                    'treino': len(X_train),
                    'teste': len(X_test)
                },
                'debug': {
                    'distribuicao_treino': f'VENDER: {vender_treino}, MANTER: {manter_treino}, COMPRAR: {comprar_treino}',
                    'distribuicao_teste_real': distribuicao_real_dict,
                    'distribuicao_teste_pred': distribuicao_pred_dict,
                    'metricas_por_classe': {
                        'classe_0_vender': {
                            'precision': round(relatorio['0']['precision'], 4) if '0' in relatorio else 0,
                            'recall': round(relatorio['0']['recall'], 4) if '0' in relatorio else 0,
                            'f1': round(relatorio['0']['f1-score'], 4) if '0' in relatorio else 0
                        },
                        'classe_1_manter': {
                            'precision': round(relatorio['1']['precision'], 4) if '1' in relatorio else 0,
                            'recall': round(relatorio['1']['recall'], 4) if '1' in relatorio else 0,
                            'f1': round(relatorio['1']['f1-score'], 4) if '1' in relatorio else 0
                        },
                        'classe_2_comprar': {
                            'precision': round(relatorio['2']['precision'], 4) if '2' in relatorio else 0,
                            'recall': round(relatorio['2']['recall'], 4) if '2' in relatorio else 0,
                            'f1': round(relatorio['2']['f1-score'], 4) if '2' in relatorio else 0
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
            
            # Mapear predição para 3 classes
            if predicao == 2:
                recomendacao = 'COMPRAR'
            elif predicao == 1:
                recomendacao = 'MANTER'
            else:
                recomendacao = 'VENDER'
                
            confianca = max(probabilidades) * 100
            
            return {
                'codigo': codigo,
                'nome': dado.nome,
                'recomendacao': recomendacao,
                'confianca': round(confianca, 2),
                'probabilidades': {
                    'vender': round(probabilidades[0] * 100, 2) if len(probabilidades) > 0 else 0,
                    'manter': round(probabilidades[1] * 100, 2) if len(probabilidades) > 1 else 0,
                    'comprar': round(probabilidades[2] * 100, 2) if len(probabilidades) > 2 else 0
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

    def _calcular_rsi(self, codigo: str, data_atual, periodo=14) -> float:
        """Calcula Relative Strength Index (RSI)"""
        try:
            data_inicio = data_atual - timedelta(days=periodo + 5)
            ativos = IbovAtivo.query.filter(
                IbovAtivo.codigo == codigo,
                IbovAtivo.data >= data_inicio,
                IbovAtivo.data <= data_atual
            ).order_by(IbovAtivo.data).all()
            
            if len(ativos) >= periodo:
                precos = [float(a.participacao.replace(',', '.')) for a in ativos]
                
                # Calcula variações diárias
                deltas = [precos[i] - precos[i-1] for i in range(1, len(precos))]
                
                # Separa ganhos e perdas
                ganhos = [d if d > 0 else 0 for d in deltas]
                perdas = [-d if d < 0 else 0 for d in deltas]
                
                # Média dos últimos 'periodo' dias
                if len(ganhos) >= periodo and len(perdas) >= periodo:
                    avg_ganho = sum(ganhos[-periodo:]) / periodo
                    avg_perda = sum(perdas[-periodo:]) / periodo
                    
                    if avg_perda != 0:
                        rs = avg_ganho / avg_perda
                        rsi = 100 - (100 / (1 + rs))
                        return rsi
        except:
            pass
        return 50.0  # RSI neutro
    
    def _calcular_momentum(self, codigo: str, data_atual, periodo=5) -> float:
        """Calcula momentum (taxa de mudança)"""
        try:
            data_inicio = data_atual - timedelta(days=periodo + 2)
            ativos = IbovAtivo.query.filter(
                IbovAtivo.codigo == codigo,
                IbovAtivo.data >= data_inicio,
                IbovAtivo.data <= data_atual
            ).order_by(IbovAtivo.data).all()
            
            if len(ativos) >= periodo + 1:
                preco_atual = float(ativos[-1].participacao.replace(',', '.'))
                preco_anterior = float(ativos[-(periodo+1)].participacao.replace(',', '.'))
                
                if preco_anterior != 0:
                    momentum = ((preco_atual - preco_anterior) / preco_anterior) * 100
                    return momentum
        except:
            pass
        return 0.0
    
    def _calcular_ranking_participacao(self, ativo_atual, todos_ativos) -> int:
        """Calcula posição no ranking de participação"""
        try:
            participacoes = []
            for ativo in todos_ativos:
                if ativo.data == ativo_atual.data:
                    try:
                        part = float(ativo.participacao.replace(',', '.'))
                        participacoes.append((ativo.codigo, part))
                    except:
                        participacoes.append((ativo.codigo, 0.0))
            
            # Ordena por participação (maior para menor)
            participacoes.sort(key=lambda x: x[1], reverse=True)
            
            # Encontra posição do ativo atual
            for i, (codigo, _) in enumerate(participacoes):
                if codigo == ativo_atual.codigo:
                    return i + 1  # Posição 1-based
                    
        except:
            pass
        return 50  # Posição média
    
    def _calcular_ranking_volume(self, ativo_atual, todos_ativos) -> int:
        """Calcula posição no ranking de volume (quantidade teórica)"""
        try:
            volumes = []
            for ativo in todos_ativos:
                if ativo.data == ativo_atual.data:
                    try:
                        vol_str = ativo.theoricalQty.replace('.', '').replace(',', '.')
                        vol = float(vol_str)
                        volumes.append((ativo.codigo, vol))
                    except:
                        volumes.append((ativo.codigo, 0.0))
            
            # Ordena por volume (maior para menor)
            volumes.sort(key=lambda x: x[1], reverse=True)
            
            # Encontra posição do ativo atual
            for i, (codigo, _) in enumerate(volumes):
                if codigo == ativo_atual.codigo:
                    return i + 1
                    
        except:
            pass
        return 50  # Posição média
