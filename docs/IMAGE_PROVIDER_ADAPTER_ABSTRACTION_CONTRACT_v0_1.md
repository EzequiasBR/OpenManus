# IMAGE_PROVIDER_ADAPTER_ABSTRACTION_CONTRACT_v0_1

## 1. Visão Geral

Este contrato define uma camada comum de adapter para diferentes APIs de geração de imagem. O objetivo é permitir que o projeto suporte qualquer provider de imagem (Pollinations.ai, DALL-E, Stable Diffusion, Imagen, ComfyUI, etc.) sem que a troca de API quebre a skill, a LLM Formatting Layer ou o Fidelity Gate.

A abstração separa:

- O que o sistema quer (prompt + parâmetros semânticos).
- O que o provider aceita (capability map).
- Como o adapter converte entre os dois.
- Como o resultado é normalizado independente da API.

Nenhuma linha de código foi alterada. Nenhum schema ou config foi criado. Nenhuma API real foi chamada.

## 2. Problema que Resolve

Cada API de imagem aceita um conjunto diferente de campos:

| Provider | Aceita negative_prompt | Aceita seed | Aceita mask | Aceita reference image | Formato |
|---|---|---|---|---|---|
| Pollinations.ai (GET) | Não | Sim (model-dependent) | Não | Sim (model-dependent) | Query params |
| Pollinations.ai (POST) | Não | Sim (model-dependent) | Não | Sim | JSON |
| DALL-E 3 | Não | Não | Não | Não | JSON |
| Stable Diffusion WebUI | Sim | Sim | Sim | Sim | JSON |
| Imagen | Não | Não | Não | Não | JSON |
| ComfyUI (local) | Depende do workflow | Depende do workflow | Sim | Sim | Workflow JSON |

Sem uma abstração:

- Cada troca de API quebra a skill e o pipeline.
- A LLM Formatting Layer precisaria conhecer cada API individualmente.
- O Fidelity Gate não teria um formato de resultado padronizado para validar.
- O sistema ficaria preso a um único provider.

O adapter genérico resolve isso definindo um contrato de interface que todo provider específico deve implementar, mantendo o resto do pipeline isolado da API real.

## 3. Decisão Arquitetural Congelada

> O sistema depende de um contrato comum de provider, não de uma API específica.

Consequências desta decisão:

- A LLM Formatting Layer formata para o contrato, não para uma API.
- O capability map traduz o contrato para cada provider.
- O adapter específico implementa a conversão final.
- Trocar de provider = criar novo adapter + capability map. Não alterar skills, LLM Formatting Layer ou Fidelity Gate.
- Um provider pode ter múltiplos endpoints (GET, POST) — cada modo vira um caminho no adapter, não um adapter novo.

Esta decisão é irreversível para o escopo da v0.1. Qualquer proposta que acople o pipeline a um provider específico está fora do contrato.

## 4. Fluxo Geral

```
Skill (ex: wireframing, ui-design)
  │
  ▼
Skill Result Canonical (documento técnico estruturado)
  │
  ▼
LLM Formatting Layer (IA de linguagem natural)
  │
  ├── Provider Registry (resolvedor: provider_id → capability map + policy + adapter)
  │
  ▼
Provider Capability Map (o que o provider suporta)
  │
  ▼
Provider Formatting Policy (como formatar para este provider)
  │
  ▼
FormattedPacket (payload normalizado — provider-agnostic)
  │
  ▼
Provider Request Packet (payload específico do provider — após validação de capability)
  │
  ▼
Provider Adapter específico (ex: PollinationsAdapter, DallEAdapter)
  │
  ├── format_request()       ── converte Request Packet → requisição HTTP real
  ├── send()                 ── executa chamada HTTP/API
  ├── parse_response()       ── converte resposta bruta → resultado normalizado
  │
  ▼
API de imagem externa (Pollinations, OpenAI, Stability, local)
  │
  ▼
Normalized Image Result (formato comum de saída)
  │
  ▼
Fidelity Gate / Result Validation
  │
  ▼
Loss Report (perdas registradas durante o fluxo)
```

Cada seta representa uma transformação com responsabilidade bem definida. Nenhuma camada invade a responsabilidade da outra.

## 5. Responsabilidades de Cada Camada

### Skill

- Produzir `SkillResultCanonical` com descrição técnica do que gerar.
- **Não sabe** que API será usada.
- **Não formata** prompt.
- **Não decide** parâmetros técnicos.

### LLM Formatting Layer

- Ler o `SkillResultCanonical`.
- Consultar o `ProviderCapabilityMap` do provider selecionado.
- Aplicar a `ProviderFormattingPolicy`.
- Produzir um pacote formatado no formato do contrato genérico.
- Gerar `loss_report` para campos que não puderam ser representados.

### Capability Map

- Declarar o que o provider suporta: campos, valores, limites, modos.
- Informar `unsupported_fields_policy` (ignore, warn, block).
- Listar modelos disponíveis e suas capacidades individuais.
- Ser um arquivo de configuração, não código.

### Formatting Policy

- Regras de como achatar ou preservar campos para cada tipo de provider.
- Exemplo: provider sem `negative_prompt` → incorporar ao prompt como negação textual.
- Exemplo: provider com suporte a seed → passar seed diretamente.

### Generic Provider Adapter (este contrato)

- Contrato de interface que todo adapter específico implementa.
- Normalizar payload de entrada e saída.
- Validar capacidades antes de enviar.
- Garantir que o resultado siga o `NormalizedImageResult`.

### Provider Adapter específico

- Implementar a interface do adapter genérico.
- Conhecer os detalhes do provider específico (endpoint, auth, formato).
- Executar a chamada HTTP/API real.
- Converter a resposta bruta para `NormalizedImageResult`.

### API externa

- Serviço real de geração de imagem (Pollinations, OpenAI, ComfyUI).
- Retornar imagem + metadados (ou apenas imagem).

### Fidelity Gate

- Validar que o payload formatado preserva requisitos críticos da skill.
- Validar que o resultado normalizado contém os campos esperados.
- Aprovar, bloquear ou emitir警告.

### Loss Report

- Registrar toda perda de fidelidade durante o fluxo.
- Diferenciar perda por falta de suporte da API vs erro de formatação.
- Alimentar auditoria e rastreabilidade.

### Provider Registry

- Manter um catálogo de todos os providers disponíveis.
- Resolver `provider_id` para capability map, formatting policy e adapter específico.
- Permitir que a LLM Formatting Layer selecione o provider sem conhecer classes ou implementações.
- Expôr metadados de cada provider (versão, status, modo de endpoint suportado).
- Ser o ponto único de registro quando um novo provider é adicionado (ver seção 19).

## 6. Provider Registry

### Problema que resolve

Hoje a LLM Formatting Layer precisaria saber qual classe de adapter usar para cada provider. Isso acopla a formatação semântica à implementação técnica. O Provider Registry resolve isso de forma declarativa:

```yaml
provider: pollinations
```

O registry resolve automaticamente:

```
pollinations
  ├── capability_map:     configs/providers/pollinations_api_v0_1.json
  ├── formatting_policy:  configs/providers/pollinations_policy.json
  └── adapter:            PollinationsAdapter
```

A LLM nunca conhece nomes de classe. Ela apenas declara o `provider_id` no pacote formatado.

### O que o Registry contém

| Campo | Descrição |
|---|---|
| `provider_id` | Identificador único (ex: `pollinations`, `dall-e-3`, `comfyui`) |
| `display_name` | Nome legível (ex: "Pollinations.ai", "DALL-E 3") |
| `provider_version` | Versão da API do provider |
| `adapter_contract_version` | Versão do contrato de adapter que este provider implementa |
| `capability_map_path` | Caminho para o arquivo de capability map |
| `formatting_policy_path` | Caminho para o arquivo de política de formatação |
| `adapter_module` | Referência ao módulo/classe do adapter específico |
| `status` | `active`, `deprecated`, `experimental` |
| `supported_endpoint_modes` | Modos de endpoint disponíveis |
| `auth_required` | Se requer autenticação |
| `default_model` | Modelo padrão, se aplicável |

### Fluxo de resolução

```text
LLM Formatting Layer
  │  "provider": "pollinations"
  ▼
Provider Registry
  │
  ├── 1. Lookup: provider_id → metadata
  ├── 2. Load:   capability_map.json
  ├── 3. Load:   formatting_policy.json
  ├── 4. Bind:   adapter class
  │
  ▼
Adapter pipeline (capability map + policy + adapter prontos para uso)
```

### Registry como camada de swap

Para trocar um provider:

1. Manter o `provider_id` no banco de dados ou config.
2. O registry resolve para o novo capability map e adapter.
3. A LLM Formatting Layer não precisa ser alterada.

Exemplo: trocar de `pollinations` para `dall-e-3`:

```yaml
# Antes
provider: pollinations
# → registry resolve: pollinations_capability.json + PollinationsAdapter

# Depois
provider: dall-e-3
# → registry resolve: dalle_capability.json + DallEAdapter
```

### Registry e versionamento

O registry também armazena versões de contrato, permitindo auditoria:

```yaml
adapter_contract_version: "0.1.0"
capability_map_version: "0.1.0"
formatting_policy_version: "0.1.0"
```

Isso garante que qualquer geração futura pode responder:

> "Esta imagem foi produzida usando qual versão do contrato?"

### Registry não é um serviço — é uma configuração

O Provider Registry não precisa ser um microsserviço ou banco de dados. Pode ser:

- Um diretório de arquivos de configuração.
- Um dicionário em memória.
- Um arquivo YAML/JSON de registro.
- Uma entrada em banco de dados.

O importante é o contrato de resolução, não a implementação.

## 7. O que o Adapter Genérico É

O adapter genérico é:

### Contrato de interface

Define os métodos que todo adapter específico deve implementar. Não é uma classe concreta — é um contrato que pode ser implementado como classe abstrata, protocolo, trait, ou modulo, conforme a linguagem do projeto.

### Normalizador de payload

Converte o payload formatado pela LLM (provider-agnostic) no formato exato que o provider espera. Se o provider espera `width` + `height` como integers, o adapter separa. Se espera `size` como string "1024x1024", o adapter junta.

### Validador de capability

Antes de enviar, o adapter verifica se o payload respeita o capability map. Campos não suportados são tratados conforme `unsupported_fields_policy` (ignorados, geram warning, ou bloqueiam).

### Padronizador de resposta

Converte a resposta bruta da API (bytes, JSON, URL) em um `NormalizedImageResult` com campos consistentes independente do provider.

### Camada de erro

Traduz erros específicos do provider (HTTP 402, 429, 502, timeout, parse failure) para códigos de erro padronizados.

### Ponto de troca de provider

O resto do sistema não precisa mudar quando um provider é trocado. Apenas o adapter específico e o capability map mudam.

## 8. O que o Adapter Genérico Não É

| O adapter genérico NÃO é | Motivo |
|---|---|
| **Skill** | Não produz conteúdo visual. Não decide o que gerar. |
| **LLM** | Não estrutura prompt. Não decide como organizar requisitos. |
| **Provider específico** | Não implementa lógica de API específica. É o contrato que providers específicos implementam. |
| **Prompt engineer** | Não inventa prompt. Não melhora prompt. Não traduz estilo para linguagem de prompt. |
| **Validador visual final** | Não verifica se a imagem gerada está correta visualmente. Isso é responsabilidade do Fidelity Gate pós-geração. |
| **Lugar para inventar conteúdo** | Não adiciona elementos visuais que não vieram da skill. |
| **Lugar para ignorar requisitos críticos** | Não pode descartar `immutable_requirements` ou `forbidden_elements` críticos. Se o provider não suporta, deve gerar `loss_report` com `decision: block`. |

## 9. Contrato Conceitual da Interface

O adapter genérico expõe os seguintes métodos conceituais. Nenhum código será implementado neste documento — apenas a descrição do contrato.

### `provider_id() → str`

Retorna o identificador único do provider (ex: `"pollinations"`, `"dall-e-3"`, `"comfyui"`).

### `load_capabilities() → CapabilityMap`

Carrega o capability map do provider. Pode ser de um arquivo de configuração, de uma variável de ambiente, ou de um registro central.

### `validate_capabilities(packet: FormattedPacket) → ValidationResult`

Verifica se o pacote formatado pela LLM é compatível com o capability map do provider. Cada campo do pacote é verificado contra o capability map:

- Campo suportado → ok.
- Campo não suportado com policy `ignore` → removido, registrado em loss_report.
- Campo não suportado com policy `warn` → removido, loss_report com `send_with_warning`.
- Campo não suportado com policy `block` → bloqueia envio, loss_report com `block`.

### `format_payload(packet: FormattedPacket, capabilities: CapabilityMap) → ProviderPayload`

Converte o pacote normalizado no formato exato que o provider espera. Exemplos:

- Provider GET: monta URL com query params.
- Provider POST JSON: monta dicionário/JSON.
- Provider multipart: monta form data com arquivos.
- Provider local workflow: monta JSON de workflow.

### `validate_payload(payload: ProviderPayload) → PayloadValidationResult`

Validações finais antes do envio:

- Campos obrigatórios presentes.
- Limites de tamanho respeitados (ex: max_prompt_chars).
- Formato de campos correto (ex: seed dentro do range).
- Autenticação configurada.

### `send(payload: ProviderPayload) → RawResponse`

Executa a chamada HTTP/API. Gerencia:

- Timeout.
- Retry (se configurado).
- Autenticação (Bearer, query key, api key header).
- Headers específicos.

### `parse_response(raw_response: RawResponse) → ParsedResponse`

Converte a resposta bruta da API em uma estrutura intermediária:

- Bytes de imagem → extrai mime type, tamanho, hash.
- JSON com URL → baixa a imagem ou registra URL.
- JSON com base64 → decodifica.
- Erro HTTP → traduz para código padronizado.

### `normalize_result(response: ParsedResponse) → NormalizedImageResult`

Converte a resposta parseada no formato padronizado do contrato (seção 13). Garante que todo resultado siga a mesma estrutura independente do provider.

### `build_loss_report(packet: FormattedPacket, payload: ProviderPayload, capabilities: CapabilityMap) → LossReport`

Compila todas as perdas identificadas durante o fluxo:

- Campos do pacote original que não foram para o payload final.
- Campos convertidos (ex: negative_prompt → texto no prompt).
- Campos descartados por falta de suporte.
- Avisos sobre limites ultrapassados.

### `report_provider_error(error: ProviderError) → NormalizedError`

Traduz erros específicos do provider para códigos padronizados (seção 17). Inclui:

- Código do erro.
- Mensagem legível.
- Sugestão de ação (retry, mudar provider, ajustar payload).
- Metadados do erro (status HTTP, response body, timestamp).

## 10. Provider Capability Map Contract

Todo provider deve declarar um capability map com os seguintes campos conceituais:

### provider_id

Identificador único do provider. Ex: `"pollinations"`, `"dall-e-3"`, `"stable-diffusion-webui"`, `"comfyui"`.

### provider_version

Versão do provider ou da API. Ex: `"0.3.0"`, `"1.7.0"`, `"latest"`.

### endpoint_modes

Lista de modos de endpoint que o provider suporta (ver seção 11). Ex: `["text_to_image_get", "text_to_image_post_json"]`.

### auth_modes

Modos de autenticação suportados. Ex: `["bearer", "query_key", "none"]`.

### input_capabilities

Campos de entrada que o provider suporta, com limites:

| Campo conceitual | Tipo | Limites |
|---|---|---|
| `prompt` | boolean + max_chars | Limite de caracteres |
| `negative_prompt` | boolean + max_chars | Se suporta e limite |
| `model` | boolean + list | Lista de modelos ou "dynamic" |
| `width` | boolean + min/max/multiple_of | Resolução |
| `height` | boolean + min/max/multiple_of | Resolução |
| `size` | boolean + format | Formato WIDTHxHEIGHT |
| `seed` | boolean + min/max | Range |
| `n` | boolean + max | Máximo de imagens |
| `quality` | boolean + values | Valores aceitos |
| `guidance` | boolean + min/max | Range |
| `steps` | boolean + min/max | Range |
| `reference_images` | boolean + max | Máximo de imagens de referência |
| `mask` | boolean | Suporte a máscara |
| `safe` | boolean + values | Valores de safety |

### output_capabilities

Campos de saída que o provider retorna:

| Campo conceitual | Descrição |
|---|---|
| `response_format` | url, b64_json, binary, file |
| `metadata` | created, seed_used, model_used, revised_prompt |
| `content_types` | image/jpeg, image/png, image/webp |

### safety_capabilities

Capacidades de segurança:

| Campo | Descrição |
|---|---|
| `safe` | boolean — suporta filtro de conteúdo |
| `safe_values` | Lista de valores aceitos |
| `content_filter` | boolean — retorna resultados de filtro |
| `auth_required` | boolean — requer autenticação |

### unsupported_fields_policy

Política para campos não suportados:

| Valor | Comportamento |
|---|---|
| `ignore` | Remove campo silenciosamente, registra loss_report informativo |
| `warn` | Remove campo, loss_report com send_with_warning |
| `block` | Bloqueia envio, loss_report com block |

### model_capabilities

Para providers com múltiplos modelos, pode declarar capacidades por modelo:

```text
model_capabilities:
  flux:
    supports_seed: true
    supports_reference_image: false
  gptimage:
    supports_seed: false
    supports_reference_image: true
    supports_quality: true
```

Modelos não listados herdam os defaults do capability map principal.

### capability_map_version

Versão semântica do capability map. Deve ser incrementada quando campos são adicionados, removidos ou alterados.

Ex: `"0.1.0"`, `"1.0.0"`.

### formatting_policy_version

Versão semântica da política de formatação associada. Independe da versão do capability map — a política pode mudar sem que as capacidades do provider mudem.

Ex: `"0.1.0"`.

### adapter_contract_version

Versão do contrato de adapter que este provider implementa. Permite verificar compatibilidade entre o adapter e o capability map.

Ex: `"0.1.0"`.

### known_limitations

Lista de limitações conhecidas não capturadas pelos campos acima. Ex:

- Prompt GET limitado por URL.
- Multi-image não suportado atualmente.
- Metadados de geração não expostos.

### validation_policy

Regras de validação adicionais:

| Campo | Descrição |
|---|---|
| `required_fields` | Campos obrigatórios sempre |
| `conditional_required` | Campos obrigatórios em certas condições |
| `mutually_exclusive` | Campos que não podem coexistir |
| `size_format` | Formato esperado para size |

## 11. Endpoint Modes

Cada provider pode suportar um ou mais modos de endpoint. O modo determina como o payload é formatado e enviado.

| Modo | Descrição | Exemplo provider |
|---|---|---|
| `text_to_image_get` | Prompt no path da URL, parâmetros como query | Pollinations GET /image/{prompt} |
| `text_to_image_post_json` | JSON body com prompt + parâmetros | Pollinations POST /v1/images/generations, DALL-E, Imagen |
| `image_edit_json` | Edição de imagem via JSON com URLs | Pollinations POST /v1/images/edits (JSON body) |
| `image_edit_multipart` | Edição de imagem via multipart com upload | Pollinations POST /v1/images/edits (multipart), OpenAI |
| `image_to_image` | Geração com imagem de referência | SD WebUI img2img |
| `inpainting` | Geração com máscara | SD WebUI inpainting, DALL-E edits |
| `local_workflow` | Workflow local (ex: ComfyUI JSON) | ComfyUI, Automatic1111 |
| `async_job` | Envio assíncrono com polling de resultado | Alguns providers enterprise |
| `websocket_stream` | Streaming via WebSocket | Realtime generation |
| `unknown` | Modo não classificado | Para providers futuros não previstos |

**Regra:** Um adapter específico pode implementar um ou mais modos. Cada modo tem seu próprio caminho de `format_payload()` e `send()`. O capability map declara quais modos estão disponíveis.

## 12. Payload Normalizado

O payload normalizado é o formato intermediário provider-agnostic que a LLM Formatting Layer produz e o adapter consome. Ele contém todos os campos semanticamente possíveis, independente de o provider suportá-los ou não.

### Provider Request Packet

Entre o `FormattedPacket` (payload normalizado, provider-agnostic) e o payload real da API, existe um conceito intermediário: o **Provider Request Packet**.

Este pacote representa o payload **após a validação de capability, mas antes da formatação final para o protocolo HTTP**. Ele é o que o adapter "decidiu enviar" — não o que a LLM "gostaria de enviar".

```text
LLM Formatting Layer
  │
  ▼
FormattedPacket (provider-agnostic: 18 campos semânticos)
  │
  ├── 1. validate_capabilities() — capability map
  ├── 2. apply_formatting_policy() — achatamento, conversão
  ├── 3. build_loss_report() — perdas identificadas
  │
  ▼
Provider Request Packet (provider-aware: campos que realmente serão enviados)
  │
  ├── 4. format_request() — adapter converte para HTTP
  │
  ▼
HTTP Request (payload real da API)
```

**O que o Provider Request Packet contém:**

```text
Campo                  | Tipo               | Descrição
-----------------------|--------------------|------------------------------------------
provider_id            | string             | Provider alvo
endpoint_mode          | string             | Modo de endpoint selecionado
capability_map_version | string             | Versão do capability map usado
formatting_policy_version | string          | Versão da política usada
adapter_contract_version | string           | Versão do contrato de adapter
request_fields         | dict               | Campos que serão enviados (já filtrados pelo capability map)
loss_report            | list[LossEntry]    | Perdas já identificadas antes do envio
original_packet_hash   | string             | Hash do FormattedPacket original (auditoria)
```

**Por que este pacote intermediário é necessário:**

1. **Debug**: você pode salvar exatamente "o que a LLM produziu" (FormattedPacket) vs "o que foi realmente enviado" (Provider Request Packet).
2. **Auditoria**: o versionamento permite rastrear qual capability map e política geraram cada requisição.
3. **Fidelity Gate**: o Gate pode comparar o FormattedPacket com o Provider Request Packet para verificar se campos críticos foram removidos.
4. **Provider Swap**: ao trocar de provider, o FormattedPacket permanece mesmo; apenas o Request Packet muda.

**Regra:**

- O FormattedPacket é **imutável** depois de produzido pela LLM.
- O Provider Request Packet é **derivado** do FormattedPacket via validação + política + loss report.
- O adapter específico recebe o **Provider Request Packet**, não o FormattedPacket.

### Campos do Payload Normalizado (18 campos semânticos)

```text
Campo                  | Tipo               | Descrição
-----------------------|--------------------|---------------------------------------------
prompt                 | string             | Obrigatório. Descrição principal.
negative_prompt        | string | null      | Opcional. Descrição do que evitar.
model                  | string | null      | Modelo desejado. Se null, provider define.
width                  | int | null         | Largura em pixels.
height                 | int | null         | Altura em pixels.
size                   | string | null      | "WIDTHxHEIGHT". Alternativa a width+height.
seed                   | int | null         | Seed para reprodutibilidade. -1 = aleatório.
n                      | int | null         | Número de imagens. Default 1.
quality                | string | null      | Qualidade: low, medium, high, hd, standard.
guidance               | float | null       | Guidance scale (cfg_scale).
steps                  | int | null         | Número de steps de inferência.
reference_images       | list[string] | []   | URLs ou caminhos de imagens de referência.
mask                   | string | null      | URL ou path da máscara para inpainting.
safe                   | string | bool | null | Filtro de conteúdo.
response_format        | string | null      | Formato de resposta: url, b64_json, file.
metadata_request       | bool              | Se deve solicitar metadados na resposta.
provider_options       | dict              | Opções específicas do provider (ex: nologo, transparent).
raw_fallback_prompt    | string | null      | Prompt bruto de fallback se a formatação falhar.
```

**Regras de uso:**

- A LLM Formatting Layer preenche os campos que fazem sentido para a skill.
- O adapter verifica cada campo contra o capability map.
- Campos não suportados não são enviados cegamente para a API — seguem a `unsupported_fields_policy`:
  - `ignore`: campo descartado, loss_report informativo.
  - `warn`: campo descartado, loss_report com warning.
  - `block`: fluxo bloqueado.
- `raw_fallback_prompt` é um prompt não estruturado que pode ser usado se o provider não suportar fields separados e a formatação da LLM falhar.

## 13. Normalized Image Result

Todo adapter específico deve retornar um resultado normalizado. Este formato é independente do provider e permite que o Fidelity Gate e o sistema consumam o resultado de forma consistente.

```text
Campo                  | Tipo               | Obrigatório | Descrição
-----------------------|--------------------|-------------|------------------------------------------
result_id              | string             | Sim         | UUID do resultado.
provider_id            | string             | Sim         | Provider que gerou.
adapter_contract_version | string           | Sim         | Versão do contrato de adapter usado.
capability_map_version | string             | Sim         | Versão do capability map usado na geração.
formatting_policy_version | string          | Sim         | Versão da política de formatação usada.
request_id             | string | null      | Não         | ID da requisição (se provider retornar).
local_path             | string | null      | Não         | Caminho local do arquivo de imagem.
remote_url             | string | null      | Não         | URL pública da imagem (se provider retornar).
bytes_hash             | string | null      | Não         | SHA256 dos bytes da imagem.
mime_type              | string             | Sim         | MIME type da imagem.
width                  | int | null         | Não         | Largura real da imagem gerada.
height                 | int | null         | Não         | Altura real da imagem gerada.
seed_used              | int | null         | Não         | Seed usado pelo provider (se retornado).
model_used             | string | null      | Não         | Modelo usado (se retornado).
prompt_sent            | string             | Sim         | Prompt efetivamente enviado.
revised_prompt         | string | null      | Não         | Prompt revisado pelo provider (se houver).
metadata               | dict              | Não         | Metadados adicionais do provider.
warnings               | list[string]       | Sim         | Avisos durante geração.
loss_report            | list[LossEntry]    | Sim         | Perdas registradas no fluxo.
error_state            | ErrorState | null  | Não         | Estado de erro, se houver.
```

**Regras:**

- `local_path` é preenchido quando o adapter salva localmente.
- `remote_url` é preenchido quando o provider retorna URL pública.
- `bytes_hash` permite verificar integridade e evitar duplicatas.
- `loss_report` é obrigatório mesmo em resultados bem-sucedidos (pode ser vazio).
- `error_state` é null se a geração foi bem-sucedida.

## 14. Política para Providers Simples

Providers simples aceitam apenas `prompt` (ex: DALL-E 3, Pollinations GET sem parâmetros extras, Imagen).

### Como o adapter deve proceder

```
Entrada (payload normalizado):
  prompt: "wireframe de tela de login"
  negative_prompt: "sem sombras, sem gradientes"
  seed: 42
  model: "flux"

1. Verificar capability map:
   - prompt → supported
   - negative_prompt → not_supported (policy: warn)
   - seed → not_supported (policy: ignore)
   - model → not_supported (policy: ignore)

2. Aplicar política:
   - negative_prompt → fundir ao prompt como negação textual
     "wireframe de tela de login. Without shadows, without gradients."
   - seed → descartar, loss_report informativo
   - model → descartar, loss_report informativo

3. Construir payload do provider:
   { "prompt": "wireframe de tela de login. Without shadows, without gradients." }

4. Gerar loss_report:
   - negative_prompt: convertido para texto no prompt (send_with_warning)
   - seed: descartado (allowed)
   - model: descartado (allowed)
```

### Regras

- Tudo que o provider não suporta vira texto no `prompt`, é descartado, ou bloqueia.
- **Campos críticos** (`immutable_requirements`, `forbidden_elements` críticos) que não podem ser representados no prompt → `block`.
- **Campos não críticos** descartados → `allowed` com loss_report.
- **Seed** descartado → `allowed` (perda aceitável).
- **Model** descartado → `allowed` (perda aceitável se a skill não especificou).
- O Fidelity Gate deve verificar se negações críticas foram preservadas textualmente.

## 15. Política para Providers Avançados

Providers avançados aceitam múltiplos campos separados (ex: Stable Diffusion WebUI, Pollinations POST com modelo e seed).

### Como o adapter deve proceder

```
Entrada (payload normalizado):
  prompt: "wireframe de tela de login, linhas finas, preto e branco"
  negative_prompt: "sombras, gradientes, fontes decorativas"
  seed: 42
  model: "flux"
  width: 1024
  height: 1024

1. Verificar capability map:
   - prompt → supported
   - negative_prompt → supported
   - seed → supported (model-dependent: flux suporta)
   - model → supported
   - width/height → supported

2. Aplicar política:
   - Manter tudo separado. Nada precisa ser achatado.

3. Construir payload do provider:
   {
     "prompt": "wireframe de tela de login, linhas finas, preto e branco",
     "negative_prompt": "sombras, gradientes, fontes decorativas",
     "seed": 42,
     "model": "flux",
     "width": 1024,
     "height": 1024
   }

4. Loss_report: vazio (sem perdas)
```

### Regras

- Campos suportados são enviados separadamente.
- Reduz achatamento textual ao mínimo.
- `loss_report` gerado apenas para campos realmente não suportados.
- Se o modelo selecionado não suportar um campo (ex: `flux` não suporta `quality`), o campo é tratado como não suportado para este modelo específico (consulta `model_capabilities`).

## 16. Política para Providers Locais

Providers locais executam inferência na própria máquina (ex: ComfyUI, Automatic1111, SD WebUI local).

### Características especiais

- Não há chamada HTTP externa (ou é localhost).
- O adapter pode montar um workflow JSON em vez de uma requisição HTTP simples.
- A resposta pode ser um arquivo local já salvo.
- Pode não haver metadados além do arquivo de imagem.

### Como o adapter deve proceder

- O capability map declara `endpoint_modes: ["local_workflow"]`.
- `format_payload()` monta o workflow JSON específico do provider local.
- `send()` pode ser:
  - Chamada HTTP para localhost.
  - Escrita de arquivo + execução de processo.
  - Chamada a SDK local.
- `parse_response()` lê o arquivo de saída.
- `normalize_result()` preenche `local_path` e tenta extrair metadados.

### Regras

- O adapter local ainda deve obedecer o capability map.
- O resultado ainda deve seguir o `NormalizedImageResult`.
- `loss_report` deve registrar se metadados não puderem ser extraídos.
- A troca de um provider remoto para local deve ser transparente para a skill e para a LLM Formatting Layer.

## 17. Política de Erros

Erros específicos do provider são traduzidos para códigos padronizados.

| Código | Significado | Ação sugerida |
|---|---|---|
| `provider_unavailable` | Provider fora do ar ou inacessível | Retry, trocar provider |
| `auth_failed` | Autenticação inválida ou ausente | Verificar credenciais |
| `payment_required` | Saldo insuficiente ou necessidade de upgrade | Recarregar, mudar de plano |
| `rate_limited` | Limite de taxa excedido | Retry com backoff |
| `invalid_payload` | Payload rejeitado pelo provider (formato, valores) | Revisar formatação |
| `unsupported_capability` | Campo solicitado não suportado pelo provider | Ajustar capability map |
| `unsafe_request` | Conteúdo bloqueado pelo filtro de segurança | Revisar prompt |
| `response_parse_failed` | Resposta da API não pôde ser interpretada | Logar resposta bruta, investigar |
| `image_generation_failed` | Provider retornou erro de geração | Re-tentar com parâmetros diferentes |
| `output_missing` | Resposta não contém imagem | Logar resposta, investigar provider |
| `timeout` | Requisição excedeu tempo limite | Aumentar timeout, retry |
| `unknown_provider_error` | Erro não classificado | Logar, notificar |

### Regras

- O adapter nunca deve expor erros brutos da API para o usuário final.
- Todo erro deve ser traduzido para o formato padronizado.
- Erros `rate_limited` e `timeout` podem ter retry automático (configurável).
- Erros `auth_failed` e `payment_required` devem bloquear o fluxo.
- Erros `unsafe_request` devem gerar `loss_report` com sugestão de revisão de prompt.

## 18. Fidelity e Loss Report

O adapter deve reportar ao Fidelity Gate toda perda de fidelidade identificada durante o processamento.

### O que o adapter deve reportar

| Tipo de perda | Exemplo | Decisão |
|---|---|---|
| Requisito crítico não enviado | `forbidden_element` sem suporte | `block` |
| Campo convertido para texto | `negative_prompt` → prompt textual | `send_with_warning` |
| Campo descartado (não crítico) | `seed` removido | `allowed` |
| Campo bloqueado por política | `guidance` em provider sem suporte | `block` |
| Campo truncado por limite | Prompt truncado por `max_prompt_chars` | `send_with_warning` |
| Modelo substituído | Modelo solicitado não disponível, fallback para default | `send_with_warning` |
| Resolução ajustada | Width/height alterado para multiplus de 64 | `allowed` |

### Formato do loss_report

```text
Campo                  | Tipo               | Descrição
-----------------------|--------------------|-----------------------------------------
original_field         | string             | Campo original perdido.
original_value         | string             | Valor original (resumido se longo).
provider_field         | string | null      | Campo do provider usado (se aplicável).
loss_reason            | string             | Código da perda.
compensation           | string             | Como o valor foi compensado.
risk                   | "baixo" | "médio" | "alto" | Risco estimado de perda de fidelidade.
decision               | "allowed" | "send_with_warning" | "block" | Decisão tomada.
```

### Integração com Fidelity Gate

- O adapter retorna o `loss_report` junto com o `NormalizedImageResult`.
- O Fidelity Gate revisa o `loss_report` como parte das validações FG-05 (nenhum campo descartado sem report) e FG-06 (payload respeita capability map).
- Se alguma entrada tiver `decision: block`, o Fidelity Gate deve bloquear o resultado.

## 19. Provider Swap Procedure

Para adicionar suporte a uma nova API de imagem, siga este procedimento:

### Fase 1: Pesquisa

1. Identificar o provider (documentação oficial, endpoints, autenticação).
2. Mapear campos aceitos e não aceitos.
3. Identificar modelos disponíveis e capacidades por modelo.
4. Identificar limites (max_prompt_chars, width/height range, rate limits).
5. Identificar formato de resposta (URL, base64, bytes, JSON).

### Fase 2: Versionamento

1. Definir `capability_map_version` (ex: `"0.1.0"`).
2. Definir `formatting_policy_version` (ex: `"0.1.0"`).
3. Definir `adapter_contract_version` que este provider implementa.

### Fase 3: Capability Map

1. Criar arquivo de configuração do capability map seguindo o contrato da seção 10.
2. Incluir `capability_map_version`, `formatting_policy_version` e `adapter_contract_version`.
3. Declarar todos os campos suportados, limites e políticas.
4. Declarar `model_capabilities` se aplicável.
5. Declarar `known_limitations`.

### Fase 4: Formatting Policy

1. Definir como o payload normalizado será convertido para este provider.
2. Decidir política para campos não suportados.
3. Documentar decisões de achatamento.

### Fase 5: Adapter Específico

1. Implementar o contrato da interface (seção 9).
2. Implementar `format_payload()` para cada endpoint mode.
3. Implementar `send()` com autenticação, timeout, retry.
4. Implementar `parse_response()` e `normalize_result()`.

### Fase 6: Testes offline

1. Validar capability map contra o schema.
2. Validar formatação de payload para casos conhecidos.
3. Validar parse de respostas simuladas.
4. Validar loss_report para campos não suportados.

### Fase 7: Teste controlado

1. Testar com chamada real (se possível em ambiente de teste).
2. Verificar se o resultado normalizado está correto.
3. Verificar se erros são traduzidos corretamente.

### Fase 8: Registry

1. Registrar o novo provider no registry de providers com todos os metadados (provider_id, versões, paths para capability map, policy e adapter).
2. Disponibilizar para a LLM Formatting Layer selecionar via `provider_id`.

### Regra fundamental

> A skill não é alterada. A LLM Formatting Layer não é alterada. O Fidelity Gate não é alterado. Apenas o capability map e o adapter específico são criados.

## 20. Compatibilidade com Pollinations

Pollinations.ai é o primeiro provider real do projeto, mas **não define a arquitetura**.

### Pollinations current tool (GET)

- Baixa capacidade: só prompt, width=1024, height=1024, nologo=true.
- `endpoint_modes`: `["text_to_image_get"]`.
- `unsupported_fields_policy`: `ignore` para a maioria dos campos.
- Capability map restrito: apenas `supports_prompt` = true, `supports_width_height` = hardcoded.

### Pollinations real API (POST + GET)

- Mais rica: model, seed, safe, image, quality, response_format.
- `endpoint_modes`: `["text_to_image_get", "text_to_image_post_json", "image_edit_json", "image_edit_multipart"]`.
- `unsupported_fields_policy`: `warn` para negative_prompt, `ignore` para steps/guidance.
- Capability map completo conforme documentado em `POLLINATIONS_IMAGE_API_EXTERNAL_RESEARCH_v0_1.md`.

### Separados no futuro

- Ambas devem se tornar configs separadas no registry.
- A LLM Formatting Layer escolhe qual usar com base no capability map.
- O adapter Pollinations específico implementa os dois modos (GET e POST).
- A ferramenta atual (`ImageGeneratorTool`) pode ser refatorada para usar o adapter, mantendo compatibilidade reversa.

## 21. Fora do Escopo

Os seguintes itens estão **explicitamente fora do escopo** deste documento e da v0.1:

- Implementar código (classes, funções, módulos).
- Criar schema Pydantic/JSON/TypedDict.
- Criar arquivos de configuração.
- Alterar a `ImageGeneratorTool` existente.
- Escolher o provider definitivo do projeto.
- Executar chamadas reais de API.
- Gerar imagens de teste.
- Decidir parâmetros default de inferência (steps, guidance, seed).
- Implementar o Fidelity Gate como código.
- Implementar o Loss Report como código.
- Definir a interface de programação exata (Python, TypeScript, etc.) — o contrato é conceitual e adaptável à linguagem do projeto.

## 22. Próximas Fases

| Fase | Descrição | Documento de saída |
|---|---|---|
| **Fase A** | Criar schema do Provider Capability Map (JSON Schema ou equivalente) | `schemas/image_provider_capability_map.schema.json` |
| **Fase B** | Criar schema do Normalized Image Result | `schemas/normalized_image_result.schema.json` |
| **Fase C** | Criar schema do Loss Report | `schemas/loss_report_entry.schema.json` |
| **Fase D** | Criar config do capability map para Pollinations API real | `configs/image_provider_capabilities/pollinations_api_v0_1.json` |
| **Fase E** | Criar config do capability map para Pollinations current tool | `configs/image_provider_capabilities/pollinations_current_tool_v0_1.json` |
| **Fase F** | Criar testes offline de validação dos capability maps contra os schemas | Testes unitários |
| **Fase G** | Propor evolução da `ImageGeneratorTool` para usar o adapter | Proposta de evolução |
| **Fase H** | Implementar adapter específico Pollinations | Código do adapter |
| **Fase I** | Integrar ao pipeline (LLM Formatting Layer → Adapter → Fidelity Gate) | Código de integração |

---

*Este documento define o contrato de abstração para adapters de providers de imagem. Nenhuma linha de código foi alterada. Nenhum schema ou config foi criado. Nenhuma API real foi chamada. O contrato é conceitual e deve ser adaptado à linguagem e às ferramentas do projeto.*

*A Pollinations.ai é o primeiro provider real, mas a arquitetura é desenhada para múltiplos providers.*
