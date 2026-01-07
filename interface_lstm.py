import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:5000"

# ========================================
# FASE 4 - LSTM FUNCTIONS
# ========================================

def coletar_dados_stock(symbol, period):
    """Coleta dados históricos de ações usando yfinance"""
    try:
        # Garantir que o símbolo esteja em maiúsculas
        symbol = symbol.strip().upper()
        
        # Adicionar .SA se for ação brasileira sem sufixo
        if len(symbol) == 5 and not symbol.endswith('.SA'):
            symbol = f"{symbol}.SA"
        
        response = requests.post(
            f"{API_BASE}/api/stock-data/coletar",
            json={
                "symbol": symbol,
                "period": period
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            data = response.json()
            mensagem = f"""✅ **Dados coletados com sucesso!**
            
📊 **Símbolo:** {data['symbol']}
📅 **Período:** {data['periodo']['inicio']} até {data['periodo']['fim']}

📈 **Estatísticas:**
- Total de registros: {data['estatisticas']['total_registros']}
- Registros inseridos: {data['estatisticas']['registros_inseridos']}
- Registros duplicados: {data['estatisticas']['registros_duplicados']}
"""
            return mensagem
        else:
            error_data = response.json()
            mensagem_erro = f"❌ Erro: {error_data.get('erro', 'Erro desconhecido')}"
            if 'dica' in error_data:
                mensagem_erro += f"\n\n💡 Dica: {error_data['dica']}"
            return mensagem_erro
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def listar_symbols_disponiveis():
    """Lista todos os símbolos disponíveis no banco"""
    try:
        response = requests.get(f"{API_BASE}/api/stock-data/symbols")
        if response.status_code == 200:
            data = response.json()
            
            if data['total_symbols'] == 0:
                return None, "📊 Nenhum símbolo encontrado. Colete dados primeiro."
            
            symbols_list = []
            for s in data['symbols']:
                symbols_list.append({
                    'Símbolo': s['symbol'],
                    'Registros': s['total_registros'],
                    'Início': s['periodo']['inicio'],
                    'Fim': s['periodo']['fim']
                })
            
            df = pd.DataFrame(symbols_list)
            mensagem = f"✅ **{data['total_symbols']} símbolos** encontrados"
            
            return df, mensagem
        else:
            return None, "❌ Erro ao listar símbolos"
    except Exception as e:
        return None, f"❌ Erro: {str(e)}"

def visualizar_dados_stock(symbol, limit):
    """Visualiza dados históricos de um símbolo"""
    try:
        response = requests.get(f"{API_BASE}/api/stock-data/{symbol}?limit={limit}")
        if response.status_code == 200:
            data = response.json()
            
            df = pd.DataFrame(data['dados'])
            
            # Criar gráfico de candlestick
            fig = go.Figure(data=[go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol
            )])
            
            fig.update_layout(
                title=f'Histórico de Preços - {symbol}',
                yaxis_title='Preço (R$)',
                xaxis_title='Data',
                template='plotly_white'
            )
            
            mensagem = f"✅ **{data['total']} registros** de {symbol}"
            
            return df, mensagem, fig
        else:
            return None, "❌ Símbolo não encontrado", None
    except Exception as e:
        return None, f"❌ Erro: {str(e)}", None

def treinar_modelo_lstm(symbol, epochs, batch_size, sequence_length, units):
    """Treina modelo LSTM"""
    try:
        mensagem_inicial = f"🧠 Iniciando treinamento do modelo LSTM para {symbol}...\n⏳ Isso pode levar alguns minutos..."
        
        response = requests.post(
            f"{API_BASE}/api/lstm/treinar",
            json={
                "symbol": symbol,
                "epochs": int(epochs),
                "batch_size": int(batch_size),
                "sequence_length": int(sequence_length),
                "units": int(units)
            },
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minutos de timeout
        )
        
        if response.status_code == 201:
            data = response.json()
            
            mensagem = f"""✅ **Modelo treinado com sucesso!**

📊 **Modelo:** {data['model_name']}
🎯 **Símbolo:** {data['symbol']}

⚙️ **Parâmetros:**
- Sequência: {data['parametros']['sequence_length']} dias
- Épocas executadas: {data['parametros']['epochs_executadas']}
- Batch size: {data['parametros']['batch_size']}
- Units LSTM: {data['parametros']['units']}

📈 **Métricas de Avaliação:**
- MAE: {data['metricas']['mae']:.4f}
- RMSE: {data['metricas']['rmse']:.4f}
- MAPE: {data['metricas']['mape']:.2f}%

📅 **Período de Treinamento:**
- Treino: {data['dados']['train_start']} até {data['dados']['train_end']}
- Teste: {data['dados']['test_start']} até {data['dados']['test_end']}

💾 **Modelo salvo em:** {data['model_path']}
"""
            return mensagem
        else:
            erro = response.json().get('erro', 'Erro desconhecido')
            return f"❌ Erro: {erro}"
    except requests.Timeout:
        return "⏱️ Timeout: O treinamento está demorando muito. Tente com menos épocas."
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def fazer_previsao_lstm(symbol, dias):
    """Faz previsão com modelo LSTM"""
    try:
        response = requests.get(f"{API_BASE}/api/lstm/prever/{symbol}?dias={dias}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Criar DataFrame com previsões
            prev_df = pd.DataFrame(data['previsoes'])
            
            # Criar gráfico
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=prev_df['data'],
                y=prev_df['preco_previsto'],
                mode='lines+markers',
                name='Previsão',
                line=dict(color='red', width=2),
                marker=dict(size=8)
            ))
            
            fig.add_hline(
                y=data['ultimo_preco_real'],
                line_dash="dash",
                line_color="green",
                annotation_text=f"Último preço real: R$ {data['ultimo_preco_real']:.2f}"
            )
            
            fig.update_layout(
                title=f'Previsões LSTM - {symbol}',
                xaxis_title='Data',
                yaxis_title='Preço Previsto (R$)',
                template='plotly_white',
                hovermode='x unified'
            )
            
            mensagem = f"""🔮 **Previsões geradas com sucesso!**

📊 **Símbolo:** {symbol}
🏷️ **Modelo:** {data['model_name']}
💰 **Último preço real:** R$ {data['ultimo_preco_real']:.2f}
📅 **Última data:** {data['ultima_data']}

📈 **Métricas do Modelo:**
- MAE: {data['metricas_modelo']['mae']:.4f}
- RMSE: {data['metricas_modelo']['rmse']:.4f}
- MAPE: {data['metricas_modelo']['mape']:.2f}%

🔮 **Próximos {dias} dias:**
"""
            for prev in data['previsoes']:
                emoji = "📈" if prev['variacao_percentual'] > 0 else "📉"
                mensagem += f"\n{emoji} {prev['data']}: R$ {prev['preco_previsto']:.2f} ({prev['variacao_percentual']:+.2f}%)"
            
            return prev_df, mensagem, fig
        else:
            erro = response.json().get('erro', 'Erro desconhecido')
            return None, f"❌ Erro: {erro}", None
    except Exception as e:
        return None, f"❌ Erro: {str(e)}", None

def listar_modelos_treinados(symbol_filter):
    """Lista modelos LSTM treinados"""
    try:
        url = f"{API_BASE}/api/lstm/modelos"
        if symbol_filter:
            url += f"?symbol={symbol_filter}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['total'] == 0:
                return None, "📊 Nenhum modelo encontrado. Treine um modelo primeiro."
            
            modelos_list = []
            for m in data['modelos']:
                modelos_list.append({
                    'Modelo': m['model_name'],
                    'Símbolo': m['symbol'],
                    'MAE': f"{m['metrics']['mae']:.4f}" if m['metrics']['mae'] else 'N/A',
                    'RMSE': f"{m['metrics']['rmse']:.4f}" if m['metrics']['rmse'] else 'N/A',
                    'MAPE': f"{m['metrics']['mape']:.2f}%" if m['metrics']['mape'] else 'N/A',
                    'Criado em': m['created_at'],
                    'Ativo': '✅' if m['is_active'] else '❌'
                })
            
            df = pd.DataFrame(modelos_list)
            mensagem = f"✅ **{data['total']} modelos** encontrados"
            
            return df, mensagem
        else:
            return None, "❌ Erro ao listar modelos"
    except Exception as e:
        return None, f"❌ Erro: {str(e)}"

# ========================================
# INTERFACE GRADIO
# ========================================

with gr.Blocks(title="FIAP Tech Challenge - Fase 4", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("""
    # 🎯 FIAP Tech Challenge - Fase 4
    ## 🧠 Deep Learning com LSTM para Predição de Preços de Ações
    
    **Desenvolvido para o Tech Challenge - Fase 4**  
    Sistema completo de predição de preços usando redes neurais LSTM
    """)
    
    with gr.Tabs():
        
        # TAB 1: Coleta de Dados
        with gr.Tab("📊 Coleta de Dados"):
            gr.Markdown("### Coletar Dados Históricos com Yahoo Finance")
            gr.Markdown("""
**Exemplos de símbolos:**
- 🇧🇷 Ações Brasileiras: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `BBDC4.SA`, `ABEV3.SA`, `BBAS3.SA`, `LREN3.SA`, `MGLU3.SA`, `SUZB3.SA`, `GGBR4.SA`, `WEGE3.SA`, `KLBN11.SA`, `PRIO3.SA`, `CIEL3.SA`, `ELET3.SA`, `CVCB3.SA`, `HAPV3.SA`, `PETR3.SA`, `BRFS3.SA`, `ENBR3.SA`, `RADL3.SA`, `SBSP3.SA`, `TIMS3.SA`, `VIVT3.SA`, `EGIE3.SA`, `MULT3.SA`, `NTCO3.SA`, `SULA11.SA`, `USIM5.SA`, `YDUQ3.SA`
- 🇺🇸 Ações Americanas: `AAPL`, `GOOGL`, `MSFT`, `TSLA`, `AMZN`, `META`, `NVDA`, `JPM`, `BAC`, `NFLX`, `DIS`, `WMT`, `V`, `MA`, `KO`, `PFE`, `INTC`, `ORCL`, `T`, `XOM`, `CVX`, `BA`, `MCD`, `IBM`, `C`, `GM`, `F`, `GE`, `QCOM`, `SBUX`, `PYPL`, `COST`, `NKE`, `HON`, `ADBE`, `CRM`, `AMD`, `TSM`, `BABA`, `BIDU`, `SNAP`, `UBER`, `LYFT`, `SQ`, `SHOP`, `ZM`, `PLTR`, `RIVN`, `LCID`, `COIN`, `ROKU`, `DOCU`, `TWLO`, `NET`, `DDOG`, `SNOW`, `MDB`, `OKTA`, `TEAM`, `CRWD`, `PANW`, `ZS`, `FSLY`, `ETSY`, `PINS`, `SPOT`, `MELI`, `SE`, `BILI`, `JD`, `PDD`, `TCEHY`, `NTES`, `YUMC`, `VIPS`, `TAL`, `EDU`, `QFIN`, `FUTU`, `TIGR`, `HUYA`, `DOYU`, `YY`, `MOMO`, `QD`, `XPEV`, `LI`, `NIO`, `BYDDF`, `TSLA`

**Dica:** Ações brasileiras precisam do sufixo `.SA`
            """)
            
            with gr.Row():
                with gr.Column():
                    symbol_input = gr.Textbox(
                        label="Símbolo da Ação",
                        placeholder="Ex: PETR4.SA ou PETR4 (adiciona .SA automaticamente)",
                        value="PETR4"
                    )
                    period_input = gr.Dropdown(
                        label="Período de Dados",
                        choices=[
                            ("1 mês", "1mo"),
                            ("3 meses", "3mo"),
                            ("6 meses", "6mo"),
                            ("1 ano", "1y"),
                            ("2 anos", "2y"),
                            ("5 anos", "5y"),
                            ("Máximo disponível", "max")
                        ],
                        value="2y",
                        info="Selecione quanto tempo de histórico deseja"
                    )
                    btn_coletar = gr.Button("🔽 Coletar Dados", variant="primary", size="lg")
                
                with gr.Column():
                    output_coleta = gr.Markdown()
            
            btn_coletar.click(
                coletar_dados_stock,
                inputs=[symbol_input, period_input],
                outputs=[output_coleta]
            )
            
            gr.Markdown("---")
            gr.Markdown("### Símbolos Disponíveis")
            
            btn_listar_symbols = gr.Button("📋 Listar Símbolos")
            output_symbols_msg = gr.Markdown()
            output_symbols_table = gr.Dataframe()
            
            btn_listar_symbols.click(
                listar_symbols_disponiveis,
                inputs=[],
                outputs=[output_symbols_table, output_symbols_msg]
            )
        
        # TAB 2: Visualizar Dados
        with gr.Tab("📈 Visualizar Dados"):
            gr.Markdown("### Visualizar Dados Históricos")
            
            with gr.Row():
                symbol_viz = gr.Textbox(
                    label="Símbolo",
                    placeholder="Ex: PETR4.SA",
                    value="PETR4.SA"
                )
                limit_viz = gr.Slider(
                    label="Número de Registros",
                    minimum=30,
                    maximum=500,
                    value=100,
                    step=10
                )
                btn_visualizar = gr.Button("📊 Visualizar", variant="primary")
            
            output_viz_msg = gr.Markdown()
            output_viz_chart = gr.Plot()
            output_viz_table = gr.Dataframe()
            
            btn_visualizar.click(
                visualizar_dados_stock,
                inputs=[symbol_viz, limit_viz],
                outputs=[output_viz_table, output_viz_msg, output_viz_chart]
            )
        
        # TAB 3: Treinar LSTM
        with gr.Tab("🧠 Treinar Modelo LSTM"):
            gr.Markdown("### Treinar Modelo de Deep Learning")
            gr.Markdown("⚠️ **Atenção:** O treinamento pode levar alguns minutos dependendo dos parâmetros.")
            
            with gr.Row():
                with gr.Column():
                    symbol_train = gr.Textbox(
                        label="Símbolo da Ação",
                        placeholder="Ex: PETR4.SA",
                        value="PETR4.SA"
                    )
                    epochs_train = gr.Slider(
                        label="Épocas de Treinamento",
                        minimum=10,
                        maximum=100,
                        value=50,
                        step=10,
                        info="Mais épocas = melhor aprendizado (mas mais lento)"
                    )
                    batch_size_train = gr.Slider(
                        label="Batch Size",
                        minimum=16,
                        maximum=64,
                        value=32,
                        step=16,
                        info="Tamanho do Lote quanto maior = maior processamento de conhecimento de registro de preços"
                        )
                
                with gr.Column():
                    sequence_length_train = gr.Slider(
                        label="Sequência (dias anteriores)",
                        minimum=30,
                        maximum=120,
                        value=60,
                        step=10,
                        info="Quantos dias usar para previsão"
                    )
                    units_train = gr.Slider(
                        label="Units LSTM",
                        minimum=25,
                        maximum=100,
                        value=50,
                        step=25,
                        info="Neurônios na camada LSTM = capacidade de processamento da IA"
                    )
                    btn_treinar = gr.Button("🚀 Treinar Modelo", variant="primary", size="lg")
            
            output_train = gr.Markdown()
            
            btn_treinar.click(
                treinar_modelo_lstm,
                inputs=[symbol_train, epochs_train, batch_size_train, sequence_length_train, units_train],
                outputs=[output_train]
            )
        
        # TAB 4: Fazer Previsões
        with gr.Tab("🔮 Previsões"):
            gr.Markdown("### Fazer Previsões de Preços")
            
            with gr.Row():
                symbol_pred = gr.Textbox(
                    label="Símbolo da Ação",
                    placeholder="Ex: PETR4.SA",
                    value="PETR4.SA"
                )
                dias_pred = gr.Slider(
                    label="Dias para Prever",
                    minimum=1,
                    maximum=30,
                    value=5,
                    step=1
                )
                btn_prever = gr.Button("🔮 Prever Preços", variant="primary")
            
            output_pred_msg = gr.Markdown()
            output_pred_chart = gr.Plot()
            output_pred_table = gr.Dataframe()
            
            btn_prever.click(
                fazer_previsao_lstm,
                inputs=[symbol_pred, dias_pred],
                outputs=[output_pred_table, output_pred_msg, output_pred_chart]
            )
        
        # TAB 5: Modelos Treinados
        with gr.Tab("📚 Modelos Treinados"):
            gr.Markdown("### Modelos LSTM Disponíveis")
            
            with gr.Row():
                symbol_filter_models = gr.Textbox(
                    label="Filtrar por Símbolo (opcional)",
                    placeholder="Ex: PETR4.SA"
                )
                btn_listar_models = gr.Button("📋 Listar Modelos", variant="primary")
            
            output_models_msg = gr.Markdown()
            output_models_table = gr.Dataframe()
            
            btn_listar_models.click(
                listar_modelos_treinados,
                inputs=[symbol_filter_models],
                outputs=[output_models_table, output_models_msg]
            )
    
    gr.Markdown("""
    ---
    ### 📚 Documentação da API
    - Swagger: [http://localhost:5000/swagger](http://localhost:5000/swagger)
    - Repositório: [GitHub](https://github.com/emanueleborges/fiaptech4)
    
    **FIAP Tech Challenge - Fase 4** | Deep Learning e IA 🚀
    """)

if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )
