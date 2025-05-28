FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# StreamlitでWebアプリを起動（Docker ComposeでもこのCMDが使われます）
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
