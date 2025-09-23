# Projeto Flask Exemplo

Este projeto é um exemplo simples de aplicação Flask para FIAP.

## Pré-requisitos
- Python 3.9+
- Git

## Passos para executar

1. **Clone o repositório:**
   ```sh
   git clone <url-do-repositorio>
   cd fiaptech3
   ```

2. **Crie o ambiente virtual:**
   ```sh
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - No Windows PowerShell:
     ```sh
     .\venv\Scripts\Activate.ps1
     ```
   - No CMD:
     ```sh
     .\venv\Scripts\activate.bat
     ```
   - No Linux/Mac:
     ```sh
     source venv/bin/activate
     ```

4. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```


5. **Execute a aplicação:**
    - Se o ambiente virtual estiver ativado:
       ```sh
       python app.py
       ```
    - Ou execute diretamente usando o Python do venv (mesmo sem ativar):
       ```sh
       ./venv/Scripts/python.exe app.py
       ```

6. **Acesse no navegador:**
   [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

Se precisar de mais informações, consulte a documentação do Flask: https://flask.palletsprojects.com/
