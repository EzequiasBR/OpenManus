import os
import sys
from pprint import pprint

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-file-api-test"
REMOTE_DIR = "/home/daytona/openmanus_file_test"
REMOTE_FILE = f"{REMOTE_DIR}/hello_daytona.txt"
EXPECTED_TEXT = "DAYTONA_FILE_API_OK\nLinha 2: upload/download validado.\n"


def print_section(title: str) -> None:
    print("-" * 80)
    print(title)
    print("-" * 80)


def main() -> None:
    print("Daytona File API test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("Sandbox name:", SANDBOX_NAME)

    confirm = input(
        "Isto vai criar uma sandbox real, testar arquivos e deletar no final. "
        "Digite FILES para continuar: "
    ).strip()

    if confirm != "FILES":
        print("Cancelado. Nenhuma sandbox foi criada.")
        return

    client = DaytonaHTTPClient()
    sandbox_id = None

    try:
        print_section("Criando sandbox")
        sandbox = client.create_sandbox(name=SANDBOX_NAME)
        pprint(sandbox)

        sandbox_id = sandbox.get("id")
        if not sandbox_id:
            raise DaytonaHTTPError("A sandbox foi criada, mas não retornou campo 'id'.")

        print_section("Criando pasta remota")
        pprint(client.create_folder(sandbox_id, REMOTE_DIR))

        print_section("Enviando arquivo")
        upload_result = client.upload_file(
            sandbox_id=sandbox_id,
            remote_path=REMOTE_FILE,
            content=EXPECTED_TEXT.encode("utf-8"),
            filename="hello_daytona.txt",
            content_type="text/plain",
        )
        pprint(upload_result)

        print_section("Consultando info do arquivo")
        pprint(client.file_info(sandbox_id, REMOTE_FILE))

        print_section("Baixando arquivo")
        downloaded = client.download_file(sandbox_id, REMOTE_FILE)
        downloaded_text = downloaded.decode("utf-8", errors="replace")
        print(downloaded_text)

        if downloaded_text != EXPECTED_TEXT:
            raise DaytonaHTTPError(
                "Conteúdo baixado não confere com o conteúdo enviado."
            )

        print_section("Validando via comando remoto")
        result = client.execute_command(
            sandbox_id=sandbox_id,
            command=f"cat {REMOTE_FILE}",
            cwd="/home/daytona",
            env={"PYTHONUNBUFFERED": "1", "SHELL": "/bin/bash"},
            timeout=20,
        )
        pprint(result)

        if result.get("exitCode") != 0:
            raise DaytonaHTTPError(
                f"cat falhou com exitCode={result.get('exitCode')}: {result.get('result')}"
            )

        if result.get("result") != EXPECTED_TEXT:
            raise DaytonaHTTPError("Resultado do cat não confere.")

        print_section("Removendo pasta remota")
        pprint(client.delete_path(sandbox_id, REMOTE_DIR, recursive=True))

        print_section("Teste File API concluído com sucesso")

    except DaytonaHTTPError as exc:
        print(f"ERRO DAYTONA: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        sys.exit(1)
    finally:
        if sandbox_id:
            print_section("Limpando sandbox")
            try:
                result = client.delete_sandbox(sandbox_id)
                pprint(result)
                print("Sandbox enviada para deleção.")
            except Exception as cleanup_exc:
                print(f"Falha ao deletar sandbox automaticamente: {cleanup_exc}")
                print("Delete manualmente depois:")
                print("python scripts\\delete_daytona_sandbox.py")
                print(f"ID: {sandbox_id}")


if __name__ == "__main__":
    main()
