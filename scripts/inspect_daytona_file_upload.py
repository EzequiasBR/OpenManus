import os
import sys
from pprint import pprint

import httpx

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-file-upload-inspect"
REMOTE_DIR = "/home/daytona/openmanus_upload_inspect"
REMOTE_FILE = f"{REMOTE_DIR}/hello.txt"
CONTENT = b"DAYTONA_UPLOAD_INSPECT_OK\n"


def headers_json() -> dict:
    api_key = os.getenv("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError("DAYTONA_API_KEY nao definida.")
    return {
        "Authorization": f"Bearer {api_key}",
    }


def print_response(label: str, response: httpx.Response) -> None:
    print("-" * 80)
    print(label)
    print("STATUS:", response.status_code)
    print("HEADERS:", dict(response.headers))
    print("BODY repr:", repr(response.text[:1000]))


def try_upload_variants(toolbox_base_url: str, sandbox_id: str) -> None:
    base = toolbox_base_url.rstrip("/")
    url = f"{base}/{sandbox_id}/files/upload"

    with httpx.Client(timeout=30.0) as client:
        # Variante 1: octet-stream
        r = client.post(
            url,
            headers={
                **headers_json(),
                "Content-Type": "application/octet-stream",
            },
            params={"path": REMOTE_FILE},
            content=CONTENT,
        )
        print_response("VARIANTE 1: raw application/octet-stream", r)

        # Variante 2: text/plain
        r = client.post(
            url,
            headers={
                **headers_json(),
                "Content-Type": "text/plain",
            },
            params={"path": REMOTE_FILE},
            content=CONTENT,
        )
        print_response("VARIANTE 2: raw text/plain", r)

        # Variante 3: sem Content-Type explícito
        r = client.post(
            url,
            headers=headers_json(),
            params={"path": REMOTE_FILE},
            content=CONTENT,
        )
        print_response("VARIANTE 3: raw sem Content-Type", r)

        # Variante 4: multipart field file
        r = client.post(
            url,
            headers=headers_json(),
            params={"path": REMOTE_FILE},
            files={"file": ("hello.txt", CONTENT, "text/plain")},
        )
        print_response("VARIANTE 4: multipart file", r)

        # Variante 5: multipart field data
        r = client.post(
            url,
            headers=headers_json(),
            params={"path": REMOTE_FILE},
            files={"data": ("hello.txt", CONTENT, "text/plain")},
        )
        print_response("VARIANTE 5: multipart data", r)


def main() -> None:
    print("Daytona File Upload route inspection")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))

    confirm = input(
        "Isto vai criar uma sandbox real, testar formatos de upload e deletar no final. "
        "Digite UPLOAD para continuar: "
    ).strip()

    if confirm != "UPLOAD":
        print("Cancelado.")
        return

    client = DaytonaHTTPClient()
    sandbox_id = None

    try:
        print("Criando sandbox...")
        sandbox = client.create_sandbox(name=SANDBOX_NAME)
        pprint(sandbox)

        sandbox_id = sandbox.get("id")
        toolbox_proxy_url = sandbox.get("toolboxProxyUrl") or "https://proxy.app.daytona.io/toolbox"

        if not sandbox_id:
            raise DaytonaHTTPError("Sandbox criada sem id.")

        print("sandbox_id:", sandbox_id)
        print("toolboxProxyUrl:", toolbox_proxy_url)

        print("Criando pasta remota...")
        pprint(client.create_folder(sandbox_id, REMOTE_DIR))

        print("Testando variantes de upload...")
        try_upload_variants(toolbox_proxy_url, sandbox_id)

        print("-" * 80)
        print("Tentando validar arquivo via comando remoto...")
        result = client.execute_command(
            sandbox_id=sandbox_id,
            command=f"ls -la {REMOTE_DIR} && cat {REMOTE_FILE}",
            cwd="/home/daytona",
            env={"PYTHONUNBUFFERED": "1", "SHELL": "/bin/bash"},
            timeout=20,
        )
        pprint(result)

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