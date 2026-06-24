import os
import sys
from pprint import pprint

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError


SANDBOX_NAME = "openmanus-toolbox-test"


def print_section(title: str) -> None:
    print("-" * 80)
    print(title)
    print("-" * 80)


def main() -> None:
    print("Daytona Toolbox command execution test")
    print("DAYTONA_API_KEY:", bool(os.getenv("DAYTONA_API_KEY")))
    print("Sandbox name:", SANDBOX_NAME)

    confirm = input(
        "Isto vai criar uma sandbox real, executar comandos e deletar no final. "
        "Digite EXECUTE para continuar: "
    ).strip()

    if confirm != "EXECUTE":
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

        print_section("Consultando diretórios da sandbox")
        for label, func in [
            ("project-dir", client.get_project_dir),
            ("user-home-dir", client.get_user_home_dir),
            ("work-dir", client.get_work_dir),
        ]:
            try:
                print(label)
                pprint(func(sandbox_id))
            except DaytonaHTTPError as exc:
                print(f"{label}: falhou: {exc}")

        commands = [
            "whoami",
            "pwd",
            "python3 --version || python --version",
            "echo DAYTONA_TOOLBOX_OK",
            "ls -la /home/daytona",
        ]

        print_section("Executando comandos stateless")
        for command in commands:
            print(f"$ {command}")
            result = client.execute_command(
                sandbox_id=sandbox_id,
                command=command,
                cwd="/home/daytona",
                timeout=20,
            )
            pprint(result)

            exit_code = result.get("exitCode")
            if exit_code != 0:
                raise DaytonaHTTPError(
                    f"Comando falhou com exitCode={exit_code}: {result.get('result')}"
                )

            print()

        print_section("Teste concluído com sucesso")

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
                print(f"python scripts\\delete_daytona_sandbox.py")
                print(f"ID: {sandbox_id}")


if __name__ == "__main__":
    main()
