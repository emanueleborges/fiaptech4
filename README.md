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

### 🚀 Início Rápido

#### Via Interface Gradio (Recomendado)

1. **Acesse** `http://localhost:7860`
2. **Aba 1 - Coletar Dados**: Digite o símbolo (ex: PETR4, VALE3) e período
3. **Aba 2 - Treinar Modelo**: Selecione o símbolo e configure parâmetros
4. **Aba 3 - Fazer Previsões**: Visualize previsões futuras
5. **Aba 4 - Métricas**: Avalie a performance do modelo

#### Via API (Avançado)

#### 1️⃣ **Coletar Dados Históricos**

Colete dados de uma ação usando Yahoo Finance:

```bash
curl -X POST http://localhost:5000/api/stock-data/coletar \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "PETR4",
    "period": "2y"
  }'
```

**Símbolos comuns:**
- **Brasileiras**: `PETR4`, `VALE3`, `ITUB4`, `BBDC4` (sem .SA)
- **Americanas**: `AAPL`, `GOOGL`, `MSFT`, `TSLA`

**Períodos disponíveis**: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

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

### 📊 Endpoints da API

#### **📈 Stock Data (Coleta de Dados)**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/stock-data/coletar` | Coleta dados do Yahoo Finance |
| GET | `/api/stock-data/symbols` | Lista símbolos disponíveis |
| GET | `/api/stock-data/<symbol>` | Obtém dados históricos (query: limit) |
| GET | `/api/stock-data/<symbol>/info` | Informações da empresa |
| DELETE | `/api/stock-data/<symbol>` | Deleta dados de um símbolo |

**Exemplo de coleta:**
```bash
curl -X POST http://localhost:5000/api/stock-data/coletar \
  -H "Content-Type: application/json" \
  -d '{"symbol": "PETR4", "period": "2y"}'
```

#### **🧠 LSTM (Deep Learning)**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/lstm/treinar` | Treina modelo LSTM |
| GET | `/api/lstm/prever/<symbol>` | Faz previsões (query: dias) |
| GET | `/api/lstm/modelos` | Lista modelos treinados |
| GET | `/api/lstm/metricas/<model_name>` | Métricas do modelo |

**Exemplo de treinamento:**
```bash
curl -X POST http://localhost:5000/api/lstm/treinar \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "PETR4.SA",
    "epochs": 50,
    "batch_size": 32,
    "sequence_length": 60
  }'
```

**Exemplo de previsão:**
```bash
curl http://localhost:5000/api/lstm/prever/PETR4.SA?dias=7
```

### 📈 Métricas de Avaliação

O sistema utiliza 3 métricas principais:

1. **MAE (Mean Absolute Error)**: Erro médio absoluto
2. **RMSE (Root Mean Square Error)**: Raiz do erro quadrático médio
3. **MAPE (Mean Absolute Percentage Error)**: Erro percentual absoluto médio

### 🎨 Interface Gradio

A interface possui 5 abas principais:

1. **📊 Coletar Dados de Ações**
   - Digite o símbolo da ação (ex: PETR4, AAPL)
   - Selecione o período (1 mês a máximo disponível)
   - Clique em "Coletar Dados"

2. **📋 Visualizar Dados Coletados**
   - Selecione um símbolo da lista
   - Defina quantidade de registros (padrão: 100)
   - Visualize tabela e gráfico interativo

3. **🧠 Treinar Modelo LSTM**
   - Escolha o símbolo para treinar
   - Configure hiperparâmetros (epochs, batch_size, etc.)
   - Acompanhe o progresso do treinamento
   - Visualize métricas (MAE, RMSE, MAPE)

4. **🔮 Fazer Previsões**
   - Selecione modelo treinado
   - Escolha número de dias para prever (1-30)
   - Visualize gráfico com previsões futuras
   - Veja tabela com preços previstos

5. **📈 Gerenciar Modelos**
   - Liste todos os modelos treinados
   - Visualize informações e métricas
   - Gerencie modelos salvos

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

### ✅ Implementado

- [x] **Coleta de dados** com Yahoo Finance (yfinance 0.2.66)
- [x] **Modelo LSTM** com arquitetura de 3 camadas
- [x] **Métricas de avaliação** (MAE, RMSE, MAPE)
- [x] **Salvamento do modelo** (.h5) e scaler (.pkl)
- [x] **API RESTful** (Flask) com 10 endpoints
- [x] **Interface Gradio** com 5 abas funcionais
- [x] **Deploy com Docker** (Dockerfile + docker-compose)
- [x] **Documentação Swagger** em `/swagger`
- [x] **Banco de dados SQLite** para persistência
- [x] **Visualizações interativas** com Plotly

### 📊 Resultados

**Dados coletados com sucesso:**
- PETR4.SA (Petrobras)
- VALE3.SA (Vale)
- ITUB4.SA (Itaú)
- AAPL (Apple)

**Modelos treinados:**
- Arquitetura: 3 camadas LSTM + Dropout
- Epochs: 50
- Batch size: 32
- Sequence length: 60 dias

**Métricas obtidas:**
- MAE: ~0.45 (erro médio de R$ 0,45)
- RMSE: ~0.62
- MAPE: ~1.18% (erro percentual)

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

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10+**
- **Flask 2.3** - API RESTful
- **SQLAlchemy** - ORM
- **SQLite** - Banco de dados

### Machine Learning
- **TensorFlow 2.15** - Framework de Deep Learning
- **Keras** - API de alto nível para redes neurais
- **scikit-learn** - Pré-processamento e métricas
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica

### Coleta de Dados
- **yfinance 0.2.66** - Yahoo Finance API
- **Requests** - HTTP client

### Frontend
- **Gradio 4.44** - Interface web interativa
- **Plotly** - Visualizações interativas

### DevOps
- **Docker** - Containerização
- **Docker Compose** - Orquestração

---

## 🐛 Troubleshooting

### Problema: yfinance não coleta dados

**Solução:** Certifique-se de usar yfinance >= 0.2.66
```bash
pip install --upgrade yfinance
```

### Problema: TensorFlow não encontrado

**Solução:** Reinstale TensorFlow
```bash
pip install tensorflow==2.15.0 protobuf==3.20.3
```

### Problema: Erro ao treinar modelo

**Causas possíveis:**
1. Poucos dados coletados (mínimo: 100 registros)
2. Período muito curto (recomendado: >= 1 ano)

**Solução:** Colete dados de período maior
```python
{"symbol": "PETR4", "period": "2y"}  # 2 anos
```

---

## 📚 Documentação Adicional

- **Swagger API**: http://localhost:5000/swagger
- **GitHub**: https://github.com/emanueleborges/fiaptech4
- **Vídeo Demonstração**: https://www.youtube.com/watch?v=CYEjMDKPmKs

---

## 👨‍� Autor

**Emanuel Borges e Rafael Cunha**  
FIAP - Pós Tech Machine Learning Engineering  
Tech Challenge - Fase 4

---

## � Licença

Projeto acadêmico - FIAP 2024/2025

---

**FIAP Tech Challenge - Fase 4** 🚀  
*Deep Learning com LSTM para Predição de Preços de Ações*
