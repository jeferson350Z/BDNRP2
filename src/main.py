from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
import os
import uuid
from pymongo import MongoClient
import redis
import json
from faststream import FastStream
from faststream.rabbit import RabbitBroker
import asyncio


# ROTA: Lista todos os motoristas e seus saldos (do Redis)
# Configurar FastStream com FastAPI
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
broker = RabbitBroker(RABBITMQ_URL)
rabbit_app = FastStream(broker)

# FastAPI app
app = FastAPI(title="TransFlow API", version="1.0.0")

# Conexões diretas
mongo_client = MongoClient(os.getenv("MONGO_URL", "mongodb://admin:admin123@mongo:27017"))
db = mongo_client.transflow


# ROTA: Lista todos os passageiros cadastrados (do MongoDB)
# CONEXÃO REDIS
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

class Passageiro(BaseModel):
    nome: str
    telefone: str

class Motorista(BaseModel):
    nome: str
    nota: float

class CorridaCreate(BaseModel):
    passageiro: Passageiro
    motorista: Motorista
    origem: str
    destino: str
    valor_corrida: float
    forma_pagamento: str

class Corrida(CorridaCreate):
    id_corrida: str
    processada: bool = False
    saldo_atualizado: bool = False

async def publish_corrida_finalizada(corrida_data: dict):
    """Publica mensagem no RabbitMQ via FastStream"""
    try:
        # Se o broker não está conectado, usar conexão direta com pika para esta versão
        import pika
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                port=5672
            )
        )
        channel = connection.channel()
        channel.basic_publish(
            exchange='',
            routing_key='corridas_finalizadas',
            body=json.dumps(corrida_data)
        )
        connection.close()
        print(f"✅ Mensagem publicada: {corrida_data['id_corrida']}")
    except Exception as e:
        print(f"❌ Erro ao publicar mensagem: {str(e)}")
        raise

@app.post("/corridas", response_model=Corrida)
async def criar_corrida(corrida: CorridaCreate):
    """Cadastra uma nova corrida e publica evento"""
    try:
        corrida_dict = corrida.dict()
        corrida_dict["id_corrida"] = f"corrida_{uuid.uuid4().hex[:8]}"
        corrida_dict["processada"] = False
        corrida_dict["saldo_atualizado"] = False
        
        # Insere no MongoDB
        result = db.corridas.insert_one(corrida_dict)
        corrida_dict["_id"] = str(result.inserted_id)
        
        # Publica no RabbitMQ (assíncrono)
        await publish_corrida_finalizada(corrida_dict)
        
        return corrida_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar corrida: {str(e)}")

@app.get("/corridas", response_model=List[Corrida])
async def listar_corridas():
    """Lista todas as corridas"""
    try:
        corridas = list(db.corridas.find())
        for corrida in corridas:
            corrida["_id"] = str(corrida["_id"])
        return corridas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar corridas: {str(e)}")

@app.get("/corridas/{forma_pagamento}", response_model=List[Corrida])
async def filtrar_corridas_por_pagamento(forma_pagamento: str):
    """Filtra corridas por forma de pagamento"""
    try:
        corridas = list(db.corridas.find({"forma_pagamento": forma_pagamento}))
        for corrida in corridas:
            corrida["_id"] = str(corrida["_id"])
        return corridas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao filtrar corridas: {str(e)}")

@app.get("/saldo/{motorista_nome}")
async def consultar_saldo(motorista_nome: str):
    """Consulta saldo do motorista no Redis"""
    try:
        # Preserve original capitalization (consumer now stores original)
        key = f"saldo:{motorista_nome}"
        saldo = redis_client.get(key)
        if saldo is None:
            # Inicializa saldo com 0.0 se não existir
            redis_client.set(key, "0.0")
            saldo = "0.0"
        return {"motorista": motorista_nome, "saldo": float(saldo)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar saldo: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check do sistema"""
    try:
        # Testa conexão MongoDB
        mongo_client.admin.command('ping')
        mongo_status = "connected"
    except:
        mongo_status = "disconnected"

    try:
        # Testa conexão Redis
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    try:
        # Testa conexão RabbitMQ
        rabbitmq_status = "connected"
    except:
        rabbitmq_status = "disconnected"

    return {
        "status": "healthy",
        "mongo": mongo_status,
        "redis": redis_status,
        "rabbitmq": rabbitmq_status
    }


@app.get("/")
async def root():
    """Root path: redirect to API docs to avoid 404 on base URL."""
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def normalize_redis_saldo_keys():
    """Normalize Redis keys `saldo:*` at startup to avoid duplicates.

    Strategy:
    - Group keys by lowercase motorista name.
    - Choose a canonical name for the group: prefer a capitalized form (e.g. 'Carlos'),
      otherwise take the first seen.
    - Sum values from all variants into the canonical key and delete duplicates.
    """
    try:
        keys = redis_client.keys("saldo:*") or []
        if not keys:
            return

        groups = {}
        for raw in keys:
            k = raw.decode() if isinstance(raw, bytes) else raw
            _, motorista = k.split(":", 1)
            lower = motorista.lower()
            groups.setdefault(lower, []).append(motorista)

        for lower, names in groups.items():
            # prefer capitalized name if present
            preferred = None
            cap = lower.capitalize()
            for n in names:
                if n == cap:
                    preferred = n
                    break
            if not preferred:
                preferred = names[0]

            total = 0.0
            for n in names:
                try:
                    val = redis_client.get(f"saldo:{n}") or "0.0"
                    if isinstance(val, bytes):
                        val = val.decode()
                    total += float(val)
                except Exception:
                    continue

            # set canonical and remove others
            redis_client.set(f"saldo:{preferred}", str(total))
            for n in names:
                if n != preferred:
                    redis_client.delete(f"saldo:{n}")

        print("✅ Redis saldo keys normalized on startup")
    except Exception as e:
        print(f"⚠️ Error normalizing Redis keys on startup: {e}")


@app.get("/routes")
async def list_routes():
    """Return registered routes for debugging."""
    output = []
    for route in app.routes:
        try:
            methods = list(route.methods) if hasattr(route, 'methods') and route.methods else []
            path = getattr(route, 'path', None) or getattr(route, 'url', None) or str(route)
            output.append({
                'path': path,
                'name': getattr(route, 'name', None),
                'methods': sorted([m for m in methods if m not in ('HEAD', 'OPTIONS')])
            })
        except Exception:
            continue
    return {'routes': output}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)