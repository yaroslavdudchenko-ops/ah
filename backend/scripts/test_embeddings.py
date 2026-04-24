"""Quick smoke test for AI Gateway embeddings endpoint."""
import asyncio
import json
import os
import sys
import httpx

KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
URL = "https://aigateway.biocad.ru/api/v2/embeddings"
MODEL = "InHouse/embeddings-model-1"


async def main():
    print(f"URL  : {URL}")
    print(f"Model: {MODEL}")
    print(f"Key  : {'***' + KEY[-4:] if KEY else 'NOT SET'}")
    print()

        async with httpx.AsyncClient(timeout=15, verify=False) as client:  # corporate CA
        resp = await client.post(
            URL,
            headers={
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json",
            },
            json={"input": "тест эмбеддингов клинических протоколов", "model": MODEL},
        )
        print(f"HTTP {resp.status_code}")
        body = resp.json()

        if "data" in body and body["data"]:
            emb = body["data"][0]["embedding"]
            print(f"SUCCESS: {len(emb)} dimensions")
            print(f"First 5 values: {emb[:5]}")
        elif "error" in body:
            print(f"API ERROR: {json.dumps(body['error'], ensure_ascii=False)}")
        else:
            print(f"Unexpected response: {json.dumps(body, ensure_ascii=False)[:400]}")


if __name__ == "__main__":
    asyncio.run(main())
