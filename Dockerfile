# Dockerfile para FIAP Tech Challenge Fase 4 - LSTM API
FROM python:3.10-slim

# Metadados
LABEL maintainer="FIAP Tech Challenge"
LABEL description="API de Deep Learning com LSTM para predição de preços de ações"
LABEL version="2.0"

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache de camadas)
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p models instance

# Expor porta da aplicação
EXPOSE 5000

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/')"

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
