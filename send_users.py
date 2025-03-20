import pandas as pd
import requests
import json
from datetime import datetime

# Configurações da API
API_URL = "http://localhost:8000"
TOKEN_URL = f"{API_URL}/token"
USERS_URL = f"{API_URL}/usuarios"

# Credenciais (em um caso real, use variáveis de ambiente)
USERNAME = "admin"
PASSWORD = "admin"

def get_token():
    """Obtém o token JWT para autenticação"""
    response = requests.post(
        TOKEN_URL,
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Erro ao obter token: {response.text}")

def send_user(user_data, token):
    """Envia os dados de um usuário para a API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        USERS_URL,
        headers=headers,
        json=user_data
    )
    
    return response

def main():
    try:
        # Lê o arquivo CSV
        df = pd.read_csv("usuarios.csv")
        
        # Obtém o token de autenticação
        token = get_token()
        print("Token obtido com sucesso!")
        
        # Processa cada linha do CSV
        for index, row in df.iterrows():
            user_data = {
                "nome": row["nome"],
                "email": row["email"],
                "cpf": row["cpf"],
                "data_nascimento": row["data_nascimento"]
            }
            
            print(f"\nProcessando usuário {index + 1}: {user_data['nome']}")
            
            # Envia os dados para a API
            response = send_user(user_data, token)
            
            if response.status_code == 201:
                print(f"✓ Usuário {user_data['nome']} cadastrado com sucesso!")
            else:
                print(f"✗ Erro ao cadastrar usuário {user_data['nome']}:")
                print(f"  Status code: {response.status_code}")
                print(f"  Resposta: {response.text}")
                
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main() 