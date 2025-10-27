# 🎯 FIAP Tech Challenge - Fase 4

## 🧠 Sistema de Deep Learning com LSTM para Predição de Preços de Ações

### 📋 Descrição do Projeto

Este projeto implementa um **modelo de Deep Learning usando redes neurais LSTM (Long Short-Term Memory)** para predição de preços de ações, desenvolvido como parte do **FIAP Tech Challenge - Fase 4**.

O sistema realiza:
- ✅ **Coleta de dados históricos** de ações usando Yahoo Finance (yfinance)
- ✅ **Pré-processamento e normalização** de dados temporais
- ✅ **Treinamento de modelos LSTM** para capturar padrões temporais
- ✅ **Avaliação com métricas** MAE, RMSE e MAPE
- ✅ **API RESTful** para servir previsões
- ✅ **Interface Gradio** para facilitar o uso
- ✅ **Deploy com Docker** para produção

### 🏗️ Arquitetura do Projeto

```
fiaptech4/
├── app/
│   ├── controllers/          # Controllers da API
│   │   ├── lstm_controller.py       # Endpoints LSTM
│   │   └── stock_data_controller.py # Endpoints dados de ações
│   ├── models/              # Modelos de dados (SQLite)
│   │   ├── stock_data_model.py      # Dados históricos
│   │   └── lstm_model_info.py       # Informações dos modelos
│   ├── services/            # Lógica de negócio
│   │   ├── lstm_service.py          # Serviço LSTM
│   │   └── stock_data_service.py    # Coleta de dados
│   └── routes/              # Rotas da API
├── models/                  # Modelos LSTM salvos (.h5)
├── instance/                # Banco de dados SQLite
├── app.py                   # Aplicação Flask
├── interface_lstm.py        # Interface Gradio LSTM
├── Dockerfile               # Container Docker
└── requirements.txt         # Dependências

```

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🚀 Como Instalar e Executar

### 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Git** para clonar o repositório
- **pip** para gerenciamento de pacotes

### 📦 Passo 1: Clonar o Repositório

```bash
git clone https://github.com/emanueleborges/fiaptech4
cd fiaptech4
```

### 🔧 Passo 2: Criar e Ativar Ambiente Virtual

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**

```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

**Linux/Mac:**

```bash
python -m venv venv
source venv/bin/activate
```

### 📚 Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**

- Flask 2.3+ (API backend)
- TensorFlow 2.15+ (Deep Learning)
- Keras 2.15+ (LSTM)
- yfinance 0.2+ (Coleta de dados Yahoo Finance)
- Gradio 4.44+ (Interface do usuário)
- Pandas (Manipulação de dados)
- SQLAlchemy (ORM para banco de dados)
- Scikit-learn (Pré-processamento e métricas)
- Plotly (Visualizações interativas)

### 🗄️ Passo 4: Configurar Banco de Dados

O sistema utiliza SQLite e criará automaticamente as tabelas necessárias:

```bash
# As tabelas serão criadas automaticamente na primeira execução
# Localização: instance/dados.db
```

### ⚡ Passo 5: Iniciar o Sistema

#### 5.1 Iniciar a API Flask (Backend)

```bash
python app.py
```

A API estará disponível em: `http://localhost:5000`

#### 5.2 Iniciar o Dashboard (Frontend)

**Em um novo terminal:**

```bash
# Interface LSTM
python interface_lstm.py
```

O dashboard estará disponível em: `http://localhost:7860`

---

## 🎮 Como Usar o Sistema

### 🚀 Início Rápido - Fase 4 (LSTM)

#### 1️⃣ **Coletar Dados Históricos**

Primeiro, colete dados de uma ação usando Yahoo Finance:

```bash
# Via API
curl -X POST http://localhost:5000/api/stock-data/coletar \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "PETR4.SA",
    "start_date": "2020-01-01",
    "end_date": "2024-10-26"
  }'
```

**Símbolos comuns:**
- Brasileiras: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `BBDC4.SA`
- Americanas: `AAPL`, `GOOGL`, `MSFT`, `TSLA`

#### 2️⃣ **Treinar Modelo LSTM**

Treine um modelo de predição:

```bash
curl -X POST http://localhost:5000/api/lstm/treinar \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "PETR4.SA",
    "epochs": 50,
    "batch_size": 32,
    "sequence_length": 60,
    "units": 50
  }'
```

**Parâmetros:**
- `epochs`: Número de épocas de treinamento (padrão: 50)
- `batch_size`: Tamanho do batch (padrão: 32)
- `sequence_length`: Dias anteriores para análise (padrão: 60)
- `units`: Unidades LSTM (padrão: 50)

#### 3️⃣ **Fazer Previsões**

Preveja os próximos dias:

```bash
curl http://localhost:5000/api/lstm/prever/PETR4.SA?dias=5
```

### 📊 Endpoints da API - Fase 4

#### **Stock Data (Coleta de Dados)**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/stock-data/coletar` | Coleta dados do Yahoo Finance |
| GET | `/api/stock-data/symbols` | Lista símbolos disponíveis |
| GET | `/api/stock-data/<symbol>` | Obtém dados históricos |
| GET | `/api/stock-data/<symbol>/info` | Informações da empresa |
| DELETE | `/api/stock-data/<symbol>` | Deleta dados |

#### **LSTM (Deep Learning)**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/lstm/treinar` | Treina modelo LSTM |
| GET | `/api/lstm/prever/<symbol>` | Faz previsões |
| GET | `/api/lstm/modelos` | Lista modelos treinados |
| GET | `/api/lstm/metricas/<model_name>` | Métricas do modelo |

### 📈 Métricas de Avaliação

O sistema utiliza 3 métricas principais:

1. **MAE (Mean Absolute Error)**: Erro médio absoluto
2. **RMSE (Root Mean Square Error)**: Raiz do erro quadrático médio
3. **MAPE (Mean Absolute Percentage Error)**: Erro percentual absoluto médio

### 🎨 Interface Gradio

A interface possui abas para:
- 📊 **Coleta de Dados**: Baixar dados históricos
- 🧠 **Treinar LSTM**: Configurar e treinar modelos
- 🔮 **Previsões**: Visualizar previsões futuras
- 📈 **Métricas**: Avaliar performance dos modelos

---

## 🐳 Deploy com Docker

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Build e Run

```bash
# Build da imagem
docker build -t fiap-lstm-api .

# Executar container
docker run -p 5000:5000 -v $(pwd)/models:/app/models fiap-lstm-api
```

### Docker Compose

```bash
docker-compose up -d
```

---

## � Documentação Técnica

### 🧠 Arquitetura do Modelo LSTM

```
Input Shape: (sequence_length, 1)
    ↓
LSTM(50 units, return_sequences=True)
    ↓
Dropout(0.2)
    ↓
LSTM(50 units, return_sequences=True)
    ↓
Dropout(0.2)
    ↓
LSTM(50 units, return_sequences=False)
    ↓
Dropout(0.2)
    ↓
Dense(25)
    ↓
Dense(1)
    ↓
Output: Preço previsto
```

### 🔄 Pipeline de Dados

1. **Coleta**: yfinance → SQLite
2. **Pré-processamento**: Normalização (MinMaxScaler)
3. **Sequências**: Criar janelas temporais
4. **Treinamento**: 80% treino, 20% teste
5. **Avaliação**: MAE, RMSE, MAPE
6. **Previsão**: Modelo salvo → Inferência

### �📊 Exemplo de Resposta da API

```json
{
  "symbol": "PETR4.SA",
  "ultimo_preco_real": 38.45,
  "previsoes": [
    {
      "data": "2024-10-28",
      "preco_previsto": 38.67,
      "variacao_percentual": 0.57
    },
    {
      "data": "2024-10-29",
      "preco_previsto": 38.82,
      "variacao_percentual": 0.96
    }
  ],
  "metricas_modelo": {
    "mae": 0.45,
    "rmse": 0.62,
    "mape": 1.18
  }
}
```

---

## 🎯 Requisitos do Tech Challenge Fase 4

- [x] **Coleta de dados** com Yahoo Finance (yfinance)
- [x] **Modelo LSTM** para capturar padrões temporais
- [x] **Métricas de avaliação** (MAE, RMSE, MAPE)
- [x] **Salvamento do modelo** treinado (.h5)
- [x] **API RESTful** (Flask)
- [x] **Deploy com Docker**
- [x] **Monitoramento** de performance
- [x] **Documentação** completa

---

## 🤝 Contribuindo

Este projeto foi desenvolvido para o FIAP Tech Challenge Fase 4.

## 📝 Licença

Projeto acadêmico - FIAP 2024

---

## 📞 Suporte

Para dúvidas sobre o projeto:
- 📧 Email: contato@fiap.com.br
- 🌐 Swagger: http://localhost:5000/swagger

---

**FIAP Tech Challenge - Fase 4** 🚀  
*Deep Learning e IA - Predição de Preços com LSTM*
- Clique em "🚀 Executar Scraping B3"
- Aguarde a coleta dos dados do IBOVESPA

### 2️⃣ **Refinamento**

- Vá para a aba "🔧 Refinamento"
- Clique em "⚡ Refinar Dados"
- Os dados serão processados para Machine Learning

### 3️⃣ **Treinamento**

- Acesse "🤖 Treinamento"
- Clique em "🧠 Treinar Modelo"
- O modelo será treinado e salvo automaticamente

### 4️⃣ **Predições**

- Na aba "🔮 Predições"
- Clique em "🎯 Fazer Predições"
- Visualize as recomendações geradas

### 5️⃣ **Análise**

- Acesse "📈 Análise e Métricas"
- Clique em "📊 Carregar Métricas"
- Acompanhe a performance do modelo

---

## 🏗️ Arquitetura do Sistema

### 📁 Estrutura de Pastas

```
fiaptech4/
├── app.py                          # Aplicação Flask principal
├── interface_lstm.py               # Interface Gradio LSTM
├── requirements.txt                # Dependências do projeto
├── README.md                       # Este arquivo
├── swagger.json                    # Documentação da API
│
├── app/                           # Aplicação principal
│   ├── controllers/               # Controladores (lógica de negócio)
│   │   ├── ibov_controller.py     # Controlador do IBOVESPA
│   │   └── ml_controller.py       # Controlador de ML
│   │
│   ├── models/                    # Modelos de dados
│   │   ├── ibov_model.py          # Modelo dos ativos
│   │   ├── dados_refinados_model.py # Modelo dos dados refinados
│   │   └── modelo_treinado_model.py # Modelo dos modelos treinados
│   │
│   ├── routes/                    # Rotas da API
│   │   └── routes.py              # Definição das rotas
│   │
│   ├── services/                  # Serviços de negócio
│   │   ├── b3_scraper_service.py  # Serviço de scraping
│   │   └── ml_service.py          # Serviço de ML
│   │
│   └── utils/                     # Utilitários
│       └── extensions.py          # Extensões e configurações
│
├── instance/                      # Dados da instância
│   └── dados.db                   # Banco de dados SQLite
│
└── models/                        # Modelos treinados
    └── *.pkl                      # Arquivos dos modelos salvos
```

### 🔄 Fluxo de Dados

1. **Scraping** → Coleta dados do B3 → Salva em `ibov_ativos`
2. **Refinamento** → Processa dados → Cria features → Salva em `dados_refinados`
3. **Treinamento** → Treina modelo → Salva `.pkl` em `/models/`
4. **Predição** → Carrega modelo → Gera recomendações
5. **Dashboard** → Visualiza resultados → Interface interativa

---

## 🔌 API Endpoints

### 📊 IBOVESPA

- `GET /ibov/ativos` - Lista todos os ativos
- `POST /scraping/b3` - Executa scraping do B3

### 🤖 Machine Learning

- `POST /ml/refinar-dados` - Refina dados para ML
- `GET /ml/dados-refinados` - Lista dados refinados
- `POST /ml/treinar` - Treina o modelo
- `POST /ml/predicao` - Faz predições
- `GET /ml/metricas` - Obtém métricas do modelo

### 📈 Monitoramento

- `GET /health` - Status da aplicação
- `GET /swagger` - Documentação da API

---

 🔌 **Links**

* **Link Youtube:**
  https://www.youtube.com/watch?v=CYEjMDKPmKs
* **Linkk Github:**
  https://github.com/emanueleborges/fiaptech4
