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
# ... 💰 Saldo de Carla incrementado em 25.50. Novo saldo: 125.50
# ... ✅ Corrida [ID] atualizada para PROCESSADO no MongoDB.


Consulte o novo saldo:

curl http://localhost:8000/saldo/Carla
# Saída esperada: 125.5


3. Consultar Corridas (MongoDB)

Listar Todas: GET /corridas

Filtrar por Pagamento: GET /corridas/Cartao

Captura de Tela do Sistema em Execução

(Neste ponto, você deve adicionar uma imagem real do seu terminal com o docker-compose ps e, idealmente, uma tela do Swagger UI ou dos logs mostrando o processamento assíncrono.)

Link do Repositório GitHub

[Insira o link do seu repositório GitHub público aqui]