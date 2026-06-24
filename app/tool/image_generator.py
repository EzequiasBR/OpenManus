import os
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx

from app.tool.base import BaseTool


class ImageGeneratorTool(BaseTool):
    name: str = "generate_image"
    description: str = (
        "Gera uma imagem ou desenho a partir de uma descrição textual. "
        "Use esta ferramenta sempre que o usuário pedir para desenhar, gerar imagem, "
        "criar ilustração, concept art, personagem, cena visual ou arte digital. "
        "Antes de chamar a ferramenta, transforme o pedido do usuário em um prompt visual "
        "detalhado, preferencialmente em inglês."
    )

    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "Prompt visual detalhado em inglês para geração da imagem. "
                    "Inclua composição, estilo, anatomia, perspectiva, iluminação, "
                    "qualidade visual e restrições negativas quando aplicável."
                ),
            }
        },
        "required": ["prompt"],
    }

    async def execute(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            return "Erro: o prompt de imagem está vazio."

        clean_prompt = prompt.strip()
        encoded_prompt = quote(clean_prompt)

        image_url = (
            f"https://gen.pollinations.ai/image/{encoded_prompt}"
            f"?width=1024&height=1024&nologo=true"
        )

        api_key = os.getenv("POLLINATIONS_API_KEY")
        if api_key:
            image_url += f"&key={quote(api_key)}"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(image_url)

            content_type = response.headers.get("content-type", "").lower()

            if response.status_code != 200:
                return (
                    "Falha ao gerar imagem. "
                    f"Status HTTP: {response.status_code}. "
                    f"Resposta: {response.text[:300]}"
                )

            if "image" not in content_type:
                return (
                    "Falha: o servidor não retornou uma imagem válida. "
                    f"Content-Type recebido: {content_type}. "
                    f"Resposta: {response.text[:300]}"
                )

            output_dir = Path("output_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            extension = ".jpg"
            if "png" in content_type:
                extension = ".png"
            elif "webp" in content_type:
                extension = ".webp"

            filename = output_dir / f"desenho_{uuid.uuid4().hex[:8]}{extension}"
            filename.write_bytes(response.content)

            safe_url = image_url
            if api_key:
                safe_url = safe_url.replace(api_key, "***REDACTED***")

            return (
                "Sucesso! Imagem gerada e salva localmente.\n"
                f"Caminho: {filename}\n"
                f"URL usada: {safe_url}"
            )

        except httpx.TimeoutException:
            return "Erro ao gerar imagem: timeout ao conectar com o backend de imagem."
        except httpx.HTTPError as e:
            return f"Erro HTTP ao gerar imagem: {type(e).__name__}: {str(e)}"
        except Exception as e:
            return f"Erro inesperado ao gerar imagem: {type(e).__name__}: {str(e)}"
