import pandas as pd
import requests
from datetime import datetime
import json

def validar_cpf(cpf: str) -> bool:
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False
    
    # Calcula os dígitos verificadores
    for i in range(9, 11):
        valor = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digito = ((valor * 10) % 11) % 10
        if int(cpf[i]) != digito:
            return False
    return True

def validar_data(data: str) -> bool:
    try:
        datetime.strptime(data, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def obter_token(url_base: str, username: str, password: str) -> str:
    """Obtém o token de autenticação"""
    response = requests.post(
        f"{url_base}/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception("Falha na autenticação")

def enviar_usuarios(arquivo_csv: str, url_base: str, token: str):
    """Envia os dados dos usuários para a API"""
    # Lê o arquivo CSV
    df = pd.read_csv(arquivo_csv)
    
    # Configura o cabeçalho com o token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Processa cada linha do CSV
    for index, row in df.iterrows():
        # Valida os dados antes de enviar
        if not row['nome'].strip():
            print(f"Erro: Nome vazio na linha {index + 1}")
            continue
            
        if not validar_cpf(row['cpf']):
            print(f"Erro: CPF inválido na linha {index + 1}")
            continue
            
        if not validar_data(row['data_nascimento']):
            print(f"Erro: Data de nascimento inválida na linha {index + 1}")
            continue
        
        # Prepara os dados para envio
        dados = {
            "nome": row['nome'].strip(),
            "email": row['email'].strip(),
            "cpf": row['cpf'].strip(),
            "data_nascimento": row['data_nascimento']
        }
        
        # Envia a requisição
        try:
            response = requests.post(
                f"{url_base}/usuarios/",
                headers=headers,
                json=dados
            )
            
            if response.status_code == 201:
                print(f"Usuário {row['nome']} cadastrado com sucesso!")
            else:
                print(f"Erro ao cadastrar {row['nome']}: {response.text}")
                
        except Exception as e:
            print(f"Erro ao processar {row['nome']}: {str(e)}")

if __name__ == "__main__":
    URL_BASE = "http://localhost:8000"
    ARQUIVO_CSV = "usuarios.csv"
    
    # Obtém o token (você pode modificar as credenciais conforme necessário)
    token = obter_token(URL_BASE, "admin", "admin123")
    
    # Envia os usuários
    enviar_usuarios(ARQUIVO_CSV, URL_BASE, token) 