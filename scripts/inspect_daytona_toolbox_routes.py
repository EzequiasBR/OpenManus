import os
import sys
import time
from pprint import pprint

import httpx

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-toolbox-route-test"
PROXY_BASE = "https://proxy.app.daytona.io/toolbox"


def headers() -> dict:
    api_key = os.getenv("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError("DAYTONA_API_KEY não está definida.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def try_get(url: str) -> None:
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=headers())
        print("GET", url)
        print("STATUS:", response.status_code)
        print("BODY:", response.text[:500])
        print("-" * 80)
    except Exception as exc:
        print("GET", url)
        print("ERROR:", type(exc).__name__, exc)
        print("-" * 80)


def try_post_execute(url: str) -> None:
    payload = {
        "command": "whoami",
        "cwd": "/home/daytona/workspace",
        "env": {"PYTHONUNBUFFERED": "1"},
        "timeout": 15,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers(), json=payload)
        print("POST", url)
        print("STATUS:", response.status_code)
        print("BODY:", response.text[:1000])
        print("-" * 80)
    except Exception as exc:
        print("POST", url)
        print("ERROR:", type(exc).__name__, exc)
        print("-" * 80)


def main() -> None:
    print("Daytona Toolbox route inspection")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))

    confirm = input(
        "Isto vai criar uma sandbox real, testar rotas e deletar no final. "
        "Digite ROUTES para continuar: "
    ).strip()

    if confirm != "ROUTES":
        print("Cancelado.")
        return

    client = DaytonaHTTPClient()
    sandbox_id = None

    try:
        print("Criando sandbox...")
        sandbox = client.create_sandbox(name=SANDBOX_NAME)
        pprint(sandbox)

        sandbox_id = sandbox.get("id")
        if not sandbox_id:
            raise RuntimeError("Sandbox criada sem id.")

        print("sandbox_id:", sandbox_id)
        print("state:", sandbox.get("state"))
        print("toolboxProxyUrl:", sandbox.get("toolboxProxyUrl"))

        print("Aguardando alguns segundos para o daemon/proxy ficar pronto...")
        time.sleep(8)

        get_paths = [
            f"{PROXY_BASE}/{sandbox_id}/toolbox/work-dir",
            f"{PROXY_BASE}/{sandbox_id}/work-dir",
            f"{PROXY_BASE}/sandbox/{sandbox_id}/toolbox/work-dir",
            f"{PROXY_BASE}/sandbox/{sandbox_id}/work-dir",
            f"{PROXY_BASE}/{sandbox_id}/toolbox/project-dir",
            f"{PROXY_BASE}/{sandbox_id}/project-dir",
            f"{PROXY_BASE}/{sandbox_id}/toolbox/user-home-dir",
            f"{PROXY_BASE}/{sandbox_id}/user-home-dir",
        ]

        print("=" * 80)
        print("TESTANDO ROTAS GET")
        print("=" * 80)
        for url in get_paths:
            try_get(url)

        post_paths = [
            f"{PROXY_BASE}/{sandbox_id}/toolbox/process/execute",
            f"{PROXY_BASE}/{sandbox_id}/process/execute",
            f"{PROXY_BASE}/sandbox/{sandbox_id}/toolbox/process/execute",
            f"{PROXY_BASE}/sandbox/{sandbox_id}/process/execute",
        ]

        print("=" * 80)
        print("TESTANDO ROTAS POST /process/execute")
        print("=" * 80)
        for url in post_paths:
            try_post_execute(url)

    except DaytonaHTTPError as exc:
        print(f"ERRO DAYTONA: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)
    finally:
        if sandbox_id:
            print("Limpando sandbox...")
            try:
                pprint(client.delete_sandbox(sandbox_id))
            except Exception as exc:
                print("Falha ao deletar sandbox:", exc)
                print("Delete manualmente:", sandbox_id)


if __name__ == "__main__":
    main()