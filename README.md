# TransFlow (dev)

DUPLA Jeferson rosa, Alexander guido  
Este repositório contém uma API FastAPI que simula um fluxo de corridas:

- Persistência: MongoDB
- Cache/saldo: Redis
- Mensageria assíncrona: RabbitMQ
- Consumer: Processa eventos `corridas_finalizadas` e atualiza Redis/MongoDB

Como usar (desenvolvimento)

1. Subir os serviços:

```bash
docker-compose up -d --build
```

2. Testar o fluxo manualmente (exemplo):

```bash
curl -X POST http://localhost:8000/corridas \
  -H 'Content-Type: application/json' \
  -d '{
    "passageiro": {"nome":"Ana","telefone":"5511999999999"},
    "motorista": {"nome":"Carlos","nota":4.8},
    "origem":"Rua A, 10",
    "destino":"Av. B, 200",
    "valor_corrida":25.5,
    "forma_pagamento":"cartao"
  }'

# verificar saldo
curl http://localhost:8000/saldo/Carlos

# listar corridas
curl http://localhost:8000/corridas
```

Testes automatizados

Instale dependências e execute os testes:

```bash
pip install -r requirements.txt
pytest -q
```

Normalização e persistência

- Ao iniciar, a API executa uma rotina que normaliza chaves Redis `saldo:*` para evitar duplicatas (soma valores e mantém uma chave canônica).
- `docker-compose.yml` foi atualizado para adicionar um volume persistente para o Redis (`redis_data`) e já existe volume para MongoDB (`mongo_data`).

Backups (exemplos)

- MongoDB (dentro do container `mongo`):
  ```bash
  # cria um dump da database transflow
  docker exec bdnrp2-mongo-1 mongodump --db transflow --archive=/tmp/transflow-$(date +%F).gz --gzip
  docker cp bdnrp2-mongo-1:/tmp/transflow-$(date +%F).gz ./
  ```

- Redis (RDB snapshot):
  ```bash
  # força snapshot no container e copia o dump
  docker exec bdnrp2-redis-1 redis-cli SAVE
  docker cp bdnrp2-redis-1:/data/dump.rdb ./dump.rdb
  ```

Se desejar, posso adicionar hooks/cron para backups automáticos e retenção.
TransFlow Backend Prototype

Este projeto é um protótipo de backend para gerenciar corridas urbanas, focado em processamento de dados em tempo real e assíncrono. Utiliza FastAPI para a API principal, MongoDB para persistência de dados de corrida, Redis para gerenciamento de saldo de motoristas (atômico) e RabbitMQ com FastStream para mensageria assíncrona.

Arquitetura

A arquitetura é baseada em microsserviços contêinerizados, orquestrados pelo Docker Compose:

app (FastAPI/Uvicorn): Servidor principal da API. Responsável por cadastrar corridas e publicar eventos.

consumer (FastStream): Serviço de worker assíncrono. Consome o evento corrida_finalizada, atualiza o saldo do motorista (Redis) e registra a transação no MongoDB.

mongo (MongoDB): Banco de dados não relacional para dados de corrida.

redis (Redis): Cache e banco de dados chave-valor para saldos de motoristas (alta performance e operações atômicas).

rabbitmq (RabbitMQ): Message broker para comunicação assíncrona.

Passos de Instalação

Pré-requisitos: Certifique-se de ter o Docker e o Docker Compose instalados.

Clone o Repositório:

git clone [LINK DO SEU REPOSITÓRIO GITHUB AQUI]
cd transflow


Construir e Iniciar os Contêineres:
O comando abaixo irá construir a imagem da aplicação (baseada no Dockerfile) e subir todos os serviços (app, consumer, mongo, redis, rabbitmq).

docker-compose up --build -d


Verificar Status:
Confirme se todos os serviços estão em execução:

docker-compose ps
# Você deve ver 'Up' para todos os 5 serviços.


Variáveis de Ambiente

As variáveis de ambiente são definidas no arquivo .env para fácil configuração.

Variável

Descrição

Valor Padrão (Docker)

MONGO_URI

URI de conexão do MongoDB

mongodb://mongo:27017

REDIS_HOST

Host do Redis

redis

RABBITMQ_URL

URL de conexão do RabbitMQ

amqp://guest:guest@rabbitmq:5672/

UVICORN_PORT

Porta de exposição da API

8000

Instruções de Uso e Testes

A API estará acessível em http://localhost:8000. Você pode usar o Swagger UI para testar os endpoints: http://localhost:8000/docs.

1. Consultar Saldo Inicial (Redis)

O serviço Redis é inicializado com saldos de exemplo.

Endpoint: GET /saldo/{motorista_nome}

Exemplo:

curl http://localhost:8000/saldo/Carla
# Saída esperada: 100.0


2. Cadastrar e Processar Corrida (MongoDB + RabbitMQ)

Ao cadastrar uma corrida, a API salva o documento no MongoDB e publica o evento. O consumer irá capturar o evento e atualizar o saldo do motorista atomicamente.

Endpoint: POST /corridas

Body (JSON):

{
  "passageiro": { "nome": "Júlia", "telefone": "99999-2222" },
  "motorista": { "nome": "Carla", "nota": 4.9 },
  "origem": "Leblon",
  "destino": "Ipanema",
  "valor_corrida": 25.50,
  "forma_pagamento": "Cartao"
}


Teste de Processamento Assíncrono:

Verifique o log do contêiner transflow_consumer. Você deverá ver as mensagens de processamento:

docker logs transflow_consumer
# ...  Saldo de Carla incrementado em 25.50. Novo saldo: 125.50
# ...  Corrida [ID] atualizada para PROCESSADO no MongoDB.


Consulte o novo saldo:

curl http://localhost:8000/saldo/Carla
# Saída esperada: 125.5


3. Consultar Corridas (MongoDB)

Listar Todas: GET /corridas

Filtrar por Pagamento: GET /corridas/Cartao

Captura de Tela do Sistema em Execução





##**4.Captura de Tela do Sistema em Execução**
![Projeto rodando ](img/Captura%20de%20tela%202025-11-24%20170451.png)

