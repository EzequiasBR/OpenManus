import sys
from pprint import pprint

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


def main() -> None:
    sandbox_id_or_name = input(
        "Digite o ID ou nome da sandbox que deseja deletar: "
    ).strip()

    if not sandbox_id_or_name:
        print("Cancelado: sandbox vazia.")
        return

    print("Sandbox alvo:", sandbox_id_or_name)

    confirm = input(
        "Isto vai DELETAR uma sandbox real na Daytona. Digite DELETE para continuar: "
    ).strip()

    if confirm != "DELETE":
        print("Cancelado. Nenhuma sandbox foi deletada.")
        return

    try:
        client = DaytonaHTTPClient()

        print("Deletando sandbox...")
        result = client.delete_sandbox(sandbox_id_or_name)
        pprint(result)

        print("-" * 80)
        print("Listando sandboxes restantes...")
        pprint(client.list_sandboxes())

    except DaytonaHTTPError as exc:
        print(f"ERRO DAYTONA: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
