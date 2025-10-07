"""
Interface Gradio COMPLETA - Todas as funcionalidades
IBOVESPA + Machine Learning (simulado)
"""
import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# URL da API Flask
API_BASE = "http://127.0.0.1:5000"


def carregar_dados_existentes():
    """Carrega dados existentes do banco"""
    try:
        response = requests.get(f"{API_BASE}/ibov/ativos")
        if response.status_code == 200:
            ativos = response.json()
            
            if not ativos:
                return None, "📊 Nenhum ativo encontrado no banco. Execute o scraping primeiro.", None
            
            # Converter para DataFrame
            df = pd.DataFrame([{
                'Código': ativo['codigo'],
                'Nome': ativo['nome'][:40],
                'Tipo': ativo['tipo'],
                'Participação (%)': str(ativo['participacao']),
                'Data': ativo['data']
            } for ativo in ativos])
            
            # Criar gráfico de participação
            fig = px.bar(
                df.head(15), 
                x='Código', 
                y='Participação (%)', 
                title='Top 15 Ativos por Participação no IBOVESPA',
                color='Participação (%)',
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                xaxis_title="Código do Ativo",
                yaxis_title="Participação (%)",
                showlegend=False
            )
            
            mensagem = f"📊 **{len(ativos)} ativos** encontrados no banco"
            return df, mensagem, fig
        else:
            return None, "❌ Erro ao buscar dados do banco", None
    except Exception as e:
        return None, f"❌ Erro: {str(e)}", None


def fazer_scraping():
    """Chama a API Flask para fazer scraping"""
    try:
        response = requests.post(f"{API_BASE}/ibov/scrap")
        
        if response.status_code in [200, 201]:
            # Após scraping, carregar dados atualizados
            return carregar_dados_existentes()
        else:
            return None, f"❌ Erro no scraping: {response.text}", None
    
    except requests.exceptions.ConnectionError:
        return None, "❌ **ERRO**: API Flask não está rodando! Execute `python app.py` primeiro", None
    except Exception as e:
        return None, f"❌ Erro inesperado: {str(e)}", None


def fazer_scraping_historico():
    """Chama a API Flask para fazer scraping de 6 meses"""
    try:
        response = requests.post(f"{API_BASE}/ibov/scrap-historico", json={}, headers={'Content-Type': 'application/json'})
        
        if response.status_code in [200, 201]:
            data = response.json()
            mensagem = f"✅ {data.get('mensagem')}\n📅 Dias: {data.get('dias_coletados')}\n📊 Registros: {data.get('total_registros')}\n📈 Média/dia: {data.get('media_por_dia')}\n❌ Erros: {data.get('erros')}"
            # Carregar dados atualizados
            df, _, fig = carregar_dados_existentes()
            return df, mensagem, fig
        else:
            return None, f"❌ Erro no scraping histórico: {response.text}", None
    
    except requests.exceptions.ConnectionError:
        return None, "❌ **ERRO**: API Flask não está rodando! Execute `python app.py` primeiro", None
    except Exception as e:
        return None, f"❌ Erro inesperado: {str(e)}", None


def refinar_dados():
    """Chama a API para refinar dados para ML"""
    try:
        response = requests.post(f"{API_BASE}/ml/refinar", json={}, headers={'Content-Type': 'application/json'})
        if response.status_code in [200, 201]:
            data = response.json()
            mensagem = f"✅ {data.get('mensagem', data.get('message', 'Sucesso!'))}\n📊 Total processado: {data.get('total_processado', 0)}\n💾 Total salvos: {data.get('total_salvos', 0)}"
            return mensagem
        else:
            return f"❌ Erro ao refinar dados: {response.text}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


def listar_dados_refinados():
    """Lista dados refinados salvos"""
    try:
        response = requests.get(f"{API_BASE}/ml/dados-refinados")
        if response.status_code == 200:
            data = response.json()
            
            # Converter para DataFrame
            df = pd.DataFrame(data['dados_refinados'])
            
            mensagem = f"📊 **{data['total']} registros** refinados encontrados"
            return df, mensagem
        else:
            return None, f"❌ Erro ao buscar dados refinados: {response.text}"
    except Exception as e:
        return None, f"❌ Erro: {str(e)}"


def treinar_modelo():
    """Chama a API para treinar modelo ML"""
    try:
        response = requests.post(f"{API_BASE}/ml/treinar", json={}, headers={'Content-Type': 'application/json'})
        if response.status_code in [200, 201]:
            data = response.json()
            metricas = data.get('metricas', {})
            mensagem = f"✅ {data.get('mensagem', 'Modelo treinado!')}\n📊 Acurácia: {float(metricas.get('acuracia', data.get('acuracia', 0)))*100:.1f}%\n🎯 Precision: {float(metricas.get('precision', data.get('precision', 0)))*100:.1f}%\n🔍 Recall: {float(metricas.get('recall', data.get('recall', 0)))*100:.1f}%\n⚖️ F1-Score: {float(metricas.get('f1_score', data.get('f1_score', 0)))*100:.1f}%"
            return mensagem
        else:
            return f"❌ Erro ao treinar modelo: {response.text}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


def fazer_predicoes():
    """Chama a API para fazer predições"""
    try:
        print("DEBUG - Iniciando predições...")
        
        # TESTE 1: Verificar se há modelo treinado
        response_metricas = requests.get(f"{API_BASE}/ml/metricas")
        if response_metricas.status_code != 200:
            return None, "❌ Erro: Nenhum modelo treinado. Treine um modelo primeiro!", None
        
        # TESTE 2: Buscar alguns códigos para testar
        response_ativos = requests.get(f"{API_BASE}/ibov/ativos")
        if response_ativos.status_code != 200:
            return None, "❌ Erro ao buscar ativos para predição", None
        
        ativos = response_ativos.json()[:5]  # Apenas 5 para teste
        if not ativos:
            return None, "❌ Nenhum ativo encontrado no banco", None
            
        codigos = [ativo['codigo'] for ativo in ativos]
        print(f"DEBUG - Códigos selecionados: {codigos}")
        
        # TESTE 3: Testar primeiro com um código único
        codigo_teste = codigos[0]
        print(f"DEBUG - Testando código único: {codigo_teste}")
        
        response_unico = requests.post(f"{API_BASE}/ml/prever", 
                                     json={"codigo": codigo_teste},
                                     headers={'Content-Type': 'application/json'})
        
        print(f"DEBUG - Resposta código único: Status {response_unico.status_code}")
        print(f"DEBUG - Conteúdo: {response_unico.text}")
        
        if response_unico.status_code != 200:
            return None, f"❌ Erro na predição única: {response_unico.text}", None
        
        # TESTE 4: Se código único funciona, testar múltiplos
        payload = {"codigos": codigos}
        print(f"DEBUG - Testando múltiplos códigos: {payload}")
        
        response = requests.post(f"{API_BASE}/ml/prever", 
                               json=payload,
                               headers={'Content-Type': 'application/json'})
        
        print(f"DEBUG - Status múltiplos: {response.status_code}")
        print(f"DEBUG - Resposta múltiplos: {response.text}")
        
        if response.status_code != 200:
            return None, f"❌ Erro em múltiplos códigos: {response.text}", None
        
        # TESTE 5: Processar dados de forma super simples
        data = response.json()
        print(f"DEBUG - Tipo de data: {type(data)}")
        print(f"DEBUG - Keys em data: {list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
        
        if 'predicoes' not in data:
            return None, f"❌ Chave 'predicoes' não encontrada. Keys disponíveis: {list(data.keys())}", None
        
        predicoes = data['predicoes']
        print(f"DEBUG - Número de predições: {len(predicoes)}")
        print(f"DEBUG - Primeira predição: {predicoes[0] if predicoes else 'Lista vazia'}")
        
        # TESTE 6: Criar DataFrame super simples - compatível com Gradio
        dados_simples = []
        for i, pred in enumerate(predicoes):
            print(f"DEBUG - Processando predição {i}: {pred}")
            print(f"DEBUG - Chaves disponíveis: {list(pred.keys()) if isinstance(pred, dict) else 'Não é dict'}")
            
            # Garantir que todos os valores são strings simples para o Gradio
            codigo = str(pred.get('codigo', 'ERRO'))
            predicao = str(pred.get('predicao', pred.get('recomendacao', 'ERRO')))
            confianca = str(pred.get('confianca', 0))
            
            dados_simples.append({
                'Codigo': codigo,
                'Recomendacao': predicao,  # Mudei o nome da coluna
                'Confianca': confianca
            })
        
        print(f"DEBUG - Dados simples: {dados_simples}")
        
        # TESTE 6: Retornar dados como string simples para debug
        if dados_simples:
            try:
                # Primeiro tentar DataFrame normal
                df_simples = pd.DataFrame(dados_simples)
                print(f"DEBUG - DataFrame criado com sucesso: {df_simples.head()}")
                
                # Garantir que todas as colunas são string
                for col in df_simples.columns:
                    df_simples[col] = df_simples[col].astype(str)
                
                # Se chegou até aqui, DataFrame está OK
                return df_simples, f"✅ {len(predicoes)} predições realizadas", None
                
            except Exception as df_error:
                print(f"DEBUG - Erro ao criar DataFrame: {df_error}")
                
                # Se DataFrame falhou, retornar como texto simples
                texto_resultado = "Predições realizadas:\n\n"
                for i, item in enumerate(dados_simples):
                    texto_resultado += f"{i+1}. {item['Codigo']}: {item['Recomendacao']} (Confiança: {item['Confianca']}%)\n"
                
                return None, texto_resultado, None
        else:
            return None, "❌ Nenhuma predição válida encontrada", None
        
    except Exception as e:
        error_msg = f"❌ Erro: {str(e)}"
        print(f"DEBUG - Exceção: {str(e)}")
        print(f"DEBUG - Tipo do erro: {type(e)}")
        return None, error_msg, None


# Interface Gradio COMPLETA
with gr.Blocks(title="IBOVESPA + ML - Sistema Completo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📊 Sistema IBOVESPA + Machine Learning")
    gr.Markdown("### Sistema de ML - FIAP DESAFIO 3")
    
    with gr.Tab("🔄 Scraping de Dados"):
        gr.Markdown("### Coletar dados do site da B3")
        
        with gr.Row():
            btn_scrap = gr.Button("🚀 Fazer Scraping (Hoje)", variant="secondary", size="lg")
            btn_scrap_hist = gr.Button("📅 Coletar 6 MESES (RECOMENDADO)", variant="primary", size="lg")
        
        status_scrap = gr.Textbox(label="Status", interactive=False)
        
        tabela_scrap = gr.Dataframe(
            label="📋 Dados Coletados",
            interactive=False,
            wrap=True
        )
        
        grafico_scrap = gr.Plot(label="📈 Gráfico de Participação")
        
        btn_scrap.click(
            fn=fazer_scraping,
            outputs=[tabela_scrap, status_scrap, grafico_scrap]
        )
        
        btn_scrap_hist.click(
            fn=fazer_scraping_historico,
            outputs=[tabela_scrap, status_scrap, grafico_scrap]
        )
    
    # Auto-carregar dados ao iniciar a interface
    demo.load(
        fn=carregar_dados_existentes,
        outputs=[tabela_scrap, status_scrap, grafico_scrap]
    )
    
    with gr.Tab(" Refinar Dados"):
        gr.Markdown("### Preparar dados para Machine Learning")
        
        btn_refinar = gr.Button("🔧 Refinar Dados para ML", variant="primary")
        status_refinar = gr.Textbox(label="Status", interactive=False)
        
        btn_refinar.click(
            fn=refinar_dados,
            outputs=[status_refinar]
        )
        
        gr.Markdown("---")
        
        btn_listar_refinados = gr.Button("📊 Ver Dados Refinados", variant="secondary")
        status_refinados = gr.Textbox(label="Status", interactive=False)
        
        tabela_refinados = gr.Dataframe(
            label="📊 Dados Refinados",
            interactive=False
        )
        
        btn_listar_refinados.click(
            fn=listar_dados_refinados,
            outputs=[tabela_refinados, status_refinados]
        )
    
    with gr.Tab("🤖 Treinar Modelo"):
        gr.Markdown("### Treinar modelo de Machine Learning")
        
        btn_treinar = gr.Button("🤖 Treinar Modelo ML", variant="primary", size="lg")
        status_treino = gr.Textbox(label="Status do Treinamento", interactive=False)
        
        btn_treinar.click(
            fn=treinar_modelo,
            outputs=[status_treino]
        )
    
    with gr.Tab("🎯 Fazer Predições"):
        gr.Markdown("### Fazer predições com o modelo treinado")
        
        btn_prever = gr.Button("🎯 Fazer Predições", variant="primary", size="lg")
        status_pred = gr.Textbox(label="Resultados das Predições", interactive=False)
        
        tabela_pred = gr.Dataframe(
            label="🎯 Predições do Modelo",
            interactive=False
        )
        
        grafico_pred = gr.Plot(label="📊 Distribuição das Predições")
        
        btn_prever.click(
            fn=fazer_predicoes,
            outputs=[tabela_pred, status_pred, grafico_pred]
        )

if __name__ == "__main__":
    print("🚀 Iniciando Interface Gradio COMPLETA...")
    print("🔗 Conectando com API Flask em http://127.0.0.1:5000")
    print("📊 Interface disponível em: http://127.0.0.1:7860")
    print("")
    print("⚠️  IMPORTANTE: Execute 'python app.py' primeiro!")
    
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7860,
        share=False,
        debug=False
    )