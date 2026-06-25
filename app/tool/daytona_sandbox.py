import json
import textwrap
import uuid
from typing import Any, Dict, Optional

from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError
from app.tool.base import BaseTool


MAX_CODE_CHARS = 20000
MAX_RESULT_FILE_CHARS = 12000
MAX_STDOUT_CHARS = 12000
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120


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
            "debug": {
                "type": "boolean",
                "description": (
                    "Quando true, inclui detalhes internos como sandbox_id, sandbox_name "
                    "e caminhos remotos. Use apenas para diagnóstico."
                ),
                "default": False,
            },
        },
        "required": ["action", "code"],
    }

    async def execute(
        self,
        action: str,
        code: str,
        timeout: int = DEFAULT_TIMEOUT,
        result_filename: str = "result.txt",
        debug: bool = False,
    ) -> str:
        if action != "run_python_code":
            return (
                "Erro: ação não suportada. "
                "Nesta versão, use action='run_python_code'."
            )

        if not code or not code.strip():
            return "Erro: o código Python está vazio."

        if len(code) > MAX_CODE_CHARS:
            return (
                f"Erro: código Python grande demais. "
                f"Limite={MAX_CODE_CHARS} caracteres, recebido={len(code)}."
            )

        if timeout < 1:
            timeout = DEFAULT_TIMEOUT

        if timeout > MAX_TIMEOUT:
            timeout = MAX_TIMEOUT

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

            stdout = run_result.get("result", "") or ""
            stdout_truncated = len(stdout) > MAX_STDOUT_CHARS
            if stdout_truncated:
                stdout = stdout[:MAX_STDOUT_CHARS]

            response: Dict[str, Any] = {
                "ok": run_result.get("exitCode") == 0,
                "exitCode": run_result.get("exitCode"),
                "stdout": stdout,
                "stdout_truncated": stdout_truncated,
                "result_file_found": False,
                "cleanup": {
                    "remote_dir_deleted": False,
                    "sandbox_delete_requested": False,
                },
            }

            if debug:
                response["debug"] = {
                    "sandbox_id": sandbox_id,
                    "sandbox_name": sandbox_name,
                    "remote_script": remote_script,
                    "remote_result": remote_result,
                }
            try:
                result_bytes = client.download_file(sandbox_id, remote_result)
                result_text = result_bytes.decode("utf-8", errors="replace")
                result_truncated = len(result_text) > MAX_RESULT_FILE_CHARS
                if result_truncated:
                    result_text = result_text[:MAX_RESULT_FILE_CHARS]

                response["result_file_found"] = True
                response["result_file_content"] = result_text
                response["result_file_truncated"] = result_truncated
            except Exception as result_exc:
                response["result_file_found"] = False
                if debug:
                    response["result_file_error"] = str(result_exc)

            try:
                client.delete_path(sandbox_id, remote_dir, recursive=True)
                response["cleanup"]["remote_dir_deleted"] = True
            except Exception as cleanup_exc:
                response["cleanup"]["remote_dir_deleted"] = False
                if debug:
                    response["cleanup"]["remote_dir_error"] = str(cleanup_exc)

            if sandbox_id:
                try:
                    client.delete_sandbox(sandbox_id)
                    response["cleanup"]["sandbox_delete_requested"] = True
                except Exception as delete_exc:
                    response["cleanup"]["sandbox_delete_requested"] = False
                    if debug:
                        response["cleanup"]["sandbox_delete_error"] = str(delete_exc)
                finally:
                    sandbox_id = None

            return json.dumps(response, indent=2, ensure_ascii=False)

        except DaytonaHTTPError as exc:
            error_response: Dict[str, Any] = {
                "ok": False,
                "error_type": "DaytonaHTTPError",
                "error": str(exc),
                "cleanup": {
                    "remote_dir_deleted": False,
                    "sandbox_delete_requested": False,
                },
            }

            if sandbox_id:
                try:
                    client.delete_sandbox(sandbox_id)
                    error_response["cleanup"]["sandbox_delete_requested"] = True
                except Exception as delete_exc:
                    if debug:
                        error_response["cleanup"]["sandbox_delete_error"] = str(delete_exc)

            return json.dumps(error_response, indent=2, ensure_ascii=False)

        except Exception as exc:
            error_response = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "cleanup": {
                    "remote_dir_deleted": False,
                    "sandbox_delete_requested": False,
                },
            }

            if sandbox_id:
                try:
                    client.delete_sandbox(sandbox_id)
                    error_response["cleanup"]["sandbox_delete_requested"] = True
                except Exception as delete_exc:
                    if debug:
                        error_response["cleanup"]["sandbox_delete_error"] = str(delete_exc)

            return json.dumps(error_response, indent=2, ensure_ascii=False)
