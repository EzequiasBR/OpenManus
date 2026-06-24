import os
from typing import Any, Dict, Optional

import httpx


class DaytonaHTTPError(RuntimeError):
    """Erro controlado para falhas na API HTTP da Daytona."""


class DaytonaHTTPClient:
    """
    Cliente HTTP mínimo para Daytona API.

    Este cliente não usa o SDK Python da Daytona.
    Isso evita conflitos de dependências com o OpenManus.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://app.daytona.io/api",
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DAYTONA_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.organization_id = organization_id or os.getenv("DAYTONA_ORGANIZATION_ID")

        if not self.api_key:
            raise DaytonaHTTPError("DAYTONA_API_KEY não está definida no ambiente.")

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.organization_id:
            headers["X-Daytona-Organization-ID"] = self.organization_id

        return headers

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                )
        except httpx.TimeoutException as exc:
            raise DaytonaHTTPError(f"Timeout ao chamar Daytona API: {method} {path}") from exc
        except httpx.HTTPError as exc:
            raise DaytonaHTTPError(f"Erro HTTP ao chamar Daytona API: {type(exc).__name__}: {exc}") from exc

        if response.status_code < 200 or response.status_code >= 300:
            body = response.text[:1000]
            raise DaytonaHTTPError(
                f"Daytona API retornou status {response.status_code} em {method} {path}: {body}"
            )

        if not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise DaytonaHTTPError(
                f"Daytona API retornou resposta não JSON em {method} {path}: {response.text[:500]}"
            ) from exc

    @staticmethod
    def mask_secret(value: str) -> str:
        if not value:
            return ""

        if len(value) <= 8:
            return "*" * len(value)

        return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"

    def validate_key(self) -> Dict[str, Any]:
        """
        Valida a API key atual.

        Endpoint:
        GET /api-keys/current
        """
        data = self._request("GET", "/api-keys/current")

        if "value" in data:
            data["value"] = self.mask_secret(str(data["value"]))

        return data

    def list_sandboxes(self) -> Dict[str, Any]:
        """
        Lista sandboxes acessíveis pela chave atual.

        Endpoint:
        GET /sandbox
        """
        return self._request("GET", "/sandbox")

    def create_sandbox(
        self,
        name: str,
        image: str = "mcr.microsoft.com/devcontainers/base:ubuntu-22.04",
        language: str = "python",
        cpu: int = 1,
        memory: int = 1,
        disk: int = 3,
        auto_stop_interval: int = 10,
        auto_delete_interval: int = 60,
    ) -> Dict[str, Any]:
        """
        Cria uma sandbox Daytona pequena e descartável a partir de uma imagem Docker pública.

        Importante:
        - Usamos 'image', não 'snapshot'.
        - Snapshot exige um snapshot já existente/ativo na conta Daytona.
        - Com image, a Daytona cria/usa snapshot derivado da imagem.

        Endpoint:
        POST /sandbox
        """
        if not name or not name.strip():
            raise DaytonaHTTPError("Nome da sandbox não pode estar vazio.")

        payload = {
            "name": name.strip(),
            "image": image,
            "language": language,
            "resources": {
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
            },
            "public": False,
            "networkBlockAll": False,
            "autoStopInterval": auto_stop_interval,
            "autoDeleteInterval": auto_delete_interval,
            "labels": {
                "source": "openmanus-local",
                "purpose": "daytona-http-test",
            },
            "envVars": {},
        }

        return self._request("POST", "/sandbox", json=payload)


    def get_sandbox(self, sandbox_id_or_name: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Consulta detalhes de uma sandbox.

        Endpoint:
        GET /sandbox/{sandboxIdOrName}
        """
        if not sandbox_id_or_name or not sandbox_id_or_name.strip():
            raise DaytonaHTTPError("sandbox_id_or_name não pode estar vazio.")

        return self._request(
            "GET",
            f"/sandbox/{sandbox_id_or_name.strip()}",
            params={"verbose": verbose},
        )

    def delete_sandbox(self, sandbox_id_or_name: str) -> Dict[str, Any]:
        """
        Deleta uma sandbox.

        Endpoint:
        DELETE /sandbox/{sandboxIdOrName}
        """
        if not sandbox_id_or_name or not sandbox_id_or_name.strip():
            raise DaytonaHTTPError("sandbox_id_or_name não pode estar vazio.")

        return self._request("DELETE", f"/sandbox/{sandbox_id_or_name.strip()}")

    def _toolbox_request(
        self,
        sandbox_id: str,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Chama a Toolbox API de uma sandbox específica.

        URL base:
        https://proxy.app.daytona.io/toolbox/{sandboxId}/toolbox
        """
        if not sandbox_id or not sandbox_id.strip():
            raise DaytonaHTTPError("sandbox_id não pode estar vazio.")

        toolbox_base_url = "https://proxy.app.daytona.io/toolbox"
        url = f"{toolbox_base_url}/{sandbox_id.strip()}{path}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                )
        except httpx.TimeoutException as exc:
            raise DaytonaHTTPError(
                f"Timeout ao chamar Daytona Toolbox API: {method} {path}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DaytonaHTTPError(
                f"Erro HTTP ao chamar Daytona Toolbox API: {type(exc).__name__}: {exc}"
            ) from exc

        if response.status_code < 200 or response.status_code >= 300:
            body = response.text[:1000]
            raise DaytonaHTTPError(
                f"Daytona Toolbox API retornou status {response.status_code} "
                f"em {method} {path}: {body}"
            )

        if not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise DaytonaHTTPError(
                f"Daytona Toolbox API retornou resposta não JSON em "
                f"{method} {path}: {response.text[:500]}"
            ) from exc

    def execute_command(
        self,
        sandbox_id: str,
        command: str,
        cwd: str = "/home/daytona",
        env: Optional[Dict[str, str]] = None,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """
        Executa um comando stateless dentro da sandbox.

        Endpoint:
        POST /process/execute

        A API Daytona espera 'command' como string.
        """
        if not command or not command.strip():
            raise DaytonaHTTPError("command não pode estar vazio.")

        payload = {
            "command": command.strip(),
            "cwd": cwd,
            "env": env or {"PYTHONUNBUFFERED": "1"},
            "timeout": timeout,
        }

        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="POST",
            path="/process/execute",
            json=payload,
        )

    def create_folder(
        self,
        sandbox_id: str,
        path: str,
        mode: str = "755",
    ) -> Dict[str, Any]:
        """
        Cria uma pasta dentro da sandbox.

        Endpoint:
        POST /files/folder?path=...
        """
        if not path or not path.strip():
            raise DaytonaHTTPError("path não pode estar vazio.")

        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="POST",
            path="/files/folder",
            params={"path": path.strip()},
            json={"mode": mode},
        )

    def upload_file(
        self,
        sandbox_id: str,
        remote_path: str,
        content: bytes,
        filename: str = "upload.bin",
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        """
        Envia um arquivo para a sandbox.

        Endpoint:
        POST /files/upload?path=...

        Contrato validado:
        - multipart/form-data
        - campo: file
        """
        if not sandbox_id or not sandbox_id.strip():
            raise DaytonaHTTPError("sandbox_id não pode estar vazio.")

        if not remote_path or not remote_path.strip():
            raise DaytonaHTTPError("remote_path não pode estar vazio.")

        if content is None:
            raise DaytonaHTTPError("content não pode ser None.")

        toolbox_base_url = "https://proxy.app.daytona.io/toolbox"
        url = f"{toolbox_base_url}/{sandbox_id.strip()}/files/upload"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    params={"path": remote_path.strip()},
                    files={
                        "file": (filename, content, content_type),
                    },
                )
        except httpx.TimeoutException as exc:
            raise DaytonaHTTPError("Timeout ao enviar arquivo para Daytona.") from exc
        except httpx.HTTPError as exc:
            raise DaytonaHTTPError(
                f"Erro HTTP ao enviar arquivo: {type(exc).__name__}: {exc}"
            ) from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise DaytonaHTTPError(
                f"Daytona File Upload retornou status {response.status_code}: "
                f"{response.text[:1000]}"
            )

        if not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def download_file(
        self,
        sandbox_id: str,
        remote_path: str,
    ) -> bytes:
        """
        Baixa um arquivo da sandbox.

        Endpoint:
        GET /files/download?path=...
        """
        if not remote_path or not remote_path.strip():
            raise DaytonaHTTPError("remote_path não pode estar vazio.")

        toolbox_base_url = "https://proxy.app.daytona.io/toolbox"
        url = f"{toolbox_base_url}/{sandbox_id.strip()}/files/download"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers=self._headers(),
                    params={"path": remote_path.strip()},
                )
        except httpx.TimeoutException as exc:
            raise DaytonaHTTPError("Timeout ao baixar arquivo da Daytona.") from exc
        except httpx.HTTPError as exc:
            raise DaytonaHTTPError(
                f"Erro HTTP ao baixar arquivo: {type(exc).__name__}: {exc}"
            ) from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise DaytonaHTTPError(
                f"Daytona File Download retornou status {response.status_code}: "
                f"{response.text[:1000]}"
            )

        return response.content

    def file_info(
        self,
        sandbox_id: str,
        remote_path: str,
    ) -> Dict[str, Any]:
        """
        Obtém metadados de um arquivo/pasta dentro da sandbox.

        Endpoint:
        GET /files/info?path=...
        """
        if not remote_path or not remote_path.strip():
            raise DaytonaHTTPError("remote_path não pode estar vazio.")

        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="GET",
            path="/files/info",
            params={"path": remote_path.strip()},
        )

    def delete_path(
        self,
        sandbox_id: str,
        remote_path: str,
        recursive: bool = False,
    ) -> Dict[str, Any]:
        """
        Remove arquivo ou pasta dentro da sandbox.

        Endpoint:
        DELETE /files?path=...&recursive=...
        """
        if not remote_path or not remote_path.strip():
            raise DaytonaHTTPError("remote_path não pode estar vazio.")

        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="DELETE",
            path="/files",
            params={
                "path": remote_path.strip(),
                "recursive": str(recursive).lower(),
            },
        )

    def get_project_dir(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Obtém o diretório raiz do projeto dentro da sandbox.

        Endpoint:
        GET /toolbox/{sandboxId}/toolbox/project-dir
        """
        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="GET",
            path="/project-dir",
        )

    def get_user_home_dir(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Obtém o diretório home do usuário dentro da sandbox.

        Endpoint:
        GET /toolbox/{sandboxId}/toolbox/user-home-dir
        """
        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="GET",
            path="/user-home-dir",
        )

    def get_work_dir(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Obtém o diretório padrão de trabalho dentro da sandbox.

        Endpoint:
        GET /toolbox/{sandboxId}/toolbox/work-dir
        """
        return self._toolbox_request(
            sandbox_id=sandbox_id,
            method="GET",
            path="/work-dir",
        )
