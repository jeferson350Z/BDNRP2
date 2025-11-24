# 🔒 Guia de Acesso - TransFlow Backend

## ✅ O que DEVE estar acessível

### 📡 API (Porta 8000)
```
URL: https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/

Rotas Disponíveis:
- GET  /health                  → Status da API
- POST /corridas               → Criar nova corrida
- GET  /corridas               → Listar todas as corridas
- GET  /corridas/{forma_pagamento} → Filtrar por forma de pagamento
- GET  /saldo/{motorista_nome} → Consultar saldo do motorista

Exemplo:
curl -X POST https://miniature-goggles-x5r675g7q766fvrpq-8000.app.github.dev/corridas \
  -H "Content-Type: application/json" \
  -d '{
    "passageiro": {"nome": "João", "telefone": "11999999999"},
    "motorista": {"nome": "Carla", "nota": 4.5},
    "origem": "Av. Paulista",
    "destino": "Av. Brasil",
    "valor_corrida": 45.50,
    "forma_pagamento": "cartao"
  }'
```

---

## ❌ O que NÃO deveria estar acessível (Segurança)

### 1️⃣ MongoDB (Porta 27017)
```
❌ https://miniature-goggles-x5r675g7q766fvrpq-27017.app.github.dev/
Erro esperado: "It looks like you are trying to access MongoDB over HTTP..."

✅ CORRETO: Acesso APENAS via string de conexão interna
   mongodb://admin:admin123@mongo:27017
```

**Credenciais MongoDB:**
```
Username: admin
Password: admin123
Database: transflow
```

---

### 2️⃣ Redis (Porta 6379)
```
❌ https://miniature-goggles-x5r675g7q766fvrpq-6379.app.github.dev/
Erro esperado: "HTTP ERROR 502"

✅ CORRETO: Acesso APENAS via conexão interna
   redis://redis:6379
```

**Redis em Desenvolvimento:**
- Sem autenticação padrão
- Acessível apenas dentro da rede Docker

---

### 3️⃣ RabbitMQ (Porta 5672 - AMQP)
```
❌ https://miniature-goggles-x5r675g7q766fvrpq-5672.app.github.dev/
Erro esperado: "HTTP ERROR 502"

 CORRETO: Acesso APENAS via string de conexão interna
   amqp://guest:guest@rabbitmq:5672/
```

**RabbitMQ Credenciais:**
```
Username: guest
Password: guest
```

---

### 4️ RabbitMQ Management Console (Porta 15672 - HTTP)
```
❌ https://miniature-goggles-x5r675g7q766fvrpq-15672.app.github.dev/
Erro esperado: "HTTP ERROR 502 - Connection Refused"

⚠️  Nota: O Management Console está DELIBERADAMENTE não exposto
    por motivos de segurança em produção.
    
Em DESENVOLVIMENTO LOCAL (localhost):
✅ http://localhost:15672
   Username: guest
   Password: guest
```

---

## 🔐 Arquitetura de Segurança

```
┌─────────────────────────────────────────┐
│  INTERNET (GitHub Codespaces)           │
│                                         │
│  ✅ API:8000 (EXPOSTO)                  │
│     └─→ Rotas HTTP públicas             │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  REDE DOCKER INTERNA (Privada)          │
│                                         │
│  ❌ MongoDB:27017   (NÃO EXPOSTO)       │
│  ❌ Redis:6379     (NÃO EXPOSTO)       │
│  ❌ RabbitMQ:5672  (NÃO EXPOSTO)       │
│  ❌ RabbitMQ:15672 (NÃO EXPOSTO)       │
│                                         │
│  Apenas serviços internos               │
│  (API, Consumer) podem acessar         │
└─────────────────────────────────────────┘
```

---

## 📋 Checklist de Segurança

- ✅ Serviços internos sem exposição HTTP
- ✅ Apenas API acessível na internet
- ✅ Credenciais separadas em `.env`
- ✅ Comunicação interna via hostnames Docker
- ✅ RabbitMQ Management Console (porta 15672) não exposto

---

## 🚀 Para Produção

Quando for fazer deploy em produção:

1. **Alterar Credenciais**
   ```env
   MONGO_INITDB_ROOT_USERNAME=seu_usuario_unico
   MONGO_INITDB_ROOT_PASSWORD=senha_forte_aleatoria
   RABBITMQ_DEFAULT_USER=usuario_rabbitmq
   RABBITMQ_DEFAULT_PASS=senha_forte_aleatoria
   ```

2. **Usar SSL/TLS**
   ```yaml
   # docker-compose.yml
   api:
     environment:
       - API_HTTPS=true
   ```

3. **Implementar Autenticação na API**
   ```python
   # src/main.py
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```

4. **Configurar Firewalls**
   - Apenas porta 443 (HTTPS)
   - Bloquear todas as outras

5. **Usar Secrets Gerenciados**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault

---

## 📞 Suporte

Para mais informações sobre as APIs, veja o arquivo `README.md` original.
