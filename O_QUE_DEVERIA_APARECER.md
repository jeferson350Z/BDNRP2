# 📍 O QUE VOCÊ DEVERIA VER EM CADA LOCAL

## ✅ CORRETO - API (Port 8000)

### URL: https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/

**Caminho: /health**
```json
{
    "status": "healthy",
    "mongo": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
}
```

**Caminho: /corridas**
```json
[
    {
        "passageiro": {
            "nome": "João Silva",
            "telefone": "11999999999"
        },
        "motorista": {
            "nome": "Carla",
            "nota": 4.5
        },
        "origem": "Av. Paulista",
        "destino": "Av. Brasil",
        "valor_corrida": 45.5,
        "forma_pagamento": "cartao",
        "id_corrida": "corrida_12345678",
        "processada": true,
        "saldo_atualizado": true
    }
]
```

**Caminho: /saldo/carla**
```json
{
    "motorista": "carla",
    "saldo": 123.45
}
```

---

## ❌ ERRADO - MongoDB (Port 27017)

### URL: https://miniature-goggles-x5r675g7q766fvrpq-27017.app.github.dev/

**Mensagem de Erro:**
```
It looks like you are trying to access MongoDB over HTTP on the native driver port.
```

**Por quê?** MongoDB não deveria estar exposto! Agora está corrigido e apenas acessível internamente.

**Credenciais (uso interno apenas):**
```
Username: admin
Password: admin123
String de conexão: mongodb://admin:admin123@mongo:27017
```

---

## ❌ ERRADO - Redis (Port 6379)

### URL: https://miniature-goggles-x5r675g7q766fvrpq-6379.app.github.dev/

**Mensagem de Erro:**
```
Esta página não está a funcionar
miniature-goggles-x5r675g7q766fvrpq-6379.app.github.dev não consegue processar este pedido de momento.
HTTP ERROR 502
```

**Por quê?** Redis não deveria estar exposto! Agora está corrigido e apenas acessível internamente.

**Configuração (uso interno apenas):**
```
Host: redis
Port: 6379
String de conexão: redis://redis:6379
```

---

## ❌ ERRADO - RabbitMQ AMQP (Port 5672)

### URL: https://miniature-goggles-x5r675g7q766fvrpq-5672.app.github.dev/

**Mensagem de Erro:**
```
Esta página não está a funcionar
miniature-goggles-x5r675g7q766fvrpq-5672.app.github.dev não consegue processar este pedido de momento.
HTTP ERROR 502
```

**Por quê?** RabbitMQ AMQP não deveria estar exposto! Agora está corrigido e apenas acessível internamente.

**Credenciais (uso interno apenas):**
```
Username: guest
Password: guest
String de conexão: amqp://guest:guest@rabbitmq:5672/
```

---

## ⚠️ RabbitMQ Management Console (Port 15672)

### URL: https://miniature-goggles-x5r675g7q766fvrpq-15672.app.github.dev/

**Mensagem de Erro:** HTTP 502

**Por quê?** O Management Console está DELIBERADAMENTE não exposto por segurança!

**Como acessar em DESENVOLVIMENTO LOCAL:**
```
URL: http://localhost:15672
Username: guest
Password: guest
```

Mas em GitHub Codespaces, não deve estar exposto à internet.

---

## 📊 Resumo de Portas

| Serviço | Porta | Exposto? | Deve Ver? | Status |
|---------|-------|----------|-----------|--------|
| API | 8000 | ✅ SIM | Respostas JSON | ✅ CORRETO |
| MongoDB | 27017 | ❌ NÃO | HTTP 502 ou erro | ✅ SEGURO |
| Redis | 6379 | ❌ NÃO | HTTP 502 | ✅ SEGURO |
| RabbitMQ AMQP | 5672 | ❌ NÃO | HTTP 502 | ✅ SEGURO |
| RabbitMQ Mgmt | 15672 | ❌ NÃO | HTTP 502 | ✅ SEGURO |

---

## 🔐 Arquitetura Segura

```
Internet (GitHub Codespaces)
    ↓
    ├─→ ✅ API:8000 (PÚBLICO)
    │   ├─ /health
    │   ├─ /corridas
    │   ├─ /saldo/{nome}
    │   └─ POST criar corrida
    │
    └─→ ❌ Tudo mais bloqueado

Rede Docker (PRIVADA)
    ├─ MongoDB:27017
    ├─ Redis:6379
    ├─ RabbitMQ:5672
    ├─ RabbitMQ:15672
    ├─ API (serviço)
    └─ Consumer (serviço)
```

---

## 🎯 O que deveria estar funcionando

✅ Criar corridas via API
✅ Listar corridas via API
✅ Consultar saldos via API
✅ Processar mensagens no consumer
✅ Armazenar em MongoDB
✅ Atualizar saldos em Redis
✅ Fila RabbitMQ funcionando

❌ NÃO deveria estar acessível via browser:
- MongoDB
- Redis
- RabbitMQ

---

## 📞 Testes Rápidos

```bash
# Health Check
curl https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/health

# Criar corrida
curl -X POST https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/corridas \
  -H "Content-Type: application/json" \
  -d '{"passageiro":{"nome":"Teste","telefone":"11999"},"motorista":{"nome":"Carla","nota":4.5},"origem":"A","destino":"B","valor_corrida":50,"forma_pagamento":"cartao"}'

# Consultar saldo
curl https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/saldo/carla
```
