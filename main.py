from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime, timedelta
from typing import Optional, List
import re
from dateutil import parser

app = FastAPI(title="API de Cadastro de Usuários")

# Configurações de segurança
SECRET_KEY = "sua_chave_secreta_aqui"  # Em produção, use uma chave segura
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelo de dados
class User(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    data_nascimento: str

class UserInDB(User):
    id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Funções auxiliares
def validate_cpf(cpf: str) -> bool:
    # Remove caracteres não numéricos (pontos e traço)
    cpf_numeros = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf_numeros) != 11:
        return False
        
    # Verifica se o formato está correto (XXX.XXX.XXX-XX)
    padrao_cpf = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
    if not re.match(padrao_cpf, cpf):
        return False
    
    return True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Simulação de banco de dados
fake_users_db = []
user_id_counter = 1

# Endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Em um caso real, você verificaria as credenciais contra um banco de dados
    if form_data.username != "admin" or form_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais incorretas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/usuarios", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(user: User, token: str = Depends(oauth2_scheme)):
    try:
        # Validação do CPF
        if not validate_cpf(user.cpf):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF inválido"
            )
        
        # Validação da data de nascimento
        try:
            data_nascimento = parser.parse(user.data_nascimento)
            if data_nascimento > datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data de nascimento não pode ser no futuro"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )
        
        # Simula a criação do usuário no banco de dados
        global user_id_counter
        user_dict = user.model_dump()
        user_dict["id"] = user_id_counter
        user_id_counter += 1
        fake_users_db.append(user_dict)
        
        return user_dict
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/usuarios", response_model=List[UserInDB])
async def list_users(token: str = Depends(oauth2_scheme)):
    """Lista todos os usuários cadastrados"""
    try:
        return fake_users_db
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/usuarios/{user_id}", response_model=UserInDB)
async def get_user(user_id: int, token: str = Depends(oauth2_scheme)):
    """Busca um usuário específico pelo ID"""
    try:
        for user in fake_users_db:
            if user["id"] == user_id:
                return user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 