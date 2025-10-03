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


def refinar_dados():
    """Chama a API para refinar dados para ML"""
    try:
        response = requests.post(f"{API_BASE}/ml/refinar")
        if response.status_code == 200:
            data = response.json()
            mensagem = f"✅ {data['message']}\n📊 Total de registros: {data['total_registros']}"
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
        response = requests.post(f"{API_BASE}/ml/treinar")
        if response.status_code == 200:
            data = response.json()
            
            # Criar gráfico das métricas
            metricas = ['Acurácia', 'Precision', 'Recall', 'F1-Score']
            valores = [float(data['acuracia']), float(data['precision']), float(data['recall']), float(data['f1_score'])]
            
            fig = px.bar(
                x=metricas,
                y=valores,
                title='Métricas do Modelo Treinado',
                color=valores,
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                yaxis=dict(tickformat='.1%', range=[0, 1]),
                xaxis_title="Métricas",
                yaxis_title="Score"
            )
            
            mensagem = f"✅ {data['message']}\n📊 Acurácia: {float(data['acuracia']):.1%}\n🎯 F1-Score: {float(data['f1_score']):.1%}"
            return mensagem, fig
        else:
            return f"❌ Erro ao treinar modelo: {response.text}", None
    except Exception as e:
        return f"❌ Erro: {str(e)}", None


def fazer_predicoes():
    """Chama a API para fazer predições"""
    try:
        # Buscar alguns códigos para testar
        response_ativos = requests.get(f"{API_BASE}/ibov/ativos")
        if response_ativos.status_code != 200:
            return None, "❌ Erro ao buscar ativos para predição", None
        
        ativos = response_ativos.json()[:10]  # Pegar apenas 10 para teste
        codigos = [ativo['codigo'] for ativo in ativos]
        
        # Fazer predição
        response = requests.post(f"{API_BASE}/ml/prever", json={"codigos": codigos})
        
        if response.status_code == 200:
            data = response.json()
            
            # Converter para DataFrame
            df = pd.DataFrame([{
                'Código': pred['codigo'],
                'Predição': pred['predicao'],
                'Confiança': f"{float(pred['confianca']):.1%}",
                'Probabilidade': f"{float(pred['probabilidade']):.3f}",
                'Status': '🟢' if pred['predicao'] == 'COMPRAR' else '🔴' if pred['predicao'] == 'VENDER' else '🟡'
            } for pred in data['predicoes']])
            
            # Criar gráfico de distribuição das predições
            pred_counts = df['Predição'].value_counts()
            fig = px.pie(
                values=pred_counts.values,
                names=pred_counts.index,
                title='Distribuição das Predições'
            )
            
            mensagem = f"🎯 **{data['total']} predições** realizadas com {data['modelo']}"
            return df, mensagem, fig
        else:
            return None, f"❌ Erro nas predições: {response.text}", None
    
    except Exception as e:
        return None, f"❌ Erro: {str(e)}", None


def obter_metricas():
    """Obtém métricas do modelo"""
    try:
        response = requests.get(f"{API_BASE}/ml/metricas")
        if response.status_code == 200:
            data = response.json()
            
            # Criar gráfico das métricas
            metricas = list(data['metricas'].keys())
            valores = [float(v) for v in data['metricas'].values()]
            
            fig = px.bar(
                x=metricas,
                y=valores,
                title='Métricas Atuais do Modelo',
                color=valores,
                color_continuous_scale='plasma'
            )
            fig.update_layout(
                yaxis=dict(tickformat='.1%', range=[0, 1]),
                xaxis_title="Métricas",
                yaxis_title="Score"
            )
            
            mensagem = f"📊 **{data['status']}**\n🕒 Última atualização: {data['ultima_atualizacao']}"
            return mensagem, fig
        else:
            return f"❌ Erro ao buscar métricas: {response.text}", None
    except Exception as e:
        return f"❌ Erro: {str(e)}", None


# Interface Gradio COMPLETA
with gr.Blocks(title="IBOVESPA + ML - Sistema Completo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📊 Sistema IBOVESPA + Machine Learning")
    gr.Markdown("### Sistema de ML - FIAP DESAFIO 3")
    
    with gr.Tab("🔄 Scraping de Dados"):
        gr.Markdown("### Coletar dados do site da B3")
        
        btn_scrap = gr.Button("🚀 Fazer Scraping", variant="primary", size="lg")
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
        
        grafico_treino = gr.Plot(label="📊 Métricas do Modelo")
        
        btn_treinar.click(
            fn=treinar_modelo,
            outputs=[status_treino, grafico_treino]
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
    
    with gr.Tab("📊 Métricas do Modelo"):
        gr.Markdown("### Visualizar métricas do modelo ativo")
        
        btn_metricas = gr.Button("📊 Obter Métricas", variant="secondary")
        status_metricas = gr.Textbox(label="Status", interactive=False)
        
        grafico_metricas = gr.Plot(label="📊 Métricas Atuais")
        
        btn_metricas.click(
            fn=obter_metricas,
            outputs=[status_metricas, grafico_metricas]
        )

if __name__ == "__main__":
    print("🚀 Iniciando Interface Gradio COMPLETA...")
    print("🔗 Conectando com API Flask em http://127.0.0.1:5000")
    print("📊 Interface disponível em: http://127.0.0.1:7863")
    print("")
    print("⚠️  IMPORTANTE: Execute 'python app.py' primeiro!")
    
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7863,
        share=False,
        debug=False
    )