# Dockerfile

# 1. Use uma imagem base oficial do Python
FROM python:3.12-slim

# 2. Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Copie o arquivo de requisitos primeiro (para aproveitar o cache do Docker)
COPY requirements.txt .

# 4. Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copie o restante do código da sua aplicação para o contêiner
COPY . .

# 6. Defina a variável de ambiente para as credenciais do Google Cloud
# O arquivo será copiado para dentro do contêiner no momento da execução no Cloud Run
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# 7. Exponha a porta que o Streamlit usa
EXPOSE 8501

# 8. Defina o comando para iniciar a aplicação quando o contêiner rodar
# O --server.port $PORT é crucial para o Cloud Run
CMD ["streamlit", "run", "dashboard.py", "--server.port", "8501", "--server.enableCORS", "false"]