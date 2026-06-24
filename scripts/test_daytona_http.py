import os
import sys
import httpx


BASE_URL = "https://app.daytona.io/api"


def get_headers() -> dict:
    api_key = os.getenv("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError("DAYTONA_API_KEY não está definida no ambiente.")

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def request(method: str, path: str, **kwargs):
    url = f"{BASE_URL}{path}"
    headers = get_headers()

    with httpx.Client(timeout=30.0) as client:
        response = client.request(method, url, headers=headers, **kwargs)

    print(f"{method} {path}")
    print(f"Status: {response.status_code}")

    text = response.text
    if len(text) > 1500:
        text = text[:1500] + "\n... [truncated]"

    print(text)
    print("-" * 80)

    return response


def main():
    print("Daytona HTTP API smoke test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("-" * 80)

    current_key = request("GET", "/api-keys/current")
    if current_key.status_code != 200:
        print("Falha: API key não validou.")
        sys.exit(1)

    sandboxes = request("GET", "/sandbox")
    if sandboxes.status_code != 200:
        print("Falha: não foi possível listar sandboxes.")
        sys.exit(1)

    print("OK: Daytona HTTP API está acessível.")


if __name__ == "__main__":
    main()
