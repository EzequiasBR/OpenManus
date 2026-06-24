import json
import textwrap
import uuid
from typing import Any, Dict, Optional

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError
from app.tool.base import BaseTool


class DaytonaSandboxTool(BaseTool):
    name: str = "daytona_sandbox"
    description: str = (
        "Executa código Python em uma sandbox remota efêmera da Daytona usando HTTP API. "
        "Use esta ferramenta quando precisar executar código com isolamento, testar scripts, "
        "validar lógica, gerar arquivos simples ou obter evidências de execução fora do ambiente local. "
        "A sandbox é criada temporariamente e deletada ao final."
    )

    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["run_python_code"],
                "description": "Ação a executar. Nesta versão, use apenas run_python_code.",
            },
            "code": {
                "type": "string",
                "description": "Código Python completo a ser executado dentro da sandbox Daytona.",
            },
            "timeout": {
                "type": "integer",
                "description": "Tempo máximo de execução em segundos.",
                "default": 30,
            },
            "result_filename": {
                "type": "string",
                "description": (
                    "Nome opcional de arquivo de resultado que o código pode gerar. "
                    "Se existir, a tool tentará baixar e incluir o conteúdo na resposta."
                ),
                "default": "result.txt",
            },
        },
        "required": ["action", "code"],
    }

    async def execute(
        self,
        action: str,
        code: str,
        timeout: int = 30,
        result_filename: str = "result.txt",
    ) -> str:
        if action != "run_python_code":
            return (
                "Erro: ação não suportada. "
                "Nesta versão, use action='run_python_code'."
            )

        if not code or not code.strip():
            return "Erro: o código Python está vazio."

        if timeout < 1:
            timeout = 30

        if timeout > 120:
            timeout = 120

        if not result_filename or not result_filename.strip():
            result_filename = "result.txt"

        client = DaytonaHTTPClient()

        sandbox_id: Optional[str] = None
        sandbox_name = f"openmanus-tool-{uuid.uuid4().hex[:8]}"
        remote_dir = f"/home/daytona/{sandbox_name}"
        remote_script = f"{remote_dir}/task.py"
        remote_result = f"{remote_dir}/{result_filename.strip()}"

        try:
            sandbox = client.create_sandbox(name=sandbox_name)
            sandbox_id = sandbox.get("id")

            if not sandbox_id:
                raise DaytonaHTTPError("Sandbox criada sem campo 'id'.")

            normalized_code = textwrap.dedent(code).strip() + "\n"

            client.create_folder(sandbox_id, remote_dir)

            client.upload_file(
                sandbox_id=sandbox_id,
                remote_path=remote_script,
                content=normalized_code.encode("utf-8"),
                filename="task.py",
                content_type="text/x-python",
            )

            run_result = client.execute_command(
                sandbox_id=sandbox_id,
                command=f"python3 {remote_script}",
                cwd=remote_dir,
                env={
                    "PYTHONUNBUFFERED": "1",
                    "SHELL": "/bin/bash",
                },
                timeout=timeout,
            )

            response: Dict[str, Any] = {
                "ok": run_result.get("exitCode") == 0,
                "sandbox_id": sandbox_id,
                "sandbox_name": sandbox_name,
                "exitCode": run_result.get("exitCode"),
                "stdout": run_result.get("result", ""),
                "remote_script": remote_script,
                "remote_result": remote_result,
            }

            try:
                result_bytes = client.download_file(sandbox_id, remote_result)
                response["result_file_found"] = True
                response["result_file_content"] = result_bytes.decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                response["result_file_found"] = False

            try:
                client.delete_path(sandbox_id, remote_dir, recursive=True)
                response["remote_cleanup"] = True
            except Exception as cleanup_exc:
                response["remote_cleanup"] = False
                response["remote_cleanup_error"] = str(cleanup_exc)

            return json.dumps(response, indent=2, ensure_ascii=False)

        except DaytonaHTTPError as exc:
            return f"Erro Daytona: {exc}"
        except Exception as exc:
            return f"Erro inesperado: {type(exc).__name__}: {exc}"
        finally:
            if sandbox_id:
                try:
                    client.delete_sandbox(sandbox_id)
                except Exception:
                    pass