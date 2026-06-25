# SKILL_RESULT_TO_IMAGE_PROVIDER_FORMATTING_CONTRACT_v0_1

## 1. Visão Geral

Este contrato define a fronteira entre o resultado técnico de uma skill de desenho (UI, wireframe, ilustração, diagrama) e o payload formatado para uma API de geração de imagem. O sistema que orquestra essa transformação é uma IA de linguagem natural — e não código fixo, template ou mapper estático.

A arquitetura separa seis camadas com responsabilidades distintas:

```text
Skill (ex: wireframing, ui-design)
  ↓ entrega
Skill Result Canonical (documento técnico estruturado)
  ↓
LLM Formatting Layer (IA de linguagem natural)
  ↓
Provider Adapter (código leve de conversão/envio)
  ↓
Image Provider / API (Stable Diffusion, DALL-E, Imagen, etc.)
  ↑
Fidelity Gate (valida que nada foi perdido ou inventado)

Provider Capability Map (descreve o que cada provider suporta)
  → usado pela LLM Formatting Layer para adaptar o payload
```

Cada camada tem um contrato específico. Nenhuma delas invade a responsabilidade da outra.

## 2. Decisão Arquitetural Congelada

> A skill produz conteúdo técnico canônico. A IA de linguagem estrutura esse conteúdo conforme o contrato do provider. O adapter apenas converte/envia o payload. O validador verifica se nenhum requisito da skill foi perdido ou inventado.

Esta decisão é irreversível para o escopo da v0.1. Qualquer proposta que acople skill a provider, ou que pule a camada de estruturação da IA, está fora do contrato.

## 3. O que a Skill É

A skill de desenho entrega um resultado técnico que contém **exclusivamente**:

| Campo | Descrição |
|---|---|
| `visual_intent` | O que a imagem deve comunicar em uma frase |
| `subject` | O que está sendo desenhado (objeto, cena, persona, componente) |
| `composition` | Como os elementos estão dispostos no quadro |
| `perspective` | Ângulo, enquadramento, ponto de vista |
| `anatomy_construction` | Regras de construção: proporções, grid, hierarquia visual, eixos |
| `style` | Estilo visual: paleta, traço, estética, referência de movimento |
| `materials` | Texturas, acabamentos, cores específicas, iluminação |
| `constraints` | Restrições técnicas: formato, resolução, orientação, budget visual |
| `forbidden_errors` | O que **não** pode aparecer: artefatos, distorções, quebras de estilo |
| `priority_map` | O que é crítica vs desejável vs opcional |
| `checkpoints` | O que deve ser verificado antes de considerar a imagem aceitável |
| `validation_criteria` | Critérios objetivos de aprovação/rejeição |

A skill **não** entrega:

- prompt formatado
- campos de API
- parâmetros de inferência
- seed, steps, guidance, mask
- imagem de referência codificada

## 4. O que a Skill Não É

```text
A skill NÃO é:
├── Provider Adapter
├── Prompt final obrigatório
├── Cliente de API
├── Runtime de imagem
├── Validador de API
├── Camada de tradução para formato específico
├── Ferramenta que decide parâmetros do provider
└── Template de payload
```

A skill produz conteúdo semântico. Ela não sabe se o provider aceita `negative_prompt`, se espera `width`/`height` como múltiplos de 64, ou se suporta `guidance_scale`. Isso é responsabilidade da LLM Formatting Layer e do Provider Capability Map.

## 5. Skill Result Canonical Contract

Schema conceitual do resultado entregue pela skill:

```json
{
  "skill_result_id": "uuid-v4",
  "skill_id": "wireframing",
  "skill_version": "0.1.0",
  "task_type": "wireframe|ui_design|illustration|diagram",

  "visual_intent": "string — uma frase que resume o propósito visual",

  "required_elements": [
    {
      "id": "el-01",
      "type": "component|shape|text|persona|object",
      "description": "string",
      "position": "top-left|center|grid-cell-3|etc",
      "critical": true
    }
  ],

  "forbidden_elements": [
    {
      "id": "forbid-01",
      "description": "o que não pode aparecer",
      "severity": "critical|high|medium"
    }
  ],

  "construction_requirements": [
    {
      "id": "con-01",
      "description": "regra de construção (ex: grid de 12 colunas, proporção áurea)",
      "critical": true
    }
  ],

  "composition_requirements": {
    "layout": "string — descrição do layout",
    "alignment": "left|center|right|grid",
    "white_space_policy": "minimum|balanced|generous",
    "critical": true
  },

  "style_requirements": {
    "palette": ["#hex", "#hex"],
    "typography": "string — famílias e hierarquia",
    "aesthetic": "string — ex: flat, skeuomorphic, neumorphic, line-art",
    "stroke_style": "string — se aplicável",
    "critical": true
  },

  "priority_map": {
    "critical": ["el-01", "con-01", "composition_requirements"],
    "high": ["el-02", "style_requirements"],
    "medium": ["el-03"],
    "optional": ["el-04"]
  },

  "validation_targets": [
    {
      "id": "val-01",
      "description": "o que verificar na imagem gerada",
      "method": "visual_inspection|structural_check|proportion_test"
    }
  ],

  "source_trace": {
    "skill_invocation_id": "uuid-v4",
    "skill_input_hash": "sha256",
    "skill_output_hash": "sha256",
    "llm_formatting_log": "string — referência ao log de transformação"
  },

  "immutable_requirements": [
    "lista de requirement_ids que não podem ser removidos sob hipótese alguma"
  ]
}
```

Campos marcados como "critical": true em qualquer nível **não podem** ser omitidos, simplificados ou distorcidos pela LLM Formatting Layer.

## 6. LLM Formatting Layer

### 6.1 Papel

A IA de linguagem natural (LLM) é a **única** camada que transforma o Skill Result Canonical em um payload compatível com o provider de imagem. Ela não é um mapper estático — ela entende o conteúdo semântico e o reestrutura.

Responsabilidades da LLM Formatting Layer:

| Operação | Permitida? |
|---|---|
| Organizar conteúdo em ordem de importância | Sim |
| Compactar conteúdo para caber no limite de caracteres | Sim, com loss_report |
| Traduzir descrição técnica para linguagem visual | Sim |
| Separar prompt positivo / negativo | Sim |
| Adaptar ao formato do provider (JSON vs string plana) | Sim |
| Preservar todos os immutable_requirements | **Obrigatório** |
| Registrar qualquer compressão que remova conteúdo | **Obrigatório** |

### 6.2 Regras Obrigatórias

```text
┌─────────────────────────────────────────────────────────────┐
│ REGRAS DA LLM FORMATTING LAYER                              │
│                                                             │
│ ✔ Pode transformar a forma (reorganizar, reestruturar)      │
│ ✘ Não pode inventar conteúdo visual novo                    │
│ ✘ Não pode adicionar requisito visual que não veio da skill │
│ ✘ Não pode remover requisito obrigatório (critical)         │
│ ✘ Não pode trocar a intenção visual                         │
│ ✘ Não pode suavizar erro proibido                           │
│ ✘ Não pode alterar prioridade crítica para high ou menor    │
│ ✘ Não pode descartar campo sem registrar no loss_report     │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Saída da LLM Formatting Layer

A LLM Formatting Layer produz um **Payload Formatado** que contém:

```json
{
  "provider": "nome-do-provider",
  "formatted_payload": { ... },
  "loss_report": [ ... ],
  "formatting_log": "string — decisões tomadas durante a formatação"
}
```

Este pacote é entregue ao Provider Adapter.

## 7. Provider Capability Map

Cada provider de imagem deve ter um mapa de capacidades registrado. Este mapa descreve o que o provider suporta, em limites quantitativos e qualitativos.

Schema conceitual:

```json
{
  "provider_id": "stable-diffusion-webui",
  "provider_version": "1.7.0",

  "supports_prompt": true,
  "supports_negative_prompt": true,
  "supports_seed": true,
  "supports_width_height": true,
  "supports_steps": true,
  "supports_guidance": true,
  "supports_reference_image": false,
  "supports_mask": false,
  "supports_inpainting": false,
  "supports_structured_json": true,

  "max_prompt_chars": 1500,
  "max_negative_prompt_chars": 1500,
  "width_multiple_of": 64,
  "height_multiple_of": 64,
  "min_width": 512,
  "max_width": 1024,
  "min_height": 512,
  "max_height": 1024,

  "unsupported_fields_policy": "ignore|error|warn",

  "required_fields": ["prompt"],
  "optional_fields": ["negative_prompt", "seed", "width", "height", "steps", "cfg_scale"]
}
```

Exemplo para DALL-E 3:

```json
{
  "provider_id": "dall-e-3",
  "supports_prompt": true,
  "supports_negative_prompt": false,
  "supports_seed": false,
  "supports_width_height": true,
  "supports_steps": false,
  "supports_guidance": false,
  "supports_reference_image": false,
  "supports_mask": false,
  "supports_inpainting": false,
  "supports_structured_json": false,
  "max_prompt_chars": 4000,
  "unsupported_fields_policy": "ignore"
}
```

O Capability Map é consultado pela LLM Formatting Layer **antes** de estruturar o payload. É ele que informa, por exemplo, que `negative_prompt` deve ser fundido ao prompt principal quando não suportado.

## 8. Provider Formatting Policy

Para cada cenário de provider, a LLM Formatting Layer deve seguir uma política específica:

### 8.1 Provider que aceita apenas prompt

- Unificar todos os requisitos (positivos e negativos) em uma única string de prompt.
- Usar linguagem natural para expressar negação: "without shadows", "no text artifacts".
- `forbidden_elements` devem ser convertidos para cláusulas de negação no início do prompt.
- `loss_report` deve registrar que `negative_prompt` não pôde ser separado.

### 8.2 Provider que aceita prompt + negative_prompt

- `required_elements`, `visual_intent`, `style_requirements` → `prompt`.
- `forbidden_elements` → `negative_prompt`.
- Manter separação rígida: negação não deve vazar para o prompt positivo.

### 8.3 Provider que aceita parâmetros avançados

- seed: usar se a skill não especificar; se especificar, preservar.
- steps / guidance: a skill não define estes valores. A LLM Formatting Layer pode definir defaults seguros (ex: steps=30, guidance=7.5). Se houver constraints que sugiram ajuste (ex: "imagem precisa ser muito detalhada"), pode sugerir steps maiores.
- width / height: extrair de constraints se presente; caso contrário, usar default do provider.

### 8.4 Provider que aceita imagem de referência

- Se a skill especificar referência visual, a LLM Formatting Layer deve extrair a descrição da referência e incluí-la no prompt.
- O provider adapter é responsável por anexar o binário da imagem (se aplicável).

### 8.5 Provider que aceita inpainting / mask

- Se `task_type` indicar inpainting, a LLM Formatting Layer deve estruturar o prompt para descrever apenas a região editada.
- `forbidden_elements` devem ser priorizados para evitar que a região editada reintroduza o erro.

### 8.6 Provider que ignora campos desconhecidos

- unsupported_fields_policy: "ignore" permite enviar campos extras sem erro. A LLM Formatting Layer ainda deve evitar enviar campos que o provider não suporta, para não criar falsas expectativas de que o campo será processado.
- Se o campo for crítico e não suportado, deve ser registrado em `loss_report` com severidade `warning` ou `block`.

## 9. Provider Adapter

O Provider Adapter é a camada de código que **executa** a chamada HTTP/API.

Regras do Provider Adapter:

```text
┌─────────────────────────────────────────────────────────────┐
│ REGRAS DO PROVIDER ADAPTER                                  │
│                                                             │
│ ✘ Não interpreta a skill                                    │
│ ✘ Não inventa prompt                                        │
│ ✘ Não decide conteúdo visual                                │
│ ✘ Não reordena prioridades                                  │
│                                                             │
│ ✔ Apenas converte o pacote final para chamada técnica       │
│ ✔ Valida campos obrigatórios (required_fields)              │
│ ✔ Reporta campos não suportados (unsupported_fields_policy) │
│ ✔ Envia a requisição                                        │
│ ✔ Retorna o resultado bruto da API                          │
└─────────────────────────────────────────────────────────────┘
```

O adapter recebe:

```json
{
  "provider": "stable-diffusion-webui",
  "formatted_payload": {
    "prompt": "...",
    "negative_prompt": "...",
    "seed": -1,
    "width": 512,
    "height": 512,
    "steps": 30,
    "cfg_scale": 7.5
  },
  "loss_report": []
}
```

E produz:

- Chamada HTTP para a API do provider.
- Resposta bruta (imagem, base64, URL, erro).
- Log da chamada.

O adapter **não** valida fidelidade do conteúdo — isso é responsabilidade do Fidelity Gate.

## 10. Fidelity Gate

O Fidelity Gate é executado **depois** que o payload formatado é produzido, **antes** de enviar ao provider (e opcionalmente **depois** do resultado, para verificar a imagem gerada contra os critérios da skill).

### 10.1 Validações obrigatórias

```text
┌─────────────────────────────────────────────────────────────┐
│ FIDELITY GATE — validações pré-envio                        │
│                                                             │
│ [FG-01] Todo requisito critical da skill está presente      │
│         no payload final?                                   │
│ [FG-02] Todo forbidden_error critical está preservado       │
│         no prompt ou negative_prompt?                       │
│ [FG-03] Nenhum requisito visual novo foi adicionado?        │
│ [FG-04] Nenhuma prioridade critical foi rebaixada?          │
│ [FG-05] Nenhum campo obrigatório foi descartado sem         │
│         loss_report?                                        │
│ [FG-06] Payload respeita o capability map do provider       │
│         (limites de caracteres, campos obrigatórios)?       │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Resultado do Fidelity Gate

```json
{
  "gate_id": "uuid-v4",
  "status": "passed|blocked|passed_with_warnings",
  "checks": [
    {
      "check_id": "FG-01",
      "description": "Todo requisito critical presente",
      "status": "passed|failed|warning",
      "details": "string — explicação se falhou"
    }
  ],
  "blocking_issues": ["FG-02", "FG-05"],
  "loss_report_reviewed": true
}
```

Se status for `blocked`, o payload **não pode** ser enviado ao provider. O sistema deve retornar à LLM Formatting Layer para corrigir.

Se status for passed_with_warnings, o envio é permitido, mas o warning deve ser registrado no source_trace da skill.

### 10.3 Validação pós-geração (opcional, v0.1 como informativa)

Após a imagem ser gerada, o Fidelity Gate pode validar a imagem contra os `validation_targets` da skill. Este é um passo informativo na v0.1 — não bloqueia o fluxo, mas alimenta o rastro de auditoria.

## 11. Loss Report

Quando a LLM Formatting Layer precisa descartar ou comprimir um campo porque o provider não o suporta, ela deve registrar um loss_report_entry.

Schema:

```json
{
  "original_field": "negative_prompt",
  "original_content": "evite sombras duras, sem distorção de perspectiva",
  "loss_reason": "provider_does_not_support_negative_prompt",
  "compensation": "conteúdo fundido ao prompt principal como negação textual",
  "risk": "baixo — negação textual é compreendida pelo modelo",
  "decision": "allowed|block|send_with_warning"
}
```

Decisões:

| Decisão | Significado |
|---|---|
| `allowed` | Perda aceitável, envio permitido |
| `block` | Perda inaceitável, payload não pode ser enviado |
| `send_with_warning` | Perda tolerada mas deve ser registrada e auditável |

Critérios para `block`:

- Campo `immutable_requirements` seria descartado.
- `forbidden_element` com `severity: critical` seria omitido.
- `visual_intent` seria alterada.

## 12. Exemplo Completo

### 12.1 Skill Result Canonical (simplificado)

```json
{
  "skill_result_id": "sr-abc-123",
  "skill_id": "wireframing",
  "skill_version": "0.1.0",
  "task_type": "wireframe",

  "visual_intent": "Wireframe de tela de login para aplicativo mobile",

  "required_elements": [
    {
      "id": "el-01",
      "type": "component",
      "description": "Campo de texto para email no topo do formulário",
      "position": "center-top",
      "critical": true
    },
    {
      "id": "el-02",
      "type": "component",
      "description": "Campo de texto para senha abaixo do email",
      "position": "center-middle",
      "critical": true
    },
    {
      "id": "el-03",
      "type": "component",
      "description": "Botão 'Entrar' abaixo dos campos",
      "position": "center-bottom",
      "critical": true
    },
    {
      "id": "el-04",
      "type": "text",
      "description": "Logo ou nome do app no topo da tela",
      "position": "top-center",
      "critical": false
    }
  ],

  "forbidden_elements": [
    {
      "id": "forbid-01",
      "description": "Sombras ou gradientes nos elementos",
      "severity": "critical"
    },
    {
      "id": "forbid-02",
      "description": "Textos ilegíveis ou fontes decorativas",
      "severity": "high"
    }
  ],

  "composition_requirements": {
    "layout": "centralizado, formulário ocupando 60% da largura",
    "alignment": "center",
    "white_space_policy": "balanced",
    "critical": true
  },

  "style_requirements": {
    "aesthetic": "wireframe preto e branco, linhas finas",
    "stroke_style": "1px solid black",
    "critical": true
  },

  "priority_map": {
    "critical": ["el-01", "el-02", "el-03", "composition_requirements", "style_requirements"],
    "high": ["forbid-01", "forbid-02"],
    "medium": ["el-04"]
  },

  "immutable_requirements": ["el-01", "el-02", "el-03", "composition_requirements", "style_requirements", "forbid-01"]
}
```

### 12.2 Capability Map (provider simples — apenas prompt)

```json
{
  "provider_id": "minimal-api",
  "supports_prompt": true,
  "supports_negative_prompt": false,
  "max_prompt_chars": 2000,
  "unsupported_fields_policy": "ignore"
}
```

### 12.3 Payload formatado para provider apenas prompt

A LLM Formatting Layer unifica tudo em uma única string:

```json
{
  "provider": "minimal-api",
  "formatted_payload": {
    "prompt": "Wireframe de tela de login mobile, centralizado, formulário ocupando 60% da largura. Preto e branco, linhas finas 1px solid black. Campo de email no topo do formulário, campo de senha abaixo, botão Entrar abaixo dos campos. Logo ou nome do app no topo da tela. Without shadows, without gradients, without decorative fonts, without illegible text."
  },
  "loss_report": [
    {
      "original_field": "negative_prompt",
      "original_content": "forbidden_elements: forbid-01, forbid-02",
      "loss_reason": "provider_does_not_support_negative_prompt",
      "compensation": "conteúdo fundido ao prompt como negação textual no final",
      "risk": "baixo",
      "decision": "allowed"
    }
  ]
}
```

### 12.4 Payload formatado para provider com prompt + negative_prompt

```json
{
  "provider": "stable-diffusion-webui",
  "formatted_payload": {
    "prompt": "Wireframe de tela de login mobile, layout centralizado, formulário ocupando 60% da largura. Estilo preto e branco, linhas finas 1px, traço sólido. Campo de email no topo, campo de senha no centro, botão Entrar abaixo. Logo ou nome do app sutil no topo.",
    "negative_prompt": "sombras, gradientes, elementos com gradiente, fontes decorativas, texto ilegível, serifa decorativa, distorção de forma",
    "seed": -1,
    "width": 512,
    "height": 512,
    "steps": 30,
    "cfg_scale": 7.5
  },
  "loss_report": []
}
```

### 12.5 Fidelity Gate Result

```json
{
  "gate_id": "fg-abc-123",
  "status": "passed",
  "checks": [
    {
      "check_id": "FG-01",
      "description": "Todo requisito critical presente",
      "status": "passed",
      "details": "el-01, el-02, el-03, composition_requirements, style_requirements todos presentes no prompt"
    },
    {
      "check_id": "FG-02",
      "description": "Todo forbidden_error critical preservado",
      "status": "passed",
      "details": "forbid-01 (sombras/gradientes) presente no negative_prompt"
    },
    {
      "check_id": "FG-03",
      "description": "Nenhum requisito visual novo adicionado",
      "status": "passed",
      "details": "Nenhum elemento fora do skill result canonical identificado"
    },
    {
      "check_id": "FG-04",
      "description": "Nenhuma prioridade critical rebaixada",
      "status": "passed",
      "details": "Todos os elementos critical estão no prompt principal"
    },
    {
      "check_id": "FG-05",
      "description": "Nenhum campo obrigatório descartado sem loss_report",
      "status": "passed",
      "details": "Apenas perda registrada em loss_report (negative_prompt não suportado no minimal-api)"
    },
    {
      "check_id": "FG-06",
      "description": "Payload respeita o capability map",
      "status": "passed",
      "details": "max_prompt_chars respeitado, campos obrigatórios presentes"
    }
  ],
  "blocking_issues": [],
  "loss_report_reviewed": true
}
```

## 13. Fora do Escopo

Os seguintes itens estão **explicitamente fora do escopo** deste documento e da v0.1:

- Implementar código (schemas, classes, funções).
- Alterar tools existentes (ImageGeneratorTool, etc.).
- Alterar testes existentes.
- Alterar provider atual de imagem.
- Alterar GraphStore ou seus schemas.
- Criar novo cliente de API.
- Criar runtime de imagem.
- Decidir qual provider será usado.
- Decidir parâmetros default de API (steps, guidance, seed) — a LLM Formatting Layer decide com base no Capability Map.

## 14. Próximas Fases

| Fase | Descrição |
|---|---|
| **Fase A** | Documentar contrato (este documento). |
| **Fase B** | Criar schemas Pydantic ou dataclasses para SkillResultCanonical, ProviderCapabilityMap, LossReportEntry, FidelityGateResult. |
| **Fase C** | Criar testes unitários do Fidelity Gate (validações FG-01 a FG-06). |
| **Fase D** | Mapear provider atual de imagem — criar ProviderCapabilityMap para o(s) provider(s) existente(s) no projeto. |
| **Fase E** | Integrar ao ImageGeneratorTool sem quebrar compatibilidade — a LLM Formatting Layer e o Fidelity Gate são camadas inseridas antes do adapter. |
| **Fase F** | Registrar eventos no GraphStore futuramente — skill invocation, formatting decisions, loss report, fidelity gate result. |

---

*Este documento é um contrato arquitetural. Nenhuma implementação de código deve ser derivada diretamente dele sem passar pelas fases B–E.*
