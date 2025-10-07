
import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:5000"


def carregar_dados_existentes():
    try:
        response = requests.get(f"{API_BASE}/ibov/ativos")
        if response.status_code == 200:
            ativos = response.json()
            
            if not ativos:
                return None, "📊 Nenhum ativo encontrado no banco. Execute o scraping primeiro.", None
            
            df = pd.DataFrame([{
                'Código': ativo['codigo'],
                'Nome': ativo['nome'][:40],
                'Tipo': ativo['tipo'],
                'Participação (%)': str(ativo['participacao']),
                'Data': ativo['data']
            } for ativo in ativos])
            
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
    try:
        response = requests.post(f"{API_BASE}/ibov/scrap")
        
        if response.status_code in [200, 201]:
            return carregar_dados_existentes()
        else:
            return None, f"❌ Erro no scraping: {response.text}", None
    
    except requests.exceptions.ConnectionError:
        return None, "❌ **ERRO**: API Flask não está rodando! Execute `python app.py` primeiro", None
    except Exception as e:
        return None, f"❌ Erro inesperado: {str(e)}", None


def fazer_scraping_historico():
    try:
        response = requests.post(f"{API_BASE}/ibov/scrap-historico", json={}, headers={'Content-Type': 'application/json'})
        
        if response.status_code in [200, 201]:
            data = response.json()
            mensagem = f"✅ {data.get('mensagem')}\n📅 Dias: {data.get('dias_coletados')}\n📊 Registros: {data.get('total_registros')}\n📈 Média/dia: {data.get('media_por_dia')}\n❌ Erros: {data.get('erros')}"
            df, _, fig = carregar_dados_existentes()
            return df, mensagem, fig
        else:
            return None, f"❌ Erro no scraping histórico: {response.text}", None
    
    except requests.exceptions.ConnectionError:
        return None, "❌ **ERRO**: API Flask não está rodando! Execute `python app.py` primeiro", None
    except Exception as e:
        return None, f"❌ Erro inesperado: {str(e)}", None


def refinar_dados():
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
    try:
        response = requests.get(f"{API_BASE}/ml/dados-refinados")
        if response.status_code == 200:
            data = response.json()
            
            df = pd.DataFrame(data['dados_refinados'])
            
            mensagem = f"📊 **{data['total']} registros** refinados encontrados"
            return df, mensagem
        else:
            return None, f"❌ Erro ao buscar dados refinados: {response.text}"
    except Exception as e:
        return None, f"❌ Erro: {str(e)}"


def treinar_modelo():
    try:
        response = requests.post(f"{API_BASE}/ml/treinar", json={}, headers={'Content-Type': 'application/json'})
        if response.status_code in [200, 201]:
            data = response.json()
            metricas = data.get('metricas_gerais', data.get('metricas', {}))
            
            acuracia = float(metricas.get('acuracia', data.get('acuracia', 0)))
            precision = float(metricas.get('precision', data.get('precision', 0)))
            recall = float(metricas.get('recall', data.get('recall', 0)))
            f1_score = float(metricas.get('f1_score', data.get('f1_score', 0)))
            
            mensagem = f"✅ {data.get('mensagem', 'Modelo treinado!')}\n📊 Acurácia: {acuracia*100:.1f}%\n🎯 Precision: {precision*100:.1f}%\n🔍 Recall: {recall*100:.1f}%\n⚖️ F1-Score: {f1_score*100:.1f}%"
            
            if 'metricas_por_classe' in data:
                mensagem += f"\n\n📈 Detalhes por classe:"
                metricas_classe = data['metricas_por_classe']
                if 'COMPRAR' in metricas_classe:
                    mensagem += f"\n🟢 COMPRAR: F1={metricas_classe['COMPRAR']['f1']*100:.1f}%"
                if 'MANTER' in metricas_classe:
                    mensagem += f"\n🟡 MANTER: F1={metricas_classe['MANTER']['f1']*100:.1f}%"
                if 'VENDER' in metricas_classe:
                    mensagem += f"\n🔴 VENDER: F1={metricas_classe['VENDER']['f1']*100:.1f}%"
            
            return mensagem
        else:
            return f"❌ Erro ao treinar modelo: {response.text}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


def fazer_predicoes():
    try:
        print("DEBUG - Iniciando predições...")
        
        response_metricas = requests.get(f"{API_BASE}/ml/metricas")
        if response_metricas.status_code != 200:
            return None, "❌ Erro: Nenhum modelo treinado. Treine um modelo primeiro!", None
        
        response_ativos = requests.get(f"{API_BASE}/ibov/ativos")
        if response_ativos.status_code != 200:
            return None, "❌ Erro ao buscar ativos para predição", None
        
        ativos = response_ativos.json()  # TODOS os ativos, não apenas 5
        if not ativos:
            return None, "❌ Nenhum ativo encontrado no banco", None
            
        codigos = [ativo['codigo'] for ativo in ativos]
        print(f"DEBUG - Total de códigos selecionados: {len(codigos)}")
        print(f"DEBUG - Primeiros 10 códigos: {codigos[:10]}")
        
        payload = {"codigos": codigos}
        print(f"DEBUG - Testando {len(codigos)} códigos")
        
        response = requests.post(f"{API_BASE}/ml/prever", 
                               json=payload,
                               headers={'Content-Type': 'application/json'})
        
        print(f"DEBUG - Status: {response.status_code}")
        
        if response.status_code != 200:
            return None, f"❌ Erro em predições: {response.text}", None
        
        data = response.json()
        print(f"DEBUG - Tipo de data: {type(data)}")
        print(f"DEBUG - Keys em data: {list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
        
        if 'predicoes' not in data:
            return None, f"❌ Chave 'predicoes' não encontrada. Keys disponíveis: {list(data.keys())}", None
        
        predicoes = data['predicoes']
        print(f"DEBUG - COMPARAÇÃO IMPORTANTE:")
        print(f"DEBUG - Códigos enviados: {len(codigos)}")
        print(f"DEBUG - Predições recebidas: {len(predicoes)}")
        print(f"DEBUG - Códigos enviados: {codigos}")
        print(f"DEBUG - Códigos que retornaram: {[p.get('codigo', 'N/A') for p in predicoes]}")
        
        if len(predicoes) < len(codigos):
            codigos_faltando = [c for c in codigos if c not in [p.get('codigo', '') for p in predicoes]]
            print(f"DEBUG - CÓDIGOS QUE FALTARAM: {codigos_faltando}")
        
        print(f"DEBUG - Primeira predição: {predicoes[0] if predicoes else 'Lista vazia'}")
        
        dados_simples = []
        for i, pred in enumerate(predicoes):
            print(f"DEBUG - Processando predição {i}: {pred}")
            print(f"DEBUG - Chaves disponíveis: {list(pred.keys()) if isinstance(pred, dict) else 'Não é dict'}")
            
            codigo = str(pred.get('codigo', 'ERRO'))
            predicao = str(pred.get('predicao', pred.get('recomendacao', 'ERRO')))
            confianca = str(pred.get('confianca', 0))
            
            dados_simples.append({
                'Codigo': codigo,
                'Recomendacao': predicao,  # Mudei o nome da coluna
                'Confianca': confianca
            })
        
        print(f"DEBUG - Dados simples: {dados_simples}")
        
        if dados_simples:
            try:
                df_simples = pd.DataFrame(dados_simples)
                print(f"DEBUG - DataFrame criado com sucesso: {df_simples.head()}")
                
                for col in df_simples.columns:
                    df_simples[col] = df_simples[col].astype(str)
                
                recomendacoes = [item['Recomendacao'] for item in dados_simples]
                
                total_comprar = sum(1 for r in recomendacoes if r == 'COMPRAR')
                total_manter = sum(1 for r in recomendacoes if r == 'MANTER')
                total_vender = sum(1 for r in recomendacoes if r == 'VENDER')
                
                print(f"DEBUG - COMPRAR: {total_comprar}, MANTER: {total_manter}, VENDER: {total_vender}")
                
                try:
                    import plotly.graph_objects as go
                    
                    labels = []
                    values = []
                    colors = []
                    
                    if total_comprar > 0:
                        labels.append('COMPRAR')
                        values.append(total_comprar)
                        colors.append('#00AA00')  # Verde
                    
                    if total_manter > 0:
                        labels.append('MANTER')
                        values.append(total_manter)
                        colors.append('#FFA500')  # Laranja
                    
                    if total_vender > 0:
                        labels.append('VENDER')
                        values.append(total_vender)
                        colors.append('#AA0000')  # Vermelho
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        marker=dict(colors=colors),
                        textinfo='label+percent+value',
                        title=f'Distribuição das {len(dados_simples)} Predições'
                    )])
                    
                    fig.update_layout(
                        title=f'📊 Predições IBOVESPA ({len(dados_simples)} ativos)',
                        font=dict(size=14)
                    )
                    
                    print(f"DEBUG - Gráfico criado com sucesso!")
                    
                except Exception as plot_error:
                    print(f"DEBUG - Erro ao criar gráfico: {plot_error}")
                    fig = None
                
                mensagem = f"✅ {len(predicoes)} predições realizadas:\n🟢 COMPRAR: {total_comprar}\n🟡 MANTER: {total_manter}\n🔴 VENDER: {total_vender}"
                
                return df_simples, mensagem, fig
                
            except Exception as df_error:
                print(f"DEBUG - Erro ao criar DataFrame/Gráfico: {df_error}")
                
                texto_resultado = f"Predições realizadas ({len(dados_simples)} ativos):\n\n"
                comprar_count = 0
                manter_count = 0
                vender_count = 0
                
                for i, item in enumerate(dados_simples):
                    if item['Recomendacao'] == 'COMPRAR':
                        emoji = "🟢"
                        comprar_count += 1
                    elif item['Recomendacao'] == 'MANTER':
                        emoji = "🟡"
                        manter_count += 1
                    else:
                        emoji = "🔴"
                        vender_count += 1
                        
                    texto_resultado += f"{emoji} {item['Codigo']}: {item['Recomendacao']} ({item['Confianca']}%)\n"
                
                texto_resultado += f"\n📊 Resumo: {comprar_count} COMPRAR, {manter_count} MANTER, {vender_count} VENDER"
                
                return None, texto_resultado, None
        else:
            return None, "❌ Nenhuma predição válida encontrada", None
        
    except Exception as e:
        error_msg = f"❌ Erro: {str(e)}"
        print(f"DEBUG - Exceção: {str(e)}")
        print(f"DEBUG - Tipo do erro: {type(e)}")
        return None, error_msg, None


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