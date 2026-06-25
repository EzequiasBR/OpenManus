# POLLINATIONS_IMAGE_API_EXTERNAL_RESEARCH_v0_1

## 1. Visão Geral

Este documento registra a pesquisa externa revisada sobre a API real de imagem da Pollinations.ai, separando fatos confirmados, conflitos, capacidades dependentes de modelo, parâmetros removidos/obsoletos e pontos que permanecem como `unknown`/`not_confirmed`.

O objetivo é fornecer uma base de evidências confiável e conservadora para:
- A criação do schema `ProviderCapabilityMap` (fase futura).
- A configuração do capability map real da Pollinations API.
- O design do adapter genérico.
- As decisões da LLM Formatting Layer e do Fidelity Gate.

Nenhuma linha de código foi alterada. Nenhuma chamada real à API foi executada. Nenhum schema ou config foi criado.

Todas as fontes externas foram revisadas em 2026-06-25. A versão da documentação consultada é `APIDOCS.md v0.3.0` (OpenAPI 3.1.0) do repositório oficial `pollinations/pollinations` (branch `main`, último commit na data da consulta).

## 2. Separação de Escopo

| Entidade | Escopo |
|---|---|
| **Pollinations.ai image API** | Provider de geração/edição de imagem via REST. Endpoints `GET /image/{prompt}`, `POST /v1/images/generations`, `POST /v1/images/edits`. Base URL `https://gen.pollinations.ai`. Documentação oficial em APIDOCS.md v0.3.0. |
| **Pollination Cloud / Ladybug Tools** | Ecossistema separado. Relacionado a CAD/BIM/AEC (simulação ambiental, análise energética, conforto térmico). Ferramentas: Honeybee, Dragonfly, HBJSON, DFJSON, JobsApi, ArtifactsApi. **Não tem relação com geração de imagem por IA.** **Não deve ser confundido com Pollinations.ai.** |
| **OpenManus ImageGeneratorTool atual** | Implementação local simplificada no arquivo `app/tool/image_generator.py`. Usa apenas o endpoint `GET /image/{prompt}` com parâmetros fixos (`width=1024`, `height=1024`, `nologo=true`). Não expõe `model`, `seed`, `safe`, `image`, `quality`. Retorna string textual com caminho local. **É um subconjunto mínimo da API real.** |

**Decisão local:** Pollinations.ai é o único provider de imagem em consideração para a v0.1. Pollination Cloud está fora de escopo. A tool atual será mantida como está até a fase de evolução.

## 3. Relação com Documentos Existentes

| Documento | Escopo | Relação com este documento |
|---|---|---|
| `SKILL_RESULT_TO_IMAGE_PROVIDER_FORMATTING_CONTRACT_v0_1.md` | Contrato arquitetural entre skill, LLM Formatting Layer, Provider Adapter e Fidelity Gate | Este documento fornece os dados de capacidade real da Pollinations API que alimentarão o Provider Capability Map referenciado no contrato |
| `IMAGE_PROVIDER_CAPABILITY_MAP_CURRENT_v0_1.md` | Mapeamento factual da tool atual (`ImageGeneratorTool`) | Este documento expande o mapeamento para a API real, revelando capacidades que a tool atual não usa |
| Pesquisa externa (fornecida pelo usuário) | Auditoria inicial da API real vs tool atual | Este documento aprofunda a auditoria com separação de conflitos, modelo-dependentes, removidos e unknown |

**Decisão local:** O schema do ProviderCapabilityMap será criado em documento posterior. O adapter genérico será definido em `docs/IMAGE_PROVIDER_ADAPTER_ABSTRACTION_CONTRACT_v0_1.md` (fase futura).

## 4. Fontes Consultadas

| Fonte | Tipo | Confiabilidade | Data | O que confirma | Observação |
|---|---|---|---|---|---|
| `https://raw.githubusercontent.com/pollinations/pollinations/main/APIDOCS.md` | official_docs | high | 2026-06-25 | v0.3.0, OpenAPI 3.1.0. Endpoints, parâmetros, schemas, autenticação, exemplos para GET/POST image, edits, upload | Fonte primária oficial. Contém schema `CreateImageResponse` |
| `https://github.com/pollinations/pollinations` (README) | official_repo | high | 2026-06-25 | Lista de modelos, key types, quick start, MCP, architecture overview | README principal. 4.7k stars, 847 forks, 9581 commits. Confirma modelo aberto e comunidade |
| `https://gen.pollinations.ai/docs` | official_docs | medium | 2026-06-25 | Página de documentação interativa | Conteúdo dinâmico (JS); retornou conteúdo mínimo sem execução de JS. APIDOCS.md é mais completo |
| `https://github.com/pollinations/pollinations/issues` | issue | medium | 2026-06-25 | Issues de comunidade sobre parâmetros, modelos, bugs | Fonte auxiliar. Issues isoladas não são verdade absoluta |
| `https://github.com/pollinations/pollinations/commits/main` | commit | high | 2026-06-25 | Histórico de alterações da APIDOCS.md e código | Não analisado em detalhe para este documento |
| `app/tool/image_generator.py` | local_code | high | 2026-06-25 | Implementação concreta da tool: endpoint GET, parâmetros fixos, sem POST | Fonte para comparação tool vs API |
| `docs/IMAGE_PROVIDER_CAPABILITY_MAP_CURRENT_v0_1.md` | local_doc | high | 2026-06-25 | Auditoria factual da tool atual | Documento pré-existente |
| Pesquisa externa (fornecida pelo usuário) | external_research | medium | 2026-06-25 | Dados coletados sobre a API Pollinations — auditoria inicial da API real vs tool atual | Tratada como auxiliar; fontes oficiais têm precedência |

**Nota sobre confiabilidade:** Fontes `official_docs` e `official_repo` têm precedência sobre `issue` e `external_research`. Parâmetros documentados em issues mas não em APIDOCS.md são marcados como `not_confirmed`. Comportamentos reportados em issues isoladas sem confirmação na documentação oficial são marcados como `conflict`.

## 5. Endpoints Identificados

### 5.1 GET /image/{prompt}

| Aspecto | Evidência |
|---|---|
| Base URL | `https://gen.pollinations.ai` (APIDOCS.md, linha de base) |
| Método | GET |
| Path | `/image/{prompt}` — prompt no path da URL |
| prompt | Tipo `string`, requerido (`*`), URL-encoded no path |
| model | Documentado como query param. **Marcado como requerido (`*`) na tabela, MAS também tem default documentado: `"zimage"`** → `conflict` |
| width | Query, integer, default `1024` |
| height | Query, integer, default `1024` |
| seed | Query, integer, default `0`, range `-1…2147483647`. **Suportado por: flux, zimage, seedream, klein. Outros ignoram.** → `model_dependent` |
| safe | Query, string/boolean, default off. Valores: privacy, secrets, sexual, violence, shield, true, nsfw |
| quality | Query, enum: `low`, `medium`, `high`, `hd`. **Só gptimage/gptimage-large/gpt-image-2** → `model_dependent` |
| image | Query, string (URL). **Múltiplas URLs separadas por `\|` ou `,`. Edição/referência. Depende do modelo.** → `model_dependent` |
| transparent | Query, boolean, default false. **Só gptimage/gptimage-large/gpt-image-2** → `model_dependent` |
| key | Query, string. Alternativa ao `Authorization` header para GET |
| nologo | **NÃO documentado na APIDOCS.md v0.3.0** → `removed_evidence` ou `not_documented` |
| Resposta | `image/jpeg` ou `image/png` (bytes) |
| Autenticação | `Authorization: Bearer <key>` (preferido) ou `?key=<key>` (alternativa GET) |
| Conflitos | `model` marcado como requerido (`*`) mas com default documentado. Se é requerido, não deveria ter default. |

**Decisão local (model policy):** Mesmo que o default `zimage` exista, o adapter futuro deve enviar `model` explicitamente por política local. Isso evita depender de defaults que podem mudar sem aviso e garante rastreabilidade.

**Decisão local (prompt no path):** O prompt no path implica limite de URL HTTP (~2000-8000 caracteres dependendo do servidor). O limite documentado de 32000 caracteres aplica-se APENAS ao endpoint POST. Para GET, o limite real é `unknown`.

### 5.2 POST /v1/images/generations

| Aspecto | Evidência |
|---|---|
| Base URL | `https://gen.pollinations.ai` |
| Path | `/v1/images/generations` |
| Método | POST |
| Content-Type | `application/json` |
| prompt | Tipo `string`, requerido (`*`). Length: `1…32000` → `max_prompt_chars = 32000` confirmado para POST |
| model | String, **default `"flux"`** (diferente do GET que usa `"zimage"`) |
| n | Integer, default 1, **range `1…1`** → `supported_limited`. **Não suporta multi-image generation** |
| size | String, formato `WIDTHxHEIGHT` (ex: `1024x1024`), default `"1024x1024"` |
| quality | Enum: `standard`, `hd`, `low`, `medium`, `high`. OpenAI `standard`/`hd` mapped to Pollinations equivalents. Default: `"medium"` |
| response_format | Enum: `url` ou `b64_json`. Default: `b64_json` |
| user | String — end-user identifier for abuse tracking |
| image | String ou String[] — reference image URL(s) for image-to-image generation. **Pollinations extension (não é OpenAI standard)** |
| safe | String/boolean — safety features |
| Autenticação | `Authorization: Bearer <key>` — **não suporta `?key=` para POST** |
| Resposta | `CreateImageResponse` (JSON) com `url` ou `b64_json`, `created`, `data` |
| `n` limitado a 1 | Mesmo que o campo exista, o range `1…1` significa que multi-image não é suportado atualmente |

**Decisão local (n):** `n` existe, mas multi-image generation não deve ser declarado como suportado real na v0.1. O range `1…1` confirma que atualmente é impossível gerar mais de uma imagem por chamada. Marcar como `supports_n = supported_limited` e `supports_multi_image_generation = not_supported_currently`.

**Decisão local (model default diferente):** GET usa `zimage` como default, POST usa `flux`. Isso confirma que o default varia por endpoint. A política de envio explícito de `model` é ainda mais importante.

### 5.3 POST /v1/images/edits

| Aspecto | Evidência |
|---|---|
| Base URL | `https://gen.pollinations.ai` |
| Path | `/v1/images/edits` |
| Método | POST |
| Content-Type | `multipart/form-data` |
| image | File upload (binary). **Pode repetir `-F "image=@…"` para múltiplas imagens de referência. Modelos que aceitam: seedream, nanobanana, klein** → `model_dependent` |
| prompt | Texto descritivo da edição |
| model | String. Exemplo no APIDOCS: `kontext` |
| size | String, formato `WIDTHxHEIGHT`. Exemplo: `1024x1024` |
| mask | **NÃO documentado na APIDOCS.md para este endpoint.** → `not_documented` |
| Retorno | `CreateImageResponse` (JSON) |
| Autenticação | `Authorization: Bearer <key>` — não suporta `?key=` |

**Decisão local:** `supports_image_edit = supported`, mas `supports_mask = not_documented`. O endpoint existe e é funcional para edição com imagem de referência, mas não há documentação de suporte a máscara (inpainting). A edição é feita via prompt descritivo + imagem de entrada, não via máscara binária.

### 5.4 Upload/Media Flow

| Aspecto | Evidência |
|---|---|
| Endpoint | `POST /upload` |
| URL base | `https://gen.pollinations.ai` |
| Método | POST |
| Content-Type | `multipart/form-data` (suporta raw binary e base64 JSON) |
| Campo | `file` (binary) |
| Resposta | JSON: `{ id, url: "https://media.pollinations.ai/<hash>", contentType, size, duplicate }` |
| Hash | Derivado dos bytes **e** do filename. Mesmo conteúdo com nomes diferentes = URLs diferentes |
| Retenção | 30 dias. Re-upload reseta o timer |
| Auth | `Authorization: Bearer <key>` |
| GET /{hash} | Recuperar media pelo hash. **Sem autenticação** — URLs públicas |
| GET /{hash}/metadata | Metadados do arquivo (hash, contentType, size, uploadedAt). **Sem autenticação** |
| HEAD /{hash} | Verificar existência sem baixar. **Sem autenticação** |

**Análise:** O fluxo de upload existe e está bem documentado na APIDOCS.md. A URL `media.pollinations.ai` é confirmada. O suporte a media storage é real e documentado. No entanto, para o escopo de geração de imagem da v0.1, este fluxo é relevante apenas como forma de obter URLs públicas para o parâmetro `image` (referência). A tool atual não usa upload.

**Decisão local:** O upload flow é `confirmed` como existente, mas não será integrado na v0.1. O parâmetro `image` pode receber URLs públicas diretamente (não precisa passar pelo upload Pollinations).

## 6. Auditoria de Parâmetros

Status:

| Código | Significado |
|---|---|
| `supported` | Documentado e funcional |
| `supported_limited` | Existe mas com limitação (ex: range 1…1) |
| `model_dependent` | Suportado apenas por modelos específicos |
| `not_supported` | Não é suportado pela API (não documentado na APIDOCS.md atual; tratado como não suportado por política local) |
| `not_documented` | Não encontrado em nenhuma fonte oficial |
| `removed_evidence` | Existiu (evidência em código/issue) mas não está na doc atual |
| `conflict` | Documentação contraditória ou comportamento reportado diferente |
| `unknown` | Nenhuma evidência disponível |
| `not_confirmed` | Mencionado em fonte não oficial, sem confirmação oficial |
| `not_exposed` | API pode suportar internamente, mas não expõe como parâmetro público |

| Parâmetro | GET /image/{prompt} | POST /v1/images/generations | POST /v1/images/edits | Status Recomendado | Observação |
|---|---|---|---|---|---|
| `prompt` | supported | supported | supported | `supported` | Campo primário em todos os endpoints |
| `model` | conflict (requerido+default) | supported (default flux) | supported | `supported` | **Conflict:** APIDOCS marca como `*` (requerido) mas documenta default `zimage`. GET default = zimage, POST default = flux |
| `width` | supported | not_exposed (usa `size`) | not_exposed (usa `size`) | `supported` | Só GET. POST usa `size` como string "WIDTHxHEIGHT" |
| `height` | supported | not_exposed (usa `size`) | not_exposed (usa `size`) | `supported` | Só GET. Idem |
| `size` | not_exposed | supported | supported | `supported` | Só POST/edits. Formato "WIDTHxHEIGHT" |
| `seed` | supported/model_dependent | no | no | `model_dependent` | GET: flux, zimage, seedream, klein. Outros ignoram. Range -1 a 2147483647 |
| `n` | no | supported_limited | no | `supported_limited` | Range 1…1. Não permite >1 |
| `quality` | model_dependent | model_dependent | no | `model_dependent` | GET: low/medium/high/hd. POST: standard/hd/low/medium/high. Só gptimage/gptimage-large/gpt-image-2 |
| `response_format` | no | supported | no | `supported` | Só POST. Valores: url, b64_json. Default b64_json |
| `user` | no | supported | no | `supported` | Só POST. End-user identifier |
| `image` | model_dependent | supported (extension) | supported (file upload) | `model_dependent` | GET/POST: URL de referência. Edits: file upload. Modelos: seedream, nanobanana, klein, kontext, gptimage |
| `mask` | no | no | not_documented | `not_documented` | Ausente na APIDOCS.md para edits. Não há endpoint de inpainting |
| `safe` | supported | supported | no | `supported` | Valores: privacy, secrets, sexual, violence, shield, true, nsfw |
| `key` | supported | not_exposed | not_exposed | `supported` | Só GET como alternativa a Bearer. POST não aceita `?key=` |
| `Authorization Bearer` | supported | supported | supported | `supported` | Método preferido para todos os endpoints |
| `referrer` | not_documented | not_documented | not_documented | `not_documented` | Não encontrado em nenhuma fonte oficial |
| `negative_prompt` | no | no | no | `not_supported` | Ausência explícita na APIDOCS.md |
| `negative` | no | no | no | `not_supported` | Ausência explícita na APIDOCS.md |
| `nologo` | not_documented | not_documented | not_documented | `removed_evidence` | Presente no código atual (hardcoded true), mas ausente na APIDOCS.md v0.3.0 |
| `enhance` | not_documented | not_documented | not_documented | `removed_evidence` | Não encontrado em APIDOCS.md atual |
| `private` | not_documented | not_documented | not_documented | `not_confirmed` | Mencionado em contextos não oficiais. Sem confirmação na doc oficial |
| `steps` | no | no | no | `not_exposed` | API não expõe. Modelos internos podem usar, mas não é parametrizável |
| `guidance` | no | no | no | `not_exposed` | Idem steps |
| `transparent` | model_dependent | no | no | `model_dependent` | Só GET. Só gptimage/gptimage-large/gpt-image-2 |
| `metadata` (structured response) | no | supported (via response) | supported (via response) | `supported` (via POST) | POST retorna `CreateImageResponse` com URL/b64_json+created. GET retorna apenas bytes sem metadados |
| `max_prompt_chars` | unknown | 32000 | unknown | `supported` (POST), `unknown` (GET/edits) | APIDOCS documenta length 1…32000 para POST. GET não documenta. Edits não documenta |

## 7. Parâmetros Removidos, Obsoletos ou Não Expostos

### 7.1 `negative_prompt` / `negative`

| Aspecto | Valor |
|---|---|
| Status | `not_supported` |
| Evidência | Ausência explícita na APIDOCS.md v0.3.0 para todos os endpoints de imagem (GET, POST generations, POST edits) |
| Risco | **Alto.** Qualquer skill que dependa de `negative_prompt` como campo separado não pode ser representada fielmente |
| Compensação | Incorporar ao prompt como negação textual. `loss_report` obrigatório para `forbidden_elements` críticos |
| Decisão | **Não entrar no payload.** Tudo deve ser fundido ao prompt principal |

### 7.2 `nologo`

| Aspecto | Valor |
|---|---|
| Status | `removed_evidence` |
| Evidência | Presente no código atual da `ImageGeneratorTool` (hardcoded `true`). **Ausente na APIDOCS.md v0.3.0.** Pode ser parâmetro obsoleto ou não documentado |
| Risco | **Baixo-médio.** Se o parâmetro não é mais reconhecido, pode ser ignorado silenciosamente. Se for obsoleto, remover não quebra nada |
| Decisão | **Não entrar em payload novo.** Manter apenas na tool legada até confirmação por chamada real |

### 7.3 `enhance`

| Aspecto | Valor |
|---|---|
| Status | `not_documented` / `removed_evidence` |
| Evidência | Não encontrado na APIDOCS.md atual. Possível parâmetro de versão anterior |
| Risco | **Baixo.** Sem evidência de funcionalidade atual |
| Decisão | **Não entrar em payload novo.** |

### 7.4 `private`

| Aspecto | Valor |
|---|---|
| Status | `not_confirmed` |
| Evidência | Não encontrado na APIDOCS.md atual. Mencionado em contextos não oficiais (issues, fóruns) sem confirmação na doc primária |
| Risco | **Médio.** Se `private` for um modo de não armazenar imagens, pode ter implicações de privacidade. Sem confirmação, não pode ser suportado |
| Decisão | **Não entrar no schema v0.1.** Manter como `not_confirmed` |

### 7.5 `steps`

| Aspecto | Valor |
|---|---|
| Status | `not_exposed` |
| Evidência | Ausência completa na APIDOCS.md. Pollinations é uma camada de roteamento sobre múltiplos providers; steps seriam específicos do modelo downstream |
| Risco | **Médio.** Sem steps, o controle de qualidade/detalhismo é limitado |
| Decisão | **Não entrar no schema v0.1 como parâmetro público.** Se um modelo interno usar steps, o adapter não tem como controlar |

### 7.6 `guidance` / `cfg_scale`

| Aspecto | Valor |
|---|---|
| Status | `unknown` / `not_exposed` |
| Evidência | Ausência completa na APIDOCS.md. Similar a steps — específico do modelo downstream |
| Risco | **Médio.** Sem guidance, o controle de aderência ao prompt é limitado |
| Decisão | **Não entrar no schema v0.1 como parâmetro público.** Marcar como `unknown/not_documented` |

### Decisão Local Consolidada

| Parâmetro | Decisão |
|---|---|
| `negative_prompt`, `negative` | Não entram em payload novo. Fundir ao prompt. |
| `enhance` | Não entra em payload novo. |
| `nologo` | Não entra em payload novo. Manter só na tool legada. |
| `steps`, `guidance` | Não entram no schema v0.1 como parâmetros públicos. Marcar como `not_exposed`. |
| `private` | Não entra no schema v0.1. Manter como `not_confirmed`. Só entrar se houver confirmação oficial forte. |

## 8. Pontos de Conflito

### 8.1 `model` com default documentado vs evidência de erro se omitido

| Fonte | Afirmação |
|---|---|
| APIDOCS.md (GET /image/{prompt}) | `model` marcado como requerido (`*`) MAS com `default: "zimage"` |
| APIDOCS.md (POST /v1/images/generations) | `model` string, `default: "flux"` (sem marcador de requerido) |
| Comportamento lógico | Se tem default, não é estritamente requerido. Se é requerido, não deveria ter default |

**Decisão conservadora:** Sempre enviar `model` explicitamente. Não confiar em default. A política de `requires_model_policy = true` no capability map resolve este conflito.

### 8.2 `n` existente vs limite atual de 1

| Fonte | Afirmação |
|---|---|
| APIDOCS.md (POST) | `n: integer, default 1, range 1…1` |
| Especificação OpenAI | `n` tipicamente permite 1-10 |

**Decisão:** `n` existe mas é `supported_limited`. `supports_multi_image_generation = not_supported_currently`. Se no futuro o range expandir, o status muda.

### 8.3 `transparent` documentado vs risco/limitação por modelo

| Fonte | Afirmação |
|---|---|
| APIDOCS.md | `transparent` é query param para GET, boolean, default false |
| APIDOCS.md | "Only supported by gptimage, gptimage-large, and gpt-image-2" |

**Decisão:** `supports_transparent_background = model_dependent`. A capacidade existe mas élimitada a 3 modelos específicos. Não é suporte universal.

### 8.4 `image` documentado vs comportamento dependente de modelo

| Fonte | Afirmação |
|---|---|
| APIDOCS.md (GET) | `image` query param, URL(s) separadas por `\|` ou `,`. "Used for editing/style reference (kontext, gptimage, seedream, klein, nanobanana)" |
| APIDOCS.md (POST generations) | `image` string or string[] — "Pollinations extension" |
| APIDOCS.md (POST edits) | `image` file upload, pode repetir para múltiplas imagens |

**Decisão:** `supports_reference_image_generation = model_dependent`. O suporte existe mas o comportamento varia por modelo. Alguns modelos usam para edição, outros para style reference.

### 8.5 `mask` ausente na documentação de edits

| Fonte | Afirmação |
|---|---|
| APIDOCS.md (POST /v1/images/edits) | Não documenta `mask` como campo |
| Especificação OpenAI | Edits aceita `mask` como campo opcional |

**Decisão:** `supports_mask = not_documented`. A API Pollinations pode ou não suportar mask internamente, mas não expõe como parâmetro público. Inpainting não deve ser prometido na v0.1.

### 8.6 Diferenças entre endpoint documentado e comportamento reportado em issues

Issues do GitHub podem reportar comportamentos que divergem da documentação oficial (ex: parâmetros que funcionam mesmo não documentados, ou que não funcionam apesar de documentados).

**Decisão:** Issues isoladas não são verdade absoluta. Comportamentos não documentados são `not_confirmed`. Comportamentos documentados mas contestados em issues são `conflict`. A documentação oficial tem precedência.

### 8.7 Parâmetros internos não expostos publicamente

| Parâmetro | Status |
|---|---|
| `steps` | `not_exposed` — API não expõe, mas modelos internos podem usar defaults |
| `guidance` | `unknown/not_documented` — Pode existir internamente mas não é parametrizável |
| Model-specific params | `not_exposed` — Cada modelo (Flux, GPT Image, Seedream) pode ter parâmetros próprios não expostos via Pollinations |

**Decisão:** Conflito não vira suporte automático. Conflito vira política conservadora no adapter. Para a v0.1, o adapter só envia parâmetros com status `supported` ou `supported_limited`.

## 9. Capability Map Recomendado para Pollinations API v0.1

| Capability | Status Recomendado | Justificativa | Observação |
|---|---|---|---|
| `supports_prompt` | `supported` | Campo primário em todos os endpoints. Documentado e funcional | — |
| `supports_model_selection` | `supported` | 20+ modelos documentados. GET e POST aceitam `model` | Conflito de requerido+default resolvido via política local |
| `requires_model_policy` | `true` | Adapter deve sempre enviar `model` explicitamente | Não confiar em default; defaults variam por endpoint |
| `supports_width_height` | `supported` | GET aceita `width` e `height` como integers | POST usa `size` em formato string; cobertura separada |
| `supports_size` | `supported` | POST e edits aceitam `size` como "WIDTHxHEIGHT" | — |
| `supports_seed` | `supported` / `model_dependent` | GET suporta seed; flux, zimage, seedream, klein honram; outros ignoram | Range -1 a 2147483647. Default 0 |
| `supports_n` | `supported_limited` | POST tem campo `n`, range 1…1 | Apenas 1 imagem por chamada |
| `supports_multi_image_generation` | `not_supported_currently` | Range 1…1 impede >1 | Pode mudar no futuro |
| `supports_quality` | `model_dependent` | Só gptimage/gptimage-large/gpt-image-2 | GET: low/medium/high/hd. POST: standard/hd/low/medium/high |
| `supports_response_format_url` | `supported` | POST response_format = "url" retorna URL pollinations.ai | — |
| `supports_response_format_b64_json` | `supported` | POST response_format = "b64_json" (default) | — |
| `supports_reference_image_generation` | `model_dependent` | kontext, gptimage, seedream, klein, nanobanana. GET via query, POST via field | Comportamento varia (edição vs style reference) |
| `supports_image_edit` | `supported` | POST /v1/images/edits documentado e funcional | Multipart, JSON body ou URL |
| `supports_mask` | `not_documented` | Ausente na APIDOCS.md para edits | Inpainting não deve ser prometido na v0.1 |
| `supports_safe` | `supported` | GET e POST aceitam `safe` como string/boolean | Valores: privacy, secrets, sexual, violence, shield, true, nsfw |
| `supports_api_key_query` | `supported` | GET aceita `?key=` como alternativa | POST não aceita |
| `supports_bearer_auth` | `supported` | Todos os endpoints aceitam `Authorization: Bearer` | Método preferido |
| `supports_referrer` | `not_documented` | Não encontrado em fontes oficiais | — |
| `supports_negative_prompt` | `not_supported` | Não documentado na APIDOCS.md atual; tratado como não suportado por política local | Não há campo separado para negação |
| `supports_nologo` | `not_supported` / `removed_evidence` | Ausente na APIDOCS.md v0.3.0 | Não entrar em payload novo |
| `supports_enhance` | `not_supported` / `removed_evidence` | Ausente na APIDOCS.md v0.3.0 | Não entrar em payload novo |
| `supports_private` | `not_confirmed` | Não confirmado em documentação oficial | Só entrar com confirmação oficial forte |
| `supports_steps` | `not_exposed` | API não expõe steps como parâmetro público | Modelos internos podem usar defaults |
| `supports_guidance` | `unknown` / `not_documented` | API não documenta guidance/cfg_scale | Pode não existir como conceito na API |
| `supports_transparent_background` | `model_dependent` | Só gptimage/gptimage-large/gpt-image-2 via GET | Default false |
| `supports_structured_response` | `supported` | POST /v1/images/generations e /edits retornam `CreateImageResponse` (JSON). GET /{hash}/metadata também | GET /image/{prompt} não retorna JSON estruturado |
| `supports_generation_metadata_response` | `partial` | POST inclui created + url/b64_json no body. GET não tem metadados de geração | Metadados de geração (seed usado, modelo, tempo) não são expostos em nenhum endpoint |
| `max_prompt_chars_known` | `post_only_32000` | POST documenta length 1…32000. GET sem documentação | Limite GET é limitado por URL HTTP (~2000-8000 chars). Edits sem documentação |

## 10. Implicações para Skill Result Formatting

### 10.1 Ausência de `negative_prompt` — impacto direto no formato do prompt

Como não há `negative_prompt` confiável na API Pollinations, restrições negativas (`forbidden_elements`, erros proibidos) devem ser incorporadas ao prompt principal como negação textual.

**Regra para a LLM Formatting Layer:**
- `forbidden_elements` com `severity: critical` → incluídos no início do prompt como "DO NOT include X", "without any Y".
- `forbidden_elements` com `severity: high` → incluídos no final do prompt.
- `loss_report` obrigatório para cada `forbidden_element` com `severity: critical`, explicando que não houve campo separado.
- O Fidelity Gate (FG-02) deve verificar se cada `forbidden_element` crítico está presente no prompt como negação textual.

### 10.2 `model` sempre explícito

A LLM Formatting Layer deve **sempre** incluir `model` no payload formatado. O capability map informa `requires_model_policy = true`. A seleção do modelo pode ser:
- Direta: se a skill especificar estilo que mapeia para um modelo específico.
- Default: `zimage` se a skill não especificar (mas enviado explicitamente, não confiando em default da API).

### 10.3 `seed` para reprodutibilidade

- Se a skill pedir reprodutibilidade (via `validation_targets` que exijam comparação entre gerações), `seed` deve ser incluído.
- Se `seed` for informado pela skill, a LLM Formatting Layer deve extraí-lo.
- Modelos que ignoram seed: `gptimage`, `kontext`, `nanobanana`, `ideogram`. O Fidelity Gate não pode garantir reprodutibilidade para esses modelos.
- `loss_report` se modelo não suportar seed.

### 10.4 `width`/`height` vs `size`

- GET usa `width` + `height` como integers.
- POST usa `size` como string "WIDTHxHEIGHT".
- A LLM Formatting Layer precisa saber qual endpoint será usado para formatar corretamente.
- Para a v0.1 (tool atual via GET), usar `width`/`height`.

### 10.5 `image` / reference image — dependente de modelo

- A capacidade de image-to-image existe mas é `model_dependent`.
- Se a skill especificar referência visual, a LLM Formatting Layer deve:
  1. Verificar se o modelo selecionado suporta `image`.
  2. Se suportar, incluir a URL da referência no payload.
  3. Se não suportar, incluir descrição textual da referência e registrar `loss_report`.

### 10.6 `mask` / inpainting — não prometido na v0.1

- `supports_mask = not_documented`.
- Nenhuma skill na v0.1 deve depender de inpainting com máscara.
- Se a skill produzir conteúdo que seria ideal para inpainting, a LLM Formatting Layer deve:
  1. Descrever a região a ser editada no prompt.
  2. Registrar `loss_report` informando que inpainting com mask não está disponível.

### 10.7 Geração de `loss_report`

| Situação | Decisão | Severidade |
|---|---|---|
| `forbidden_elements` crítico sem negative_prompt | `send_with_warning` | warning |
| `seed` solicitado mas modelo não suporta | `allowed` com loss_report | info |
| `seed` solicitado mas tool atual não envia (atualização pendente) | `allowed` | info |
| `model` solicitado mas tool atual não envia | `allowed` | info |
| `width`/`height` diferente do suportado | `send_with_warning` se GET, `allowed` se POST | warning |
| `steps` ou `guidance` solicitados | `block` — API não suporta | block |
| `mask` para inpainting | `block` — não documentado | block |
| `image` referência solicitada mas modelo não suporta | `send_with_warning` | warning |
| `transparent` solicitado mas modelo não suporta | `send_with_warning` | warning |

## 11. Decisões Locais para o Projeto

1. **Configs separadas:** Pollinations API e Pollinations current tool terão configs separadas. A API real terá um capability map completo; a tool atual terá um subconjunto. Isso permite que a LLM Formatting Layer escolha o target correto.

2. **Adapter genérico:** O adapter será desenhado para vários providers, não apenas Pollinations. A abstração deve permitir que um novo provider (ex: DALL-E, SD WebUI) seja adicionado com um novo capability map, sem alterar a LLM Formatting Layer.

3. **Tool atual imutável (por enquanto):** A `ImageGeneratorTool` não será alterada até que existam: schema, capability maps, testes offline e proposta de evolução. A tool atual continua sendo o target de fallback.

4. **Schema após este documento:** O schema `ProviderCapabilityMap` só será criado após a conclusão deste documento de pesquisa. A ordem é: pesquisa → schema → configs → testes → evolução da tool.

5. **Fidelity Gate com dois tipos de perda:** O Fidelity Gate deve diferenciar:
   - Perda por falta de suporte da API (ex: `negative_prompt` não existe).
   - Perda por erro de formatação da LLM (ex: campo crítico omitido acidentalmente).
   - O primeiro é registrado com `decision: allowed` ou `send_with_warning`. O segundo pode ser `block`.

6. **Parâmetros removidos não serão enviados:** `negative_prompt`, `negative`, `enhance`, `nologo` não entram em payload novo. A ferramenta legada pode continuar enviando `nologo` até ser atualizada.

7. **Capabilities dependentes de modelo exigirão validação adicional:** O capability map deve incluir uma lista de modelos que suportam cada capacidade `model_dependent`. O adapter (ou uma camada de validação) deve verificar se o modelo selecionado suporta a capacidade antes de enviar.

8. **Política de seed:** Se a skill pedir reprodutibilidade e o modelo suportar seed, o adapter deve enviar seed fixo. Se o modelo não suportar, registrar perda. A LLM Formatting Layer não deve inventar seed para skills que não pediram.

9. **Política de modelo default:** Se a skill não especificar modelo, usar `zimage` (GET) ou `flux` (POST) conforme o endpoint. Mas **sempre enviar explicitamente**.

10. **Prompt no path (GET) vs body (POST):** O adapter deve escolher o endpoint com base no tamanho do prompt. Prompts > ~2000 caracteres devem usar POST para evitar truncamento por limite de URL.

## 12. Conclusão Técnica

### Confirmed

- `prompt` é suportado em todos os endpoints.
- `model` pode ser selecionado entre 20+ modelos.
- `width`/`height` são suportados no GET; `size` no POST/edits.
- `seed` é suportado por flux, zimage, seedream, klein.
- `safe` é suportado como string/boolean com valores específicos.
- `response_format` = url ou b64_json no POST.
- `image` (referência) é suportado com limitações de modelo.
- `transparent` é suportado por gptimage/gptimage-large/gpt-image-2.
- `POST /v1/images/edits` existe e aceita imagem + prompt + modelo.
- `POST /upload` existe para media storage com hash content-addressed.
- `max_prompt_chars` = 32000 para POST.
- Autenticação via `Authorization: Bearer` ou `?key=` (GET).
- API é OpenAI-compatível para `/v1/images/generations` e `/v1/images/edits`.

### Conflict

- `model` é marcado como requerido mas tem default — resolver com política `requires_model_policy = true`.
- `n` existe mas range é 1…1 — `supported_limited`, não multi-image.
- Comportamento de `nologo` (presente no código, ausente na APIDOCS) — `removed_evidence`.

### Model-dependent

- `seed`: suportado por flux, zimage, seedream, klein; outros ignoram.
- `quality`: só gptimage/gptimage-large/gpt-image-2.
- `transparent`: só gptimage/gptimage-large/gpt-image-2.
- `image` (referência): kontext, gptimage, seedream, klein, nanobanana.
- Multi-image upload em edits: seedream, nanobanana, klein.

### Removed/obsolete

- `negative_prompt`: ausente da APIDOCS. Nunca fez parte da API documentada.
- `negative`: idem.
- `enhance`: não encontrado na APIDOCS atual.
- `nologo`: presente no código, ausente na APIDOCS. Provavelmente obsoleto.

### Not documented

- `mask` para edits/inpainting — ausente na APIDOCS.
- `referrer` — não encontrado.
- `guidance` / `cfg_scale` — não encontrado.
- `steps` — não encontrado como parâmetro público.
- `private` — não confirmado em fonte oficial.

### Recommended for schema v0.1

- `supports_prompt = supported`
- `supports_model_selection = supported`
- `requires_model_policy = true`
- `supports_width_height = supported` (GET) / `supports_size = supported` (POST)
- `supports_seed = supported` (com `model_dependent` specific models list)
- `supports_n = supported_limited`
- `supports_multi_image_generation = not_supported_currently`
- `supports_quality = model_dependent`
- `supports_response_format_url = supported`
- `supports_response_format_b64_json = supported`
- `supports_reference_image_generation = model_dependent`
- `supports_image_edit = supported`
- `supports_mask = not_documented`
- `supports_safe = supported`
- `supports_api_key_query = supported`
- `supports_bearer_auth = supported`
- `supports_negative_prompt = not_supported`
- `supports_nologo = not_supported` / `removed_evidence`
- `supports_enhance = not_supported` / `removed_evidence`
- `supports_private = not_confirmed`
- `supports_steps = not_exposed`
- `supports_guidance = unknown` / `not_documented`
- `supports_transparent_background = model_dependent`
- `supports_structured_response = supported`
- `supports_generation_metadata_response = partial` (POST inclui created+url/b64_json; metadados de geração como seed/model/tempo não expostos)
- `max_prompt_chars_known = post_only_32000`

### Must stay unknown/not_confirmed

- `supports_referrer` — sem evidência.
- `supports_private` — sem confirmação oficial.
- `supports_guidance` — pode não existir como conceito.
- `max_prompt_chars` para GET/edits — não documentado.
- Comportamento exato de `nologo` — requer chamada real para confirmar.
- Se `mask` funciona internamente mesmo não documentado — requer teste real.

## 13. Próximas Fases

| Fase | Descrição | Documento de saída |
|---|---|---|
| 1 | Criar contrato de abstração do Provider Adapter | `docs/IMAGE_PROVIDER_ADAPTER_ABSTRACTION_CONTRACT_v0_1.md` |
| 2 | Criar schema JSON do ProviderCapabilityMap | `schemas/image_provider_capability_map.schema.json` |
| 3 | Criar config JSON do capability map Pollinations API real | `configs/image_provider_capabilities/pollinations_api_v0_1.json` |
| 4 | Criar config JSON do capability map Pollinations tool atual | `configs/image_provider_capabilities/pollinations_current_tool_v0_1.json` |
| 5 | Criar testes offline de validação dos capability maps contra o schema | Testes unitários |
| 6 | Propor evolução do `ImageGeneratorTool` (adicionar model, seed, safe, image como opcionais, sem quebrar compatibilidade) | Proposta de evolução |
| 7 | Adicionar suporte ao POST `/v1/images/generations` para obter metadados na resposta | Proposta de evolução (ou fase separada) |

---

*Este documento registra a pesquisa externa revisada sobre a API real de imagem da Pollinations.ai. Nenhuma linha de código foi alterada. Nenhuma chamada real à API foi executada. Nenhum schema ou config foi criado. As decisões locais são políticas de projeto para a v0.1 e podem ser revisadas conforme nova evidência surja.*

*Versão da API consultada: APIDOCS.md v0.3.0 (OpenAPI 3.1.0), repositório pollinations/pollinations, branch main, 2026-06-25.*
