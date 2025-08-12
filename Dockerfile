# Dockerfile

# 1. Use uma imagem base oficial do Python
FROM python:3.12-slim

# 2. Defina variáveis de ambiente para o Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# 4. Copie o arquivo de requisitos primeiro
COPY requirements.txt .

# 5. Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copie o restante do código da sua aplicação
COPY . .

# 7. Defina a variável de ambiente para as credenciais do Google Cloud
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# 8. Exponha a porta que o Streamlit usa
EXPOSE 8501

# 9. Defina o comando para iniciar a aplicação
# <<< MUDANÇA PRINCIPAL AQUI >>>
# Usamos 'python -m streamlit run' que é uma forma mais robusta de invocar um módulo.
# O --server.port 8501 garante que ele use a porta correta, em vez de depender da variável $PORT.
CMD ["python", "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501", "--server.enableCORS", "false"]