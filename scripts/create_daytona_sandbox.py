import os
import sys
from pprint import pprint

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-test-sandbox"


def main() -> None:
    print("Daytona sandbox creation test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("Sandbox name:", SANDBOX_NAME)
    print("-" * 80)

    confirm = input(
        "Isto vai criar uma sandbox real na Daytona. Digite CREATE para continuar: "
    ).strip()

    if confirm != "CREATE":
        print("Cancelado. Nenhuma sandbox foi criada.")
        return

    try:
        client = DaytonaHTTPClient()

        print("Criando sandbox...")
        sandbox = client.create_sandbox(name=SANDBOX_NAME)
        pprint(sandbox)

        sandbox_id = sandbox.get("id") or sandbox.get("name") or SANDBOX_NAME
        print("-" * 80)
        print("Sandbox criada.")
        print("Identificador:", sandbox_id)

        print("-" * 80)
        print("Listando sandboxes...")
        pprint(client.list_sandboxes())

    except DaytonaHTTPError as exc:
        print(f"ERRO DAYTONA: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
