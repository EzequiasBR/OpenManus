# POLLINATIONS_IMAGE_API_CAPABILITY_AUDIT_v0_1

> **Status:** Documento de auditoria inicial preservado como histórico técnico.
>
> Este documento foi criado antes da pesquisa externa revisada registrada em
> `docs/POLLINATIONS_IMAGE_API_EXTERNAL_RESEARCH_v0_1.md`.
>
> Em caso de conflito entre este documento e o documento `EXTERNAL_RESEARCH`,
> a versão revisada em `POLLINATIONS_IMAGE_API_EXTERNAL_RESEARCH_v0_1.md`
> deve prevalecer.
>
> Este documento continua útil para registrar a comparação inicial entre a
> `ImageGeneratorTool` atual, a documentação oficial observada e as primeiras
> hipóteses de capability map. Ele não deve ser usado sozinho como fonte final
> para schema, adapter ou implementação.

## 1. Visão Geral

Este documento mapeia a **API real** do Pollinations.ai para geração de imagem (`GET /image/{prompt}` e endpoints correlatos), separando claramente:

- O que está **observado no código atual** da `ImageGeneratorTool`.
- O que está **documentado na API oficial** (APIDOCS.md, GitHub repo).
- O que é **inferido ou não confirmado**.

O objetivo é fornecer uma base factual para futura evolução do `ImageGeneratorTool` e do `Provider Capability Map`, permitindo decisões de projeto baseadas nas capacidades reais do provider — e não apenas no subconjunto atualmente exposto pela tool.

Nenhuma linha de código foi alterada. Nenhuma chamada real à API foi executada.

## 2. Relação com Documento Anterior

| Documento | Escopo |
|---|---|
| `IMAGE_PROVIDER_CAPABILITY_MAP_CURRENT_v0_1.md` | Comportamento atual da `ImageGeneratorTool`. Apenas o que a tool **faz** no código. |
| `POLLINATIONS_IMAGE_API_CAPABILITY_AUDIT_v0_1.md` **(este)** | Capacidades reais/documentadas da API Pollinations.ai. O que a API **suporta**, independente da tool atual. |

A tool atual pode usar **um subconjunto** das capacidades da API. A API pode ter capacidades que a tool não expõe. A API pode não ter capacidades que a tool "simula" via prompt textual.

## 3. Fontes Consultadas

| Fonte | Tipo | Confiabilidade | Data | Observação |
|---|---|---|---|---|
| `app/tool/image_generator.py` | local_code | Alta | 2026-06-25 | Implementação concreta; fatos observáveis no código |
| `docs/IMAGE_PROVIDER_CAPABILITY_MAP_CURRENT_v0_1.md` | local_code | Alta | 2026-06-25 | Auditoria factual da tool |
| `docs/SKILL_RESULT_TO_IMAGE_PROVIDER_FORMATTING_CONTRACT_v0_1.md` | local_code | Alta | 2026-06-25 | Contrato-alvo de formatação |
| `https://github.com/pollinations/pollinations` (README) | official_repo | Alta | 2026-06-25 | README público do repositório oficial |
| `https://raw.githubusercontent.com/pollinations/pollinations/main/APIDOCS.md` | official_docs | Alta | 2026-06-25 | Documentação oficial da API v0.3.0 — fonte principal para capacidades |
| `https://pollinations.ai` | official_docs | Média | 2026-06-25 | Site oficial; conteúdo dinâmico (JS), informação limitada sem execução |
| `https://gen.pollinations.ai/docs` | official_docs | Média | 2026-06-25 | Página de docs; retornou conteúdo mínimo sem JavaScript |

## 4. Endpoint(s) Observados e Documentados

### 4.1 Endpoint usado no código atual

```
GET https://gen.pollinations.ai/image/{prompt}?width=1024&height=1024&nologo=true[&key={api_key}]
```

| Aspecto | Observado |
|---|---|
| Método HTTP | GET |
| Prompt | Path URL-encoded |
| `width` | Hardcoded 1024 |
| `height` | Hardcoded 1024 |
| `nologo` | Hardcoded true |
| `key` | Opcional, de `POLLINATIONS_API_KEY` |
| `model` | Não enviado |
| `seed` | Não enviado |
| `Authorization` header | Não usado |

### 4.2 Endpoints documentados na API (não usados pela tool)

A API Pollinations documenta os seguintes endpoints de imagem:

| Endpoint | Método | Documentado? | Usado pela tool? |
|---|---|---|---|
| `GET /image/{prompt}` | GET | Sim | **Sim** |
| `POST /v1/images/generations` | POST | Sim (OpenAI-compatível) | Não |
| `POST /v1/images/edits` | POST | Sim (OpenAI-compatível, multipart) | Não |
| `POST /upload` | POST | Sim (media storage) | Não |

### 4.3 Observações sobre formato de chamada

- O endpoint GET aceita prompt no **path** da URL, não no body nem em query string.
- O endpoint POST `/v1/images/generations` aceita JSON body com `prompt`, `model`, `size`, `quality`, `response_format`, `image` (referência), `safe`, `n`.
- O endpoint POST `/v1/images/edits` aceita multipart/form-data com `image`, `prompt`, `model`, `size`.
- A documentação indica que `Authorization: Bearer <key>` é o método preferido, mas `?key=<key>` é suportado para clientes que não podem enviar headers (ex: `<img>` tags).
- A API tem dois tipos de chave: `sk_` (secret, server-side) e `pk_` (publishable, client-side).

## 5. Parâmetros Documentados ou Observados

### 5.1 Tabela completa de parâmetros

Legenda:
- **observado_no_codigo_atual**: parâmetro efetivamente enviado pela `ImageGeneratorTool`.
- **documentado_na_api**: parâmetro listado na documentação oficial da API (APIDOCS.md).
- **not_confirmed**: mencionado em alguma fonte mas não confirmado na documentação oficial primária.
- **unknown**: não encontrado em nenhuma fonte confiável.

| Parâmetro | Obs. no código atual | Doc. na API | Tipo | Status | Risco |
|---|---|---|---|---|---|
| `prompt` | yes | yes | string (path) | `supported` | Baixo — é o campo primário |
| `model` | no | yes | string (query) | `not_used_by_tool` | Médio — tool sempre usa default `zimage` |
| `width` | yes (hardcoded 1024) | yes | integer (query) | `hardcoded_in_tool` | Baixo — API aceita, mas tool não expõe |
| `height` | yes (hardcoded 1024) | yes | integer (query) | `hardcoded_in_tool` | Baixo — API aceita, mas tool não expõe |
| `seed` | no | yes | integer (query) | `not_used_by_tool` | Médio — API suporta (-1 a 2147483647), mas tool não envia |
| `nologo` | yes (hardcoded true) | not_confirmed | boolean (query) | `unknown` | Baixo — parâmetro não documentado oficialmente |
| `safe` | no | yes | string/boolean (query) | `not_used_by_tool` | Médio — API tem sistema de safety |
| `quality` | no | yes | enum (query) | `not_used_by_tool` | Baixo — só gptimage/gptimage-large/gpt-image-2 |
| `image` (referência) | no | yes | string (query, URL) | `not_used_by_tool` | Alto — habilita image-to-image |
| `transparent` | no | yes | boolean (query) | `not_used_by_tool` | Baixo — só gptimage/gptimage-large/gpt-image-2 |
| `key` | yes (opcional) | yes | string (query) | `supported` | Baixo — documentado |
| `negative_prompt` | no | no | — | `not_supported` | **Alto** — API não documenta campo separado |
| `steps` | no | no | — | `not_supported` | Médio — API não documenta |
| `guidance` / `cfg_scale` | no | no | — | `not_supported` | Médio — API não documenta |
| `mask` | no | no | — | `not_supported` | **Alto** — API não documenta para image gen |
| `inpainting` | no | no | — | `not_supported` | **Alto** — API não documenta endpoint específico |
| `response_format` | no | yes | enum (POST) | `not_used_by_tool` | Baixo — aplica apenas ao POST |
| `n` (number of images) | no | yes | integer (POST) | `not_used_by_tool` | Baixo — max 1, documentado |
| `referrer` | no | no | — | `not_confirmed` | Desprezível |
| `enhance` | no | no | — | `not_confirmed` | Desprezível |
| `private` | no | no | — | `not_confirmed` | Desprezível |

### 5.2 Observações detalhadas

**`negative_prompt`**: A documentação oficial da API (APIDOCS.md v0.3.0) não lista `negative_prompt` ou `negative` como parâmetro para nenhum endpoint de imagem. A ausência é explícita. Qualquer suporte a negação depende exclusivamente do modelo de inferência downstream interpretar texto de negação no `prompt`.

**`steps` e `guidance`**: Não documentados. A API Pollinations é uma camada de roteamento sobre múltiplos providers (Flux, GPT Image, Seedream, etc.). Esses parâmetros seriam específicos do modelo e a API não os expõe.

**`nologo`**: A documentação oficial da API *não* menciona `nologo`. Este parâmetro pode ser específico de uma versão anterior ou não documentado. Foi observado no código atual, mas não confirmado como parte da API oficial.

**`seed`**: Documentado com suporte para os modelos `flux`, `zimage`, `seedream`, `klein`. Outros modelos (ex: `gptimage`, `kontext`, `nanobanana`) ignoram silenciosamente. Range: -1 (aleatório) a 2147483647.

**`model`**: A documentação observada indica default `zimage`, mas a pesquisa externa posterior registrou conflito; política local futura: enviar `model` explicitamente. Modelos disponíveis para imagem: `kontext`, `nanobanana`, `nanobanana-2`, `nanobanana-pro`, `seedream5`, `seedream`, `seedream-pro`, `ideogram-v4-turbo`, `ideogram-v4-balanced`, `ideogram-v4-quality`, `gptimage`, `gptimage-large`, `gpt-image-2`, `flux`, `zimage`, `wan-image`, `wan-image-pro`, `qwen-image`, `grok-imagine`, `grok-imagine-pro`, `klein`, `p-image`, `p-image-edit`, `nova-canvas`.

## 6. Capability Map da API Pollinations

### 6.1 Tabela de capacidades

| Capacidade | Status | Fonte |
|---|---|---|
| `supports_prompt` | `supported` | APIDOCS.md, código atual |
| `supports_negative_prompt` | `not_supported` | Não documentado na APIDOCS.md atual; tratado como não suportado por política local |
| `supports_width_height` | `supported` | APIDOCS.md: `width` (int), `height` (int) como query params |
| `supports_seed` | `supported` | APIDOCS.md: `seed` (int, -1 a 2147483647), modelos específicos |
| `supports_model_selection` | `supported` | APIDOCS.md: 20+ modelos documentados |
| `supports_enhance` | `not_confirmed` | Não encontrado em documentação oficial |
| `supports_nologo` | `not_confirmed` | Parâmetro presente no código atual, mas não na APIDOCS.md |
| `supports_private` | `not_confirmed` | Não encontrado em documentação oficial |
| `supports_safe` | `supported` | APIDOCS.md: `safe` (string/boolean), sistema de content filtering |
| `supports_steps` | `not_supported` | Não documentado na API |
| `supports_guidance` | `not_supported` | Não documentado na API |
| `supports_reference_image` | `supported` | APIDOCS.md: `image` (string, URL) para image-to-image |
| `supports_mask` | `not_supported` | Não documentado para image generation |
| `supports_inpainting` | `not_supported` | Não há endpoint específico; `POST /v1/images/edits` faz image editing, não inpainting com mask |
| `supports_structured_json` | `supported` | APIDOCS.md: `POST /v1/images/generations` responde com JSON |
| `supports_structured_response` | `supported` | APIDOCS.md: endpoint POST retorna `CreateImageResponse` com `url` ou `b64_json`, `created`, `data` |
| `supports_local_file_output` | `not_supported` | API remota; salvamento local é responsabilidade do cliente |
| `supports_api_key` | `supported` | APIDOCS.md: `Authorization: Bearer` ou `?key=` |
| `max_prompt_chars` | `not_confirmed` | APIDOCS.md documenta para POST: `prompt` length `1…32000`. Para GET, não documentado. |

### 6.2 Diferenças entre API real e tool atual

O capability map da **API real** é significativamente mais rico que o mapeamento anterior da tool. Os campos que a tool atual **não usa** mas a **API suporta**:

- `model` (seleção entre 20+ modelos)
- `seed` (reprodutibilidade, suportado por flux/zimage/seedream/klein)
- `safe` (filtro de conteúdo)
- `quality` (qualidade da imagem, modelos gptimage)
- `image` (imagem de referência para image-to-image)
- `transparent` (fundo transparente, modelos gptimage)
- `structured_json` (via POST endpoint)

## 7. Gap Analysis: API Real vs Tool Atual

| Capacidade | API suporta? | Tool atual usa? | Impacto | Prioridade futura |
|---|---|---|---|---|
| `prompt` | Sim | Sim | N/A | — |
| `negative_prompt` | **Não** | Não | Alto — perda de fidelidade em `forbidden_elements` | Crítica (mitigação via prompt textual) |
| `width/height` | Sim | Parcial (hardcoded) | Baixo — 1024x1024 cobre maioria dos casos | Média |
| `seed` | Sim | **Não** | Alto — sem reprodutibilidade | Alta |
| `model_selection` | Sim | **Não** | Alto — sem controle de estilo/modelo | Alta |
| `safe` | Sim | **Não** | Médio — sem filtro de conteúdo | Média |
| `quality` | Sim (parcial) | **Não** | Baixo — só modelos gptimage | Baixa |
| `reference_image` | Sim | **Não** | Alto — sem image-to-image | Alta |
| `steps` | **Não** | Não | Médio — sem controle de qualidade | Média (via seed e modelo) |
| `guidance` | **Não** | Não | Médio | Média (via seed e modelo) |
| `structured_json` | Sim (POST) | **Não** | Médio — tool retorna string, não JSON | Média |
| `structured_response` | Sim (POST) | **Não** | Alto — sem metadados de auditoria | Alta |
| `api_key` | Sim | Sim (parcial, query) | Baixo — aceita `Authorization` header também | Baixa |

### 7.1 Análise dos gaps mais impactantes

1. **`seed` não utilizado**: A tool atual perde reprodutibilidade. A API suporta seed para modelos como `flux`, `zimage`, `seedream`, `klein`. Impacto direto em `validation_targets` que dependem de comparação entre gerações.

2. **`model` não utilizado**: A tool atual sempre depende do comportamento padrão documentado como `zimage`, mas a política local futura deve enviar `model` explicitamente. Não é possível selecionar `flux`, `gptimage`, `seedream5` ou outros. Impacto direto em `style_requirements` que podem exigir modelo específico.

3. **`image` (referência) não utilizado**: A API suporta image-to-image via parâmetro `image` (GET) ou `POST /v1/images/edits`. A tool atual não expõe. Impacto direto em skills que precisam de referência visual.

4. **POST endpoint não utilizado**: A tool atual usa GET, que retorna apenas bytes. O POST endpoint retorna JSON com metadados. A ausência de metadados impede auditoria pós-geração.

## 8. Implicações para a Skill Formatting Layer

### 8.1 Quando usar prompt único

A API não suporta `negative_prompt` como campo separado. **Todo** conteúdo — incluindo `forbidden_elements`, `constraints` e restrições negativas — deve ser incluído no `prompt` como texto de negação.

Estratégia recomendada:
- `required_elements`, `visual_intent`, `style_requirements` → parte principal do prompt.
- `forbidden_elements` → final do prompt como cláusulas de negação ("without X, no Y, avoid Z").
- Se o modelo selecionado suportar negação textual (ex: Flux, SD via Pollinations), a eficácia é moderada.

### 8.2 Quando usar `seed`

- Se o `SkillResultCanonical` tiver `validation_targets` que exijam comparabilidade entre gerações, **deve-se** usar `seed`.
- Se `seed` for informado pela skill (via `constraints` ou `priority_map`), a LLM Formatting Layer deve extraí-lo e enviá-lo.
- Modelos que **suportam** seed: `flux`, `zimage`, `seedream`, `klein`.
- Modelos que **ignoram** seed: `gptimage`, `kontext`, `nanobanana`, `ideogram` (silenciosamente).
- Se o modelo não suportar seed, `loss_report` deve registrar.

### 8.3 Quando usar `model`

- Se a skill especificar estilo que mapeia para um modelo específico (ex: `flux` para realismo, `gptimage` para ilustração, `seedream5` para anime/sonho), a LLM Formatting Layer deve selecionar o modelo.
- Se a skill não especificar, usar `zimage` (default da API).
- A LLM Formatting Layer precisa de um mapeamento `style → model` para fazer essa escolha.

### 8.4 Como lidar com ausência de `negative_prompt` separado

- Tudo vira prompt único. `loss_report` obrigatório para `forbidden_elements` com `severity: critical`.
- `Fidelity Gate` deve verificar se negações críticas foram preservadas no prompt.
- Compensação: usar negação textual forte ("DO NOT include X", "without any Y").

### 8.5 Quando gerar `loss_report`

| Situação | Decisão |
|---|---|
| `forbidden_elements` com `severity: critical` não separável em negative_prompt | `send_with_warning` |
| `width`/`height` da skill diferente de 1024x1024 | `send_with_warning` — API aceita, mas tool atual não expõe |
| `seed` solicitado pela skill mas tool não envia | `allowed` (quando tool for atualizada, passa a `none`) |
| `model` solicitado mas tool atual não envia | `allowed` (idem) |
| `steps` ou `guidance` solicitados | `block` — API não suporta, nem com evolução da tool atual |

### 8.6 Campos que ainda precisam ser achatados em texto

Mesmo após evolução da tool para usar mais parâmetros da API, os seguintes campos **continuam sem campo próprio na API** e devem ser achatados em texto:

- `forbidden_elements` → prompt (negação textual)
- `composition_requirements` → prompt (descrição textual)
- `anatomy_construction` → prompt (descrição textual)
- `materials` → prompt (descrição textual)
- `perspective` → prompt (descrição textual)
- `constraints` de formato não-width/height → prompt

## 9. Riscos

### 9.1 Documentação externa divergente

A documentação oficial (APIDOCS.md v0.3.0) é a fonte primária. O parâmetro `nologo` observado no código atual **não aparece** na APIDOCS.md. Pode ser:
- Um parâmetro obsoleto.
- Um parâmetro não documentado mas funcional.
- Um parâmetro de versão anterior.

Recomendação: antes de evoluir a tool, testar `nologo` com uma chamada real para confirmar se ainda é aceito.

### 9.2 API agregadora/opaca

Pollinations.ai roteia requisições para múltiplos modelos (Flux, GPT Image, Seedream, etc.). O comportamento real depende:
- Do modelo selecionado (parâmetro `model`).
- Do modelo **realmente usado** se `model` não for enviado (default `zimage`, que pode mudar).
- Do provider upstream (que pode estar fora do ar, lento ou ter sido substituído).

Risco: mesmo parâmetros documentados podem ser ignorados por modelos específicos (ex: `seed` é ignorado por `gptimage`).

### 9.3 Mudança de parâmetros sem versionamento claro

A API não tem versão explícita para o endpoint GET `/image/{prompt}`. O APIDOCS.md referencia `v0.3.0` apenas como metadado. Parâmetros podem ser adicionados, alterados ou removidos sem aviso.

### 9.4 Prompt no path

O prompt é enviado no **path** da URL via GET. Isso implica:
- Limite de tamanho de URL (tipicamente ~8000 caracteres no total, incluindo query params).
- Prompt muito longo pode ser truncado ou rejeitado pelo servidor HTTP.
- A APIDOCS.md documenta `max_prompt_chars: 32000` apenas para o endpoint POST. Para GET, o limite é indeterminado.

### 9.5 Limite de prompt desconhecido (GET)

A documentação oficial informa que o POST aceita prompts de 1 a 32000 caracteres. Para o GET (usado pela tool atual), o limite não está documentado. URLs HTTP têm limite prático de ~2000-8000 caracteres dependendo do servidor.

### 9.6 Campos suportados pela API mas não pela tool

Conforme tabela na seção 7, múltiplos campos (`model`, `seed`, `safe`, `image`, `quality`) são suportados pela API mas não expostos pela `ImageGeneratorTool`. Qualquer skill que dependa desses campos terá `loss_report` até a tool ser atualizada.

### 9.7 Provider pode ignorar parâmetro silenciosamente

A documentação da API alerta que certos modelos ignoram `seed` silenciosamente. O mesmo pode ocorrer para outros parâmetros. A tool não tem como detectar se o parâmetro foi honrado porque a resposta GET não inclui metadados.

## 10. Decisão Técnica

> O schema do Provider Capability Map só deve ser criado depois deste mapeamento da API real. A tool atual deve continuar imutável até que exista gap analysis, schema e testes mínimos. A API Pollinations.ai suporta mais capacidades do que a tool atual expõe (model, seed, reference_image, structured_json), mas a ausência de negative_prompt, steps e guidance é uma restrição arquitetural da API que o contrato v0.1 já prevê com o mecanismo de loss_report.

## 11. Próximas Fases

| Fase | Descrição |
|---|---|
| **Fase A** | Criar schema Pydantic/JSON do `ProviderCapabilityMap` com base no contrato v0.1 e nos dados deste documento |
| **Fase B** | Criar config JSON para Pollinations API real (capability map completo) |
| **Fase C** | Criar config JSON para Pollinations tool atual (subconjunto usado) |
| **Fase D** | Criar testes offline de carregamento e validação dos capability maps contra o schema |
| **Fase E** | Propor evolução da `ImageGeneratorTool`: adicionar `model`, `seed`, `safe`, `image` como parâmetros opcionais, sem quebrar compatibilidade |
| **Fase F** | Adicionar suporte ao POST `/v1/images/generations` para obter metadados na resposta |

---

*Este documento é uma auditoria factual baseada em código local e documentação oficial. Campos marcados como `not_confirmed` devem ser verificados com chamada real de API antes de serem considerados suportados. Nenhuma chamada real foi executada durante esta auditoria.*
