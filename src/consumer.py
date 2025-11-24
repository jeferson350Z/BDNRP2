from faststream import FastStream
from faststream.rabbit import RabbitBroker
import os
from pymongo import MongoClient
import redis

# Configurações
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")

# Conexões
broker = RabbitBroker(RABBITMQ_URL)
app = FastStream(broker)

# Usando PyMongo síncrono
mongo_client = MongoClient(MONGO_URL)
db = mongo_client.transflow

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

@broker.subscriber("corridas_finalizadas")
async def processar_corrida_finalizada(corrida_data: dict):
    """Processa corrida finalizada: atualiza Redis e MongoDB"""
    try:
        print(f"🔄 Processando corrida: {corrida_data.get('id_corrida', 'unknown')}")
        
        # Preserve original capitalization as requested
        motorista_nome = corrida_data.get('motorista', {}).get('nome', '')
        valor_corrida = corrida_data.get('valor_corrida', 0)
        
        if not motorista_nome:
            print("❌ Erro: Nome do motorista não encontrado")
            return
        
        # Atualizar saldo do motorista no Redis com atomicidade
        with redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(f"saldo:{motorista_nome}")
                    saldo_atual = float(pipe.get(f"saldo:{motorista_nome}") or "0.0")
                    novo_saldo = saldo_atual + valor_corrida
                    
                    pipe.multi()
                    pipe.set(f"saldo:{motorista_nome}", str(novo_saldo))
                    pipe.execute()
                    break
                except redis.WatchError:
                    continue
        
        print(f"💰 Saldo atualizado: {motorista_nome} = {novo_saldo}")
        
        # MongoDB síncrono
        db.corridas.update_one(
            {"id_corrida": corrida_data.get("id_corrida")},
            {"$set": {"processada": True, "saldo_atualizado": True}}
        )
        
        print(f"✅ Corrida {corrida_data.get('id_corrida')} processada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao processar corrida: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    print("🚀 Iniciando consumer FastStream...")
    asyncio.run(app.run())