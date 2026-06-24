import os
import sys

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


def main() -> None:
    print("Daytona HTTP API smoke test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("-" * 80)

    try:
        client = DaytonaHTTPClient()

        key_info = client.validate_key()
        print("validate_key(): OK")
        print(key_info)
        print("-" * 80)

        sandboxes = client.list_sandboxes()
        print("list_sandboxes(): OK")
        print(sandboxes)
        print("-" * 80)

        print("OK: Daytona HTTP API está acessível via camada app.integrations.daytona_http.")

    except DaytonaHTTPError as exc:
        print(f"ERRO DAYTONA: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
