from pydantic import BaseModel, EmailStr, validator
from datetime import date
import re

class UserBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    data_nascimento: date

    @validator('nome')
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('O nome não pode estar vazio')
        return v.strip()

    @validator('cpf')
    def cpf_valido(cls, v):
        # Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, v))
        
        if not re.match(r'^\d{11}$', cpf):
            raise ValueError('CPF deve conter 11 dígitos')
            
        # Verifica se todos os dígitos são iguais
        if len(set(cpf)) == 1:
            raise ValueError('CPF inválido')
            
        # Calcula os dígitos verificadores
        for i in range(9, 11):
            valor = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
            digito = ((valor * 10) % 11) % 10
            if int(cpf[i]) != digito:
                raise ValueError('CPF inválido')
                
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True 