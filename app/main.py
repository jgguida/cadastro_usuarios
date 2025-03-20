from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
import csv
from io import StringIO
import os
from sqlalchemy import and_

from database.database import engine, get_db, Base, SessionLocal
from models.user import User
from schemas.user import UserCreate, User as UserSchema

# Criar as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Configurações de segurança
SECRET_KEY = "sua_chave_secreta_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuração do FastAPI
app = FastAPI(
    title="Sistema de Cadastro de Usuários",
    description="API para cadastro e gerenciamento de usuários",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de segurança
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Configuração dos templates e arquivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Funções de autenticação
def verify_password(plain_password: str, hashed_password: str = None):
    if hashed_password is None:
        return plain_password == "admin"
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

# Rotas de autenticação
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == "admin" and password == "admin":
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            expires=1800,
        )
        return response
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Usuário ou senha inválidos"},
        status_code=400
    )

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# Middleware para verificar autenticação
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    if request.url.path in ["/login", "/static/css/style.css", "/static/js/main.js"]:
        return await call_next(request)

    user = await get_current_user(request)
    if not user and request.url.path != "/login":
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)

# Rotas
@app.post("/usuarios/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    # Verificar se já existe usuário com este email
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email já registrado"
        )
    
    # Verificar se já existe usuário com este CPF
    db_user = db.query(User).filter(User.cpf == user.cpf).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="CPF já registrado"
        )
    
    # Criar novo usuário
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/usuarios/", response_model=List[UserSchema])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    usuarios = db.query(User).offset(skip).limit(limit).all()
    return usuarios

# Rotas de template
@app.get("/")
async def home(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": users,
        "username": user
    })

@app.get("/cadastro")
async def cadastro_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request, "username": "admin"})

@app.post("/cadastro")
async def cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...)
):
    db = SessionLocal()
    try:
        # Verificar email duplicado
        if db.query(User).filter(User.email == email).first():
            return templates.TemplateResponse(
                "cadastro.html",
                {
                    "request": request,
                    "error": "Email já cadastrado",
                    "username": "admin"
                },
                status_code=400
            )

        # Verificar CPF duplicado
        if db.query(User).filter(User.cpf == cpf).first():
            return templates.TemplateResponse(
                "cadastro.html",
                {
                    "request": request,
                    "error": "CPF já cadastrado",
                    "username": "admin"
                },
                status_code=400
            )

        # Criar usuário
        user = User(
            nome=nome,
            email=email,
            cpf=cpf,
            data_nascimento=datetime.strptime(data_nascimento, "%Y-%m-%d")
        )
        db.add(user)
        db.commit()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "cadastro.html",
            {
                "request": request,
                "error": f"Erro ao cadastrar usuário: {str(e)}",
                "username": "admin"
            },
            status_code=400
        )
    finally:
        db.close()

@app.get("/importar-csv")
async def importar_csv_page(request: Request):
    return templates.TemplateResponse("importar_csv.html", {"request": request, "username": "admin"})

@app.post("/importar-csv")
async def importar_csv(request: Request, arquivo: UploadFile = File(...)):
    if not arquivo.filename.endswith('.csv'):
        return templates.TemplateResponse(
            "importar_csv.html",
            {
                "request": request,
                "error": "Por favor, envie um arquivo CSV válido",
                "username": "admin"
            },
            status_code=400
        )

    try:
        contents = await arquivo.read()
        csv_text = contents.decode('utf-8')
        
        # Remover BOM se presente
        if csv_text.startswith('\ufeff'):
            csv_text = csv_text[1:]
            
        csv_data = StringIO(csv_text)
        csv_reader = csv.DictReader(csv_data)
        
        required_fields = ['nome', 'email', 'cpf', 'data_nascimento']
        header = csv_reader.fieldnames

        if not header:
            return templates.TemplateResponse(
                "importar_csv.html",
                {
                    "request": request,
                    "error": "O arquivo CSV está vazio ou mal formatado",
                    "username": "admin"
                },
                status_code=400
            )

        missing_fields = [field for field in required_fields if field not in header]
        if missing_fields:
            return templates.TemplateResponse(
                "importar_csv.html",
                {
                    "request": request,
                    "error": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}\nCampos encontrados: {', '.join(header)}",
                    "username": "admin"
                },
                status_code=400
            )
        
        db = SessionLocal()
        users_added = 0
        errors = []

        try:
            for row in csv_reader:
                try:
                    # Validar data - tentar diferentes formatos
                    data_str = row['data_nascimento'].strip()
                    try:
                        # Tentar formato YYYY-MM-DD
                        data_nascimento = datetime.strptime(data_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            # Tentar formato DD/MM/YYYY
                            data_nascimento = datetime.strptime(data_str, "%d/%m/%Y")
                        except ValueError:
                            raise ValueError(f"Data inválida para o usuário {row['nome']}: {data_str}. Use o formato DD/MM/AAAA ou AAAA-MM-DD")

                    # Verificar email duplicado
                    if db.query(User).filter(User.email == row['email'].strip()).first():
                        raise ValueError(f"Email já cadastrado: {row['email']}")

                    # Verificar CPF duplicado
                    if db.query(User).filter(User.cpf == row['cpf'].strip()).first():
                        raise ValueError(f"CPF já cadastrado: {row['cpf']}")

                    user = User(
                        nome=row['nome'].strip(),
                        email=row['email'].strip(),
                        cpf=row['cpf'].strip(),
                        data_nascimento=data_nascimento
                    )
                    db.add(user)
                    users_added += 1
                except Exception as e:
                    errors.append(str(e))

            if errors:
                db.rollback()
                error_message = "Erros encontrados:\n" + "\n".join(errors)
                return templates.TemplateResponse(
                    "importar_csv.html",
                    {
                        "request": request,
                        "error": error_message,
                        "username": "admin"
                    },
                    status_code=400
                )

            db.commit()
            return templates.TemplateResponse(
                "importar_csv.html",
                {
                    "request": request,
                    "success": f"{users_added} usuários importados com sucesso!",
                    "username": "admin"
                }
            )

        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "importar_csv.html",
                {
                    "request": request,
                    "error": f"Erro ao processar o arquivo: {str(e)}",
                    "username": "admin"
                },
                status_code=400
            )
        finally:
            db.close()

    except UnicodeDecodeError:
        return templates.TemplateResponse(
            "importar_csv.html",
            {
                "request": request,
                "error": "Erro ao ler o arquivo. Certifique-se que é um arquivo CSV válido em formato UTF-8",
                "username": "admin"
            },
            status_code=400
        )
    except Exception as e:
        return templates.TemplateResponse(
            "importar_csv.html",
            {
                "request": request,
                "error": f"Erro inesperado: {str(e)}",
                "username": "admin"
            },
            status_code=400
        )

# Rotas da API
@app.get("/api/users")
async def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users

@app.get("/api/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@app.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        # Tenta converter a data para o formato correto
        data_nascimento_obj = None
        try:
            data_nascimento_obj = datetime.strptime(data_nascimento, "%Y-%m-%d")
        except ValueError:
            try:
                data_nascimento_obj = datetime.strptime(data_nascimento, "%d/%m/%Y")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido")

        # Verifica se o email já existe para outro usuário
        existing_user = db.query(User).filter(
            and_(User.email == email, User.id != user_id)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email já cadastrado")

        # Verifica se o CPF já existe para outro usuário
        existing_user = db.query(User).filter(
            and_(User.cpf == cpf, User.id != user_id)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="CPF já cadastrado")

        user.nome = nome
        user.email = email
        user.cpf = cpf
        user.data_nascimento = data_nascimento_obj
        db.commit()
        
        return {"message": "Usuário atualizado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    try:
        db.delete(user)
        db.commit()
        return {"message": "Usuário excluído com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) 