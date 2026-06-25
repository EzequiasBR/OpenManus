# IMAGE_PROVIDER_CAPABILITY_MAP_CURRENT_v0_1

## 1. Visão Geral

Este documento mapeia as capacidades reais do provider de imagem atualmente integrado ao OpenManus (`ImageGeneratorTool` → Pollinations.ai). O objetivo é estabelecer uma linha de base factual para futura integração com o contrato `SKILL_RESULT_TO_IMAGE_PROVIDER_FORMATTING_CONTRACT_v0_1.md`, permitindo que a LLM Formatting Layer e o Fidelity Gate operem com base em capacidades observadas — e não supostas.

Nenhuma linha de código foi alterada. Todas as afirmações abaixo são extraídas exclusivamente da leitura dos arquivos-fonte.

## 2. Arquivos Inspecionados

| Arquivo | O que prova |
|---|---|
| `app/tool/image_generator.py` | Implementação concreta da tool: provider, endpoint, parâmetros enviados, tratamento de resposta, saída |
| `app/tool/__init__.py` | Registro da tool como `ImageGeneratorTool` — exportada como parte do pacote |
| `app/agent/manus.py` | Uso da tool no agente: `ImageGeneratorTool()` é instanciado em `available_tools` (linha 42) |
| `app/tool/base.py` | Classe base `BaseTool` e `ToolResult` — formato de retorno padronizado |
| `app/prompt/manus.py` | Prompt do sistema — não menciona a tool de imagem especificamente; o agente decide o uso |
| `docs/SKILL_RESULT_TO_IMAGE_PROVIDER_FORMATTING_CONTRACT_v0_1.md` | Contrato-alvo: define o schema de capability map que este documento preenche |

## 3. Provider Atual Observado

### 3.1 Identificação

| Campo | Valor |
|---|---|
| Nome do provider | Pollinations.ai |
| Explicitação no código | Sim — URL hardcoded em `image_generator.py:43-46` |
| Endpoint | `https://gen.pollinations.ai/image/{encoded_prompt}?width=1024&height=1024&nologo=true` |
| Modelo interno | `unknown` — Pollinations.ai roteia para vários modelos internamente; não há parâmetro `model` |
| Chave de API | Opcional — lida de `POLLINATIONS_API_KEY` (linha 48); se presente, anexada como `&key=...` |

### 3.2 Modo de Chamada

| Aspecto | Observado |
|---|---|
| Protocolo | HTTP GET |
| Biblioteca | `httpx.AsyncClient` (linha 53) |
| Timeout | 120s (linha 53) |
| Formato do prompt | Texto puro, URL-encoded no path da URL (`urllib.parse.quote`) |
| Parâmetros adicionais | `width=1024`, `height=1024`, `nologo=true` — todos hardcoded |
| Método de chamada | Síncrono dentro de `async with` — uma única requisição GET, sem SDK |

### 3.3 Saída e Armazenamento

| Aspecto | Observado |
|---|---|
| Tipo de resposta esperada | Bytes de imagem (JPEG, PNG ou WebP, detectado por `content-type`) |
| Salva arquivo localmente | Sim — `output_images/desenho_{uuid_8hex}.{ext}` (linhas 72-82) |
| Diretório de saída | `output_images/` no diretório de trabalho |
| Metadados retornados ao agente | `Sucesso! Imagem gerada e salva localmente.\nCaminho: {filename}\nURL usada: {safe_url}` — string textual |
| Formato do valor de retorno | `str` (não `ToolResult` com `base64_image`) |

## 4. Capability Map Atual

### 4.1 Tabela de Capacidades

| Capacidade | Status | Evidência |
|---|---|---|
| `supports_prompt` | `supported` | Único parâmetro obrigatório; enviado via URL |
| `supports_negative_prompt` | `not_supported` | Não há campo separado; tudo fundido em `prompt` |
| `supports_width_height` | `not_supported` | `width=1024` e `height=1024` são hardcoded; a tool não aceita parâmetros do usuário |
| `supports_seed` | `not_supported` | Nenhum parâmetro `seed` no código |
| `supports_steps` | `not_supported` | Nenhum parâmetro `steps` no código |
| `supports_guidance` | `not_supported` | Nenhum parâmetro `cfg_scale` ou `guidance` |
| `supports_model_selection` | `not_supported` | Nenhum parâmetro `model` |
| `supports_style` | `not_supported` | Nenhum parâmetro de estilo separado |
| `supports_reference_image` | `not_supported` | Nenhum campo para imagem de referência |
| `supports_mask` | `not_supported` | Nenhum campo para máscara |
| `supports_inpainting` | `not_supported` | Nenhum campo para inpainting |
| `supports_structured_json` | `not_supported` | API espera apenas query params GET; não aceita JSON |
| `supports_metadata_response` | `not_supported` | Resposta é apenas bytes de imagem; não há metadados JSON |
| `supports_local_file_output` | `supported` | `write_bytes` salva em `output_images/` |
| `max_prompt_chars` | `unknown` | Pollinations.ai não documenta limite no código; não há validação de tamanho |

### 4.2 Observações sobre `not_supported`

- `width` e `height` são **enviados** com valores fixos (1024x1024), mas a **tool não permite que o usuário os controle**. Por isso foram marcados como `not_supported` — a capacidade de controle não existe, apenas o valor hardcoded.
- Caso o provider Pollinations.ai processe `negative_prompt`, `seed` ou `steps` embutidos no texto do prompt, isso é uma característica do modelo, não da API — e portanto não contabilizado como suporte da tool.

## 5. Payload Atual

### 5.1 O que a tool recebe

```json
{
  "prompt": "string — texto livre, de preferência em inglês"
}
```

### 5.2 O que a tool envia (URL construída)

```
GET https://gen.pollinations.ai/image/{url_encoded_prompt}?width=1024&height=1024&nologo=true[&key={api_key}]
```

| Parâmetro HTTP | Origem | Mutável? |
|---|---|---|
| `{prompt}` (path) | Parâmetro `prompt` da tool | Sim |
| `width` | Hardcoded (1024) | Não |
| `height` | Hardcoded (1024) | Não |
| `nologo` | Hardcoded (true) | Não |
| `key` | Env var `POLLINATIONS_API_KEY` | Indiretamente |

### 5.3 Campos ausentes no payload atual

Todos os campos do contrato `Provider Capability Map` que não estão listados acima (negative_prompt, seed, steps, guidance, model, style, reference_image, mask, structured_json) estão **ausentes** do payload enviado. A ferramenta simplesmente não os constrói.

## 6. Output Atual

### 6.1 Fluxo de saída

```
Requisição HTTP GET
  → resposta com status 200 e content-type image/*
  → response.content (bytes)
  → output_images/desenho_{uuid}.{ext}
  → string textual: "Sucesso! Imagem gerada e salva localmente.\nCaminho: ...\nURL usada: ..."
```

### 6.2 Formato do retorno

```python
# Assinatura real:
async def execute(self, prompt: str) -> str:
    ...
    return "Sucesso! Imagem gerada e salva localmente.\nCaminho: ...\nURL usada: ..."

# Ou em caso de erro:
return "Erro: ..."
return "Falha ao gerar imagem. Status HTTP: ..."
return "Falha: o servidor não retornou uma imagem válida. ..."
return "Erro ao gerar imagem: timeout ..."
return "Erro HTTP ao gerar imagem: ..."
return "Erro inesperado ao gerar imagem: ..."
```

### 6.3 Observações importantes

- O retorno é uma **string**, não um `ToolResult` com `base64_image` preenchido.
- A classe base `ToolResult` (em `base.py`) possui campo `base64_image: Optional[str]`, mas a tool atual não o utiliza.
- Não há metadados da API no retorno — apenas o caminho do arquivo e a URL usada.
- A URL original é redactada se houver `api_key` (substituída por `***REDACTED***`).

## 7. Compatibilidade com o Novo Contrato

Análise de como o `Skill Result Canonical` (definido no contrato v0.1) pode ser mapeado para o provider atual.

### 7.1 Campos que podem ir diretamente para `prompt`

| Campo Canonical | Compatível? | Estratégia |
|---|---|---|
| `visual_intent` | Sim | Primeira frase do prompt |
| `required_elements[].description` | Sim | Concatenado no prompt |
| `composition_requirements.layout` | Sim | Texto descritivo no prompt |
| `style_requirements` | Sim | Texto descritivo no prompt |
| `materials` | Sim | Texto descritivo no prompt |
| `perspective` | Sim | Texto descritivo no prompt |
| `anatomy_construction` | Sim | Texto descritivo no prompt |
| `subject` | Sim | Texto descritivo no prompt |

### 7.2 Campos que precisam ser compactados pela IA de linguagem

| Campo Canonical | Motivo da compactação |
|---|---|
| `required_elements` (múltiplos) | Limite de caracteres desconhecido; pode precisar priorizar por `priority_map` |
| `validation_criteria` | Não é conteúdo visual; deve ser armazenado para pós-geração, não no prompt |

### 7.3 Campos que precisam virar texto porque o provider não tem campo próprio

| Campo Canonical | Transformação necessária |
|---|---|
| `forbidden_elements` | Incluído no prompt como negação textual: "without X, no Y" |
| `constraints` (formato, resolução) | Via texto (ex: "square format, high resolution") — `width`/`height` são fixos |

### 7.4 Campos que devem gerar `loss_report`

| Campo Canonical | Motivo do `loss_report` |
|---|---|
| `forbidden_elements` (todos) | Provider não tem `negative_prompt`; negação textual é menos precisa |
| `composition_requirements` com `critical` | Se exceder limite de caracteres, perda de fidelidade |
| `constraints.width` / `constraints.height` | Provider usa valores fixos 1024x1024; qualquer outra proporção é perdida |

## 8. Riscos e Limitações

### 8.1 Ausência de `negative_prompt`

Todo conteúdo de `forbidden_elements` precisa ser expresso como negação textual dentro do prompt positivo. Modelos de geração interpretam negação textual de forma imprecisa — o risco de o erro proibido ainda aparecer é **moderado a alto**.

### 8.2 Ausência de `seed`

Não é possível reproduzir uma imagem exata. Qualquer regereração pode produzir resultado diferente. Isso afeta `validation_targets` que dependem de comparabilidade.

### 8.3 Ausência de `steps` e `guidance`

A tool não tem controle sobre qualidade/estilo via parâmetros numéricos. A LLM Formatting Layer não pode ajustar detalhismo ou aderência ao prompt. Tudo depende do modelo interno escolhido pelo Pollinations.ai.

### 8.4 Limite de prompt desconhecido

O código não documenta o limite máximo de caracteres do prompt para Pollinations.ai. Se o prompt exceder o limite, o comportamento é imprevisível (truncamento silencioso ou erro HTTP). Isso é um **risco alto** para skills que produzem muitos `required_elements`.

### 8.5 Retorno sem metadados

A API retorna apenas bytes de imagem. Não há informações sobre seed usado, modelo, tempo de inferência, NSFW filtering, ou razão de falha. Isso limita a capacidade de auditoria do Fidelity Gate pós-geração.

### 8.6 Perda de fidelidade quando tudo vira prompt único

Este é o risco central: um `Skill Result Canonical` com dezenas de requisitos, restrições, prioridades e erros proibidos precisa ser achatado em uma única string de prompt. A compressão inevitável da LLM Formatting Layer pode:
- Omitir requisitos de baixa prioridade.
- Suavizar erros proibidos.
- Perder nuances de composição.

O Fidelity Gate deve sinalizar esses casos como `passed_with_warnings` ou `blocked`.

### 8.7 Comportamento interno do provider desconhecido

Pollinations.ai é um agregador que roteia para múltiplos modelos. O modelo real usado pode mudar sem aviso. Imagens geradas em momentos diferentes podem ter estilos diferentes para o mesmo prompt. Isso fragiliza qualquer validação visual repetível.

## 9. Decisão Técnica

> O provider atual (Pollinations.ai via HTTP GET) deve ser tratado como target inicial de baixa capacidade. O LLM Formatting Layer deve preservar o máximo de requisitos no prompt textual e o Fidelity Gate deve registrar limitações quando a API não suportar campos separados. A ausência de `negative_prompt`, `seed`, `steps`, `guidance` e limite de caracteres conhecido são restrições arquiteturais que o contrato v0.1 já prevê, e o `loss_report` é o mecanismo para registrar essas perdas sem bloquear o fluxo.

## 10. Próximas Fases

| Fase | Descrição |
|---|---|
| **Fase A** | Criar schema JSON do capability map (basear no exemplo do contrato v0.1, preenchendo com valores deste documento) |
| **Fase B** | Criar teste unitário para carregar e validar o capability map contra o schema |
| **Fase C** | Criar Fidelity Gate mínimo que valide payload antes do envio (FG-01 a FG-06 do contrato) |
| **Fase D** | Adaptar `ImageGeneratorTool` para receber payload formatado da LLM Formatting Layer, mantendo compatibilidade com chamadas legadas (só `prompt`) |
| **Fase E** | Adicionar suporte a metadados de saída: salvar `seed`, `model`, `loss_report` junto com a imagem em `output_images/` |
| **Fase F** | Suportar providers mais ricos (SD WebUI, DALL-E, Imagen) com capability maps separados |

---

*Este documento é uma auditoria factual. Nenhuma inferência sobre comportamento não observado foi registrada como fato. Campos marcados como `unknown` ou `not_supported` devem ser reavaliados quando o provider for alterado ou atualizado.*
