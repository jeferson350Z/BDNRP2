import time
import httpx

BASE = "http://localhost:8000"

sample = {
    "passageiro": {"nome": "Ingridi", "telefone": "5511999999999"},
    "motorista": {"nome": "TestDriver", "nota": 4.7},
    "origem": "Rua Teste, 1",
    "destino": "Av Teste, 2",
    "valor_corrida": 10.5,
    "forma_pagamento": "dinheiro"
}


def test_end_to_end_flow():
    client = httpx.Client(base_url=BASE, timeout=10)

    # create corrida
    r = client.post("/corridas", json=sample)
    assert r.status_code == 200, f"POST /corridas failed: {r.text}"
    data = r.json()
    assert "id_corrida" in data
    corrida_id = data["id_corrida"]

    # wait for consumer to process (poll)
    processed = False
    for _ in range(15):
        time.sleep(1)
        r2 = client.get("/corridas")
        assert r2.status_code == 200
        items = r2.json()
        for c in items:
            if c.get("id_corrida") == corrida_id and c.get("processada"):
                processed = True
                break
        if processed:
            break

    assert processed, "Consumer did not process the corrida in time"

    # check saldo
    r3 = client.get(f"/saldo/{sample['motorista']['nome']}")
    assert r3.status_code == 200
    saldo = r3.json().get("saldo")
    assert saldo is not None and float(saldo) >= sample["valor_corrida"]
