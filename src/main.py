from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import uuid
from pymongo import MongoClient
import redis  # ✅ Já está no requirements.txt
import json
import pika

app = FastAPI(title="TransFlow API", version="1.0.0")

# Conexões diretas - CORRIGIDAS
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"))
db = mongo_client.transflow

# ✅ CONEXÃO REDIS CORRIGIDA para a versão 4.5.4
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True  # Para retornar strings em vez de bytes
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

def publish_corrida_finalizada(corrida_data: dict):
    """Publica mensagem no RabbitMQ"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                port=5672
            )
        )
        channel = connection.channel()
        
        # Declara a exchange
        channel.exchange_declare(exchange='corridas', exchange_type='topic', durable=True)
        
        # Publica a mensagem
        channel.basic_publish(
            exchange='corridas',
            routing_key='corrida.finalizada',
            body=json.dumps(corrida_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # torna a mensagem persistente
            )
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
        
        # Publica no RabbitMQ (síncrono)
        publish_corrida_finalizada(corrida_dict)
        
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
        saldo = redis_client.get(f"saldo:{motorista_nome}")
        if saldo is None:
            redis_client.set(f"saldo:{motorista_nome}", "0.0")
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

    return {
        "status": "healthy",
        "mongo": mongo_status,
        "redis": redis_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)