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
        image: str = "debian:12.9",
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
