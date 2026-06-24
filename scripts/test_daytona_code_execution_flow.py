import os
import sys
from pprint import pprint

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-code-flow-test"
REMOTE_DIR = "/home/daytona/openmanus_code_flow"
REMOTE_SCRIPT = f"{REMOTE_DIR}/task.py"
REMOTE_RESULT = f"{REMOTE_DIR}/result.txt"

PYTHON_SCRIPT = f"""\
from pathlib import Path
import json
import platform
import sys

result = {{
    "status": "DAYTONA_CODE_EXECUTION_OK",
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "calculation": sum(range(1, 11)),
}}

Path("{REMOTE_RESULT}").write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("SCRIPT_EXECUTED_OK")
print("RESULT_PATH={REMOTE_RESULT}")
"""


def print_section(title: str) -> None:
    print("-" * 80)
    print(title)
    print("-" * 80)


def main() -> None:
    print("Daytona code execution flow test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("Sandbox name:", SANDBOX_NAME)

    confirm = input(
        "Isto vai criar uma sandbox real, enviar código, executar e deletar no final. "
        "Digite CODE para continuar: "
    ).strip()

    if confirm != "CODE":
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

        print_section("Sandbox criada")
        print("sandbox_id:", sandbox_id)
        print("state:", sandbox.get("state"))
        print("toolboxProxyUrl:", sandbox.get("toolboxProxyUrl"))

        print_section("Criando pasta remota")
        pprint(client.create_folder(sandbox_id, REMOTE_DIR))

        print_section("Enviando script Python")
        upload_result = client.upload_file(
            sandbox_id=sandbox_id,
            remote_path=REMOTE_SCRIPT,
            content=PYTHON_SCRIPT.encode("utf-8"),
            filename="task.py",
            content_type="text/x-python",
        )
        pprint(upload_result)

        print_section("Validando script enviado")
        pprint(client.file_info(sandbox_id, REMOTE_SCRIPT))

        print_section("Executando script dentro da sandbox")
        command = f"python3 {REMOTE_SCRIPT}"
        result = client.execute_command(
            sandbox_id=sandbox_id,
            command=command,
            cwd=REMOTE_DIR,
            env={"PYTHONUNBUFFERED": "1", "SHELL": "/bin/bash"},
            timeout=30,
        )
        pprint(result)

        if result.get("exitCode") != 0:
            raise DaytonaHTTPError(
                f"Execução falhou com exitCode={result.get('exitCode')}: {result.get('result')}"
            )

        if "SCRIPT_EXECUTED_OK" not in result.get("result", ""):
            raise DaytonaHTTPError("A saída do script não confirmou SCRIPT_EXECUTED_OK.")

        print_section("Consultando arquivo de resultado")
        pprint(client.file_info(sandbox_id, REMOTE_RESULT))

        print_section("Baixando resultado")
        downloaded = client.download_file(sandbox_id, REMOTE_RESULT)
        downloaded_text = downloaded.decode("utf-8", errors="replace")
        print(downloaded_text)

        if "DAYTONA_CODE_EXECUTION_OK" not in downloaded_text:
            raise DaytonaHTTPError("Resultado baixado não contém DAYTONA_CODE_EXECUTION_OK.")

        if '"calculation": 55' not in downloaded_text:
            raise DaytonaHTTPError("Resultado baixado não contém calculation=55.")

        print_section("Validando resultado via comando remoto")
        cat_result = client.execute_command(
            sandbox_id=sandbox_id,
            command=f"cat {REMOTE_RESULT}",
            cwd=REMOTE_DIR,
            env={"PYTHONUNBUFFERED": "1", "SHELL": "/bin/bash"},
            timeout=20,
        )
        pprint(cat_result)

        if cat_result.get("exitCode") != 0:
            raise DaytonaHTTPError(
                f"cat result falhou com exitCode={cat_result.get('exitCode')}: {cat_result.get('result')}"
            )

        print_section("Removendo pasta remota")
        pprint(client.delete_path(sandbox_id, REMOTE_DIR, recursive=True))

        print_section("Teste de fluxo de execução concluído com sucesso")

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