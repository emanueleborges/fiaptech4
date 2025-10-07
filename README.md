# 🎯 FIAP Tech Challenge - Fase 3

## Sistema de Machine Learning para Análise IBOVESPA

### 📋 Descrição do Projeto

Este projeto implementa um sistema completo de Machine Learning para análise e predição de ativos do IBOVESPA, desenvolvido como parte do **FIAP Tech Challenge - Fase 3**.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🚀 Como Instalar e Executar

### 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Git** para clonar o repositório
- **pip** para gerenciamento de pacotes

### 📦 Passo 1: Clonar o Repositório

```bash
git clone https://github.com/emanueleborges/fiaptech3
cd desafio3-fiap
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

- Flask 3.0+ (API backend)
- Gradio 4.44+ (Interface do usuário)
- Pandas (Manipulação de dados)
- SQLAlchemy (ORM para banco de dados)
- BeautifulSoup4 (Web scraping)
- Plotly (Visualizações interativas)
- APScheduler (Agendamento de tarefas)

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
# Interface básica
python interface.py
```

O dashboard estará disponível em: `http://localhost:7860`

---

## 🎮 Como Usar o Sistema

### 1️⃣ **Coleta de Dados**

- Acesse a aba "📊 Coleta de Dados"
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
desafio3-fiap/
├── app.py                          # Aplicação Flask principal
├── interface.py                    # Interface Gradio básica
├── interface_producao.py           # Interface profissional
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
  https://github.com/emanueleborges/fiaptech3
