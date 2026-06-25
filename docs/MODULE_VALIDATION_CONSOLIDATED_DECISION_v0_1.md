# Module Validation Consolidated Decision — v0.1

> **Date:** 2026-06-25
> **Bases verificáveis usadas nesta decisão:**
> - `docs/MODULE_DISPOSITION_PLAN_v0_1.md`
> - `scripts/validation/validate_modules.py`
> - validação modular feita por dois agentes independentes, consolidada neste documento
> - resultados registrados de `compileall`, `pip check`, `pytest` sandbox e inspeções de import/registry
> - inventário e auditorias já existentes em `docs/`
>
> **Observação:** Os relatórios independentes foram usados como insumo durante a consolidação, mas não estão presentes neste workspace com nomes de arquivo separados; a decisão final consolidada é este documento.
>
> **Regra:** Este documento **não autoriza limpeza automática**. Nenhum código foi alterado.

---

## 1. Resumo Executivo

Dois agentes independentes validaram o projeto OpenManus local com metodologias complementares. Ambos concluem:

1. **`python -m compileall app`** passou — todo o pacote `app/` compila sem erro.
2. **`python -m pip check`** passou — nenhuma dependência formalmente quebrada.
3. **Cobertura de testes insuficiente** — `pytest -k "not sandbox"` seleciona 0 testes. A única suíte (`tests/sandbox/*`, 25 testes) não está saudável no ambiente atual: em uma execução registrada, houve 13 falhas, 10 erros e 2 testes passando. As falhas estão concentradas no caminho Docker/sandbox local.
4. **8 módulos com import FAIL** — todos por `ModuleNotFoundError: No module named 'daytona'`. Nenhum afeta o Manus atual (que usa o caminho HTTP validado).
5. **52 módulos com import PASS** — core, tools, flows, prompts, MCP, browser, search, charts, bedrock.
6. **Não há base para remoção agressiva.** O projeto tem acoplamento real entre módulos, e a cobertura de testes é insuficiente para garantir que remoções não quebrem runtime.
7. **A próxima etapa deve ser desacoplamento/organização, não remoção.**

### Divergência entre os dois relatórios

| Aspecto | Relatório 1 (Runtime) | Relatório 2 (Independente) | Resolução |
|---------|----------------------|---------------------------|-----------|
| Importação `app.tool.*` | PASS via import direto | SKIP por risco de execução (timeout no pacote agregador) | Ambos verdadeiros: import direto funciona, mas o pacote `app.tool.__init__` acopla opcionais ao core |
| Docker sandbox | Import PASS, runtime FAIL (Docker desligado) | Docker CLI instalado, named pipe indisponível | Consenso: QUARANTINE_FOR_FIX |
| `app/daytona/` | FAIL (SDK ausente) | FAIL (SDK ausente) | Consenso: LEGACY_DEPENDENCY |
| `app/tool/file_operators.py` | PASS import, PASS instancia LocalFileOperator | SKIP por risco + INVESTIGATE (acoplamento com sandbox client) | Consenso: KEEP_PROTECTED / INVESTIGATE |
| `app/tool/str_replace_editor.py` | PASS import, PASS instancia | KEEP_CORE (registrado no Manus) | Consenso: KEEP_PROTECTED |

---

## 2. Tabela de Consenso

| Módulo/Área | Classif. R1 | Classif. R2 | Decisão Consolidada | Justificativa | Ação Próxima |
|---|---|---|---|---|---|
| `app/agent/` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Base de toda hierarquia de agentes | Manter; criar teste de boot |
| `app/flow/` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Orquestração de agentes | Manter |
| `app/prompt/` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | System prompts do core | Manter |
| `app/config.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Singleton de configuração | Manter; testar parsing |
| `app/llm.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Cliente LLM central | Manter |
| `app/schema.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Modelos de dados | Manter |
| `app/exceptions.py` | KEEP_CORE | — | **KEEP_CORE** | Exceções do core | Manter |
| `app/logger.py` | KEEP_CORE | — | **KEEP_CORE** | Logger singleton (loguru) | Manter |
| `app/tool/base.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Classe base de todas as tools | Manter |
| `app/tool/tool_collection.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Gerenciamento de tools | Manter |
| `app/tool/terminate.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Finaliza interação | Manter |
| `app/tool/create_chat_completion.py` | KEEP_CORE | KEEP_CORE | **KEEP_PROTECTED** | Output LLM estruturado; tool padrão de `ToolCallAgent` | Manter; proteger |
| `app/tool/python_execute.py` | KEEP_CORE | KEEP_CORE | **KEEP_PROTECTED** | Execução Python local; registrada no Manus | Manter; proteger |
| `app/tool/str_replace_editor.py` | KEEP_CORE | KEEP_CORE | **KEEP_PROTECTED** | Registrado no Manus; edição local de arquivos | Manter; proteger |
| `app/tool/ask_human.py` | KEEP_CORE | KEEP_CORE | **KEEP_CORE** | Input do usuário | Manter |
| `app/tool/file_operators.py` | KEEP_CORE | INVESTIGATE | **KEEP_PROTECTED / INVESTIGATE** | Acoplado com sandbox client (SANDBOX_CLIENT) | Manter; investigar desacoplamento |
| `app/integrations/daytona_http.py` | KEEP_VALIDATED_TOOL | KEEP_VALIDATED_TOOL | **KEEP_VALIDATED_TOOL** | Caminho HTTP validado para Daytona | Manter; proteger |
| `app/tool/daytona_sandbox.py` | KEEP_VALIDATED_TOOL | KEEP_VALIDATED_TOOL | **KEEP_VALIDATED_TOOL** | Registrado no Manus; tool de execução remota | Manter; testar |
| `app/tool/image_generator.py` | KEEP_VALIDATED_TOOL | KEEP_VALIDATED_TOOL | **KEEP_VALIDATED_TOOL** | Geração de imagem (Pollinations); registrado no Manus | Manter; testar |
| `output_images/` | — | KEEP_LOCAL_RUNTIME_OUTPUT | **KEEP_LOCAL_RUNTIME_OUTPUT** | Diretório de output do ImageGeneratorTool | Manter; não apagar |
| `scripts/validation/validate_modules.py` | KEEP_CORE | — | **KEEP_VALIDATION_UTILS** | Utilitário de validação modular usado na consolidação | Manter; reutilizar |
| `app/sandbox/` | QUARANTINE_FOR_FIX | QUARANTINE_FOR_FIX | **QUARANTINE_FOR_FIX** | Docker local; import OK, runtime falha (socket + named pipe) | Manter; isolar em fase futura |
| `tests/sandbox/` | QUARANTINE_FOR_FIX | QUARANTINE_FOR_FIX | **QUARANTINE_FOR_FIX** | Única suíte de testes; falha por Docker | Manter; marcador `@pytest.mark.docker` |
| `app/daytona/` | LEGACY_DEPENDENCY | LEGACY_DEPENDENCY | **LEGACY_DEPENDENCY / INVESTIGATE** | SDK daytona não instalado; 2 módulos (sandbox.py, tool_base.py) | Investigar antes de remover |
| `app/agent/sandbox_agent.py` | LEGACY_DEPENDENCY | INVESTIGATE | **LEGACY_DEPENDENCY / INVESTIGATE** | Entry point sandbox_main.py; importa app.daytona | Investigar antes de remover |
| `app/tool/computer_use_tool.py` | LEGACY_DEPENDENCY | INVESTIGATE | **LEGACY_DEPENDENCY / INVESTIGATE** | Depende de app.daytona.tool_base; não registrado no Manus | Investigar antes de remover |
| `app/tool/sandbox/` | LEGACY_DEPENDENCY | LEGACY_DEPENDENCY | **LEGACY_DEPENDENCY / INVESTIGATE** | 4 tools legadas (shell, files, browser, vision) — SDK daytona ausente | Investigar antes de remover |
| `app/mcp/` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL** | Servidor MCP (FastMCP) | Manter opcional |
| `app/tool/mcp.py` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL** | Client MCP (MCPClients) | Manter opcional |
| `app/bedrock.py` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL** | Cliente AWS Bedrock | Manter opcional |
| `app/tool/browser_use_tool.py` | KEEP_OPTIONAL | INVESTIGATE | **KEEP_OPTIONAL / INVESTIGATE** | Registrado no Manus; depende de browser_use + playwright | Investigar dependências |
| `app/tool/crawl4ai.py` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL / INVESTIGATE** | Lazy import; falha graciosa se ausente | Manter; confirmar desuso |
| `app/tool/web_search.py` + `app/tool/search/` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL / INVESTIGATE** | Busca em múltiplos engines | Manter opcional |
| `app/tool/chart_visualization/` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL / INVESTIGATE** | Visualização de dados (Node.js + Puppeteer) | Manter opcional |
| `app/tool/bash.py` | KEEP_OPTIONAL | KEEP_OPTIONAL | **KEEP_OPTIONAL / INVESTIGATE** | Execução shell (incompatível Windows) | Manter; revisar adequação |
| `app/tool/planning.py` | KEEP_CORE | KEEP_OPTIONAL | **KEEP_OPTIONAL** | PlanningTool; usado por PlanningFlow | Manter opcional |
| `logs/`, `__pycache__/`, `.pytest_cache`, `*.pyc` | — | DEFER_FUTURE | **REMOVE_CANDIDATE_AFTER_PROOF_ONLY** | Artefatos de runtime/teste; não versionados | Limpar apenas quando houver prova de não-versionamento e sem impacto no runtime |

---

## 3. Decisões Consolidadas Obrigatórias

### KEEP_CORE (manter, testar, proteger)

- `app/agent/` (base, react, toolcall, manus, browser, mcp, swe, data_analysis)
- `app/flow/` (base, flow_factory, planning)
- `app/prompt/` (manus, toolcall, browser, swe, planning, mcp, visualization)
- `app/config.py`
- `app/llm.py`
- `app/schema.py`
- `app/exceptions.py`
- `app/logger.py`
- `app/tool/base.py`
- `app/tool/tool_collection.py`
- `app/tool/terminate.py`
- `app/tool/ask_human.py`

### KEEP_PROTECTED

- `app/tool/create_chat_completion.py` — tool de output LLM estruturado, usada como tool padrão por `ToolCallAgent`. É o mecanismo que força o LLM a responder em formato estruturado (ToolCall). Removê-la quebraria o ciclo de conversa de todos os agentes.
- `app/tool/python_execute.py` — registrada no Manus e ligada ao fluxo principal de execução local.
- `app/tool/str_replace_editor.py` — registrada no Manus, apesar de depender de `file_operators`.

### KEEP_PROTECTED / INVESTIGATE

- `app/tool/file_operators.py` — KEEP_PROTECTED porque está acoplado a `app.sandbox.client.SANDBOX_CLIENT`. Mesmo com `use_sandbox=false`, o import permanece. Desacoplamento futuro necessário.

### KEEP_VALIDATED_TOOL (manter, proteger como ativo do fork)

- `app/integrations/daytona_http.py`
- `app/tool/daytona_sandbox.py`
- `app/tool/image_generator.py`

### KEEP_LOCAL_RUNTIME_OUTPUT

- `output_images/` — diretório escrito por `ImageGeneratorTool`. Não apagar.

### KEEP_VALIDATION_UTILS

- `scripts/validation/validate_modules.py` — utilitário usado na validação modular consolidada. Deve ser preservado para comparação entre relatórios e revalidação controlada.

### QUARANTINE_FOR_FIX (manter no repositório, isolar de validação padrão)

- `app/sandbox/` — Docker local. Import OK, runtime falha no Windows (socket + named pipe).
- `tests/sandbox/` — única suíte de testes existente. Não está saudável no ambiente atual: 13 falhas, 10 erros, 2 passes registrados. Concentrada no caminho Docker/sandbox local.

### LEGACY_DEPENDENCY / INVESTIGATE

- `app/daytona/` (sandbox.py, tool_base.py)
- `app/tool/sandbox/` (sb_shell_tool, sb_files_tool, sb_browser_tool, sb_vision_tool)
- `app/agent/sandbox_agent.py` — LEGACY_DEPENDENCY / INVESTIGATE
- `app/tool/computer_use_tool.py` — LEGACY_DEPENDENCY / INVESTIGATE

### KEEP_OPTIONAL

- `app/mcp/` e `app/tool/mcp.py`
- `app/bedrock.py`
- `app/tool/web_search.py` e `app/tool/search/` — KEEP_OPTIONAL / INVESTIGATE
- `app/tool/crawl4ai.py` — KEEP_OPTIONAL / INVESTIGATE
- `app/tool/chart_visualization/` — KEEP_OPTIONAL / INVESTIGATE
- `app/tool/bash.py` — KEEP_OPTIONAL / INVESTIGATE
- `app/tool/planning.py`
- `app/tool/browser_use_tool.py` — KEEP_OPTIONAL / INVESTIGATE

### REMOVE_CANDIDATE_AFTER_PROOF_ONLY

- `logs/` — arquivos de log locais, somente quando não versionados.
- `__pycache__/`, `.pytest_cache`, `*.pyc` — artefatos de compilação/teste, somente após prova de não-impacto no runtime.

---

## 4. Decisão sobre Docker e Sandbox Local

### Estado real do ambiente

- **Docker Desktop existe** no PC do usuário. Foi validado anteriormente via CLI (`docker --version`, `docker ps`, criação de containers).
- **Durante a execução do Relatório 1** (validação de runtime), o Docker estava **desligado por decisão do usuário** (etapa anterior já concluída).
- **Durante a execução do Relatório 2** (auditoria independente), `docker version`, `docker info` e `docker ps` falharam com `(2, 'CreateFile', 'O sistema não pode encontrar o arquivo especificado.')` — mesmo sintoma de Docker desligado ou named pipe `//./pipe/dockerDesktopLinuxEngine` indisponível.
- **Em validação anterior com Docker ativo**, houve falha na camada de terminal/socket interativo: `RuntimeError: Failed to get socket connection` em `app/sandbox/core/terminal.py:71`.

### Decisão

1. **`app/sandbox/` permanece QUARANTINE_FOR_FIX.** Docker não é o problema único — mesmo com Docker ativo, o terminal interativo via socket falha no Windows.
2. **`tests/sandbox/` permanece QUARANTINE_FOR_FIX.** Os 25 testes dependem de Docker local e a suíte não está saudável: em execução registrada, 13 falhas, 10 erros e 2 passes. As falhas concentram-se no caminho Docker/sandbox local.
3. **Não remover.** Ambos os diretórios ficam no repositório aguardando desacoplamento/correção futura.
4. **Isolar da validação padrão.** Adicionar marcador `@pytest.mark.docker` aos testes de sandbox.
5. **O caminho validado para execução remota** é `app/tool/daytona_sandbox.py` + `app/integrations/daytona_http.py` (HTTP), não o sandbox Docker local.

---

## 5. Decisão sobre Daytona

### Estado atual

O fork local tem **dois caminhos Daytona** coexistindo:

| Caminho | Status | Import | Uso no Manus |
|---------|--------|--------|--------------|
| `app/integrations/daytona_http.py` + `app/tool/daytona_sandbox.py` | **Validado** (caminho ativo) | PASS | `DaytonaSandboxTool` registrado no Manus |
| `app/daytona/` + `app/tool/sandbox/` + `app/agent/sandbox_agent.py` + `app/tool/computer_use_tool.py` | **Legado** (SDK pip) | FAIL (SDK `daytona` não instalado) | Não usado |

### Decisão

1. **`app/integrations/daytona_http.py` e `app/tool/daytona_sandbox.py`** são o caminho validado atual. **KEEP_VALIDATED_TOOL.** Não misturar com limpeza de sandbox Docker ou Daytona legado.
2. **`app/daytona/`** (sandbox.py, tool_base.py) é LEGACY_DEPENDENCY. Não remover ainda porque existem importadores ativos.
3. **`app/agent/sandbox_agent.py`** e **`app/tool/computer_use_tool.py`** são LEGACY_DEPENDENCY / INVESTIGATE. Dependem de `app.daytona.*` e não são registrados no Manus atual. Mapear todos os importadores antes de decidir.
4. **`app/tool/sandbox/`** (4 tools) é LEGACY_DEPENDENCY / INVESTIGATE. Importam `app.daytona.tool_base`. Não são usados pelo Manus atual.
5. **Criar fase futura** para decidir o destino do Daytona legado — após desacoplamento modular e testes de boot.

---

## 6. Decisão sobre Geração de Imagem

1. **`app/tool/image_generator.py`** fica como KEEP_VALIDATED_TOOL. Está registrado no Manus como `generate_image` e é funcional.
2. **`output_images/`** fica como KEEP_LOCAL_RUNTIME_OUTPUT. O ImageGeneratorTool salva imagens (arquivos `desenho_*.jpg`) neste diretório.
3. **Não apagar `output_images/`.** É output local de runtime, não lixo.
4. **Futuramente** pode haver política de `.gitignore` com `.local_data/output_images` ou mover para `.local_data/`, mas não agora.
5. **Este módulo serve como prova de conceito** para a futura Skill Adapter / API Execution Layer.

---

## 7. O que Não Remover Agora

| Categoria | Itens |
|-----------|-------|
| **Core de agentes** | `app/agent/` (todos), `app/flow/`, `app/prompt/`, `app/config.py`, `app/llm.py`, `app/schema.py`, `app/exceptions.py`, `app/logger.py` |
| **Tools registradas no Manus** | `python_execute`, `browser_use`, `str_replace_editor`, `ask_human`, `generate_image`, `terminate`, `daytona_sandbox` |
| **Tools base** | `app/tool/base.py`, `app/tool/tool_collection.py`, `app/tool/create_chat_completion.py` |
| **Tools protegidas** | `app/tool/create_chat_completion.py`, `app/tool/python_execute.py`, `app/tool/str_replace_editor.py`, `app/tool/file_operators.py` |
| **Sandbox local** | `app/sandbox/`, `tests/sandbox/` — mesmo falhando, não remover |
| **Daytona legado** | `app/daytona/`, `app/tool/sandbox/`, `app/agent/sandbox_agent.py`, `app/tool/computer_use_tool.py` — ainda existem importadores |
| **File operators** | `app/tool/file_operators.py` — acoplado ao sandbox client |
| **Str replace editor** | `app/tool/str_replace_editor.py` — registrado no Manus |
| **MCP** | `app/mcp/`, `app/tool/mcp.py` — opcional, mas integrado |
| **Bedrock** | `app/bedrock.py` — opcional, mas referenciado por `app/llm.py` |
| **Browser/search/crawl/chart** | `app/tool/browser_use_tool.py`, `app/tool/web_search.py`, `app/tool/search/`, `app/tool/crawl4ai.py`, `app/tool/chart_visualization/`, `app/tool/bash.py`, `app/tool/planning.py` |
| **Imagem** | `app/tool/image_generator.py`, `output_images/` |
| **Integração validada** | `app/integrations/daytona_http.py`, `app/tool/daytona_sandbox.py` |
| **Utilitários de validação** | `scripts/validation/validate_modules.py` |
| **Dependências** | `requirements.txt`, `setup.py` — não alterar sem checklist |

---

## 8. Próximas Fases Recomendadas

### Fase 2A — Consolidar Plano e Decisão

- Sincronizar `MODULE_DISPOSITION_PLAN_v0_1.md` e este documento
- Atualizar contagens por classificação
- Revisar checklist de limpeza com os achados de runtime

### Fase 2B — Criar Testes Mínimos de Boot

- Teste de import/registry do core:
  ```python
  from app.agent.manus import Manus; m = Manus()
  ```
- Teste de bootstrap do `ToolCollection` com tools registradas
- Teste de compilação/import de cada módulo KEEP_CORE
- Alvo: `tests/` fora de `tests/sandbox/`

### Fase 2C — Isolar Sandbox Docker da Validação Padrão

- Adicionar `pytest.ini` ou `pyproject.toml` com `asyncio_default_fixture_loop_scope = "function"`
- Marcar `tests/sandbox/*` com `@pytest.mark.docker`
- Configurar exceção: `pytest -m "not docker"` para CI/local sem Docker

### Fase 2D — Mapear e Decidir Daytona Legado

- Listar todos os importadores de `app.daytona.*`
- Confirmar se `app/agent/sandbox_agent.py` e `app/tool/computer_use_tool.py` têm entry points ativos
- Se confirmado desuso: manter como `LEGACY_DEPENDENCY / INVESTIGATE` até prova suficiente
- Se ainda usado: documentar, manter e planejar desacoplamento

### Fase 2E — Avaliar Remoção Controlada (só após 2A–2D)

- Remover apenas módulos com:
  - Confirmação de não-uso por 30 dias
  - Testes de boot passando sem o módulo
  - Branch separada com rollback documentado

### Fase 3 — GraphStore Binário Fechado (após Fase 2B)

- Iniciável assim que a consolidação documental (Fase 2A) e os testes mínimos de boot/import/registry (Fase 2B) estiverem concluídos
- Retomar planejamento de `app/integrations/graphstore_cli.py`
- Criar `app/tool/graphstore_memory.py`
- Atualizar `.gitignore` com `.local_data/`
- **Não requer** conclusão da remoção estrutural de módulos legados (Fases 2C–2E)

### Futuro — Skill Adapter e Provider Registry

- Criar `docs/SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT_v0_1.md`
- Implementar `app/skills/router.py`, adapters, validadores
- Registrar providers configuráveis pelo usuário

---

## 9. Conclusão Final

1. **Não remover código ainda.** O projeto compila, não tem dependências quebradas, mas 8 módulos legados falham import e a cobertura de testes é zero fora de sandbox.
2. **Não alterar dependências ainda.** `requirements.txt` e `setup.py` permanecem intocados até a Fase 2E.
3. **Usar os achados para guiar desacoplamento seguro.** A tabela de consenso (seção 2) e as decisões obrigatórias (seção 3) são o mapa para as próximas fases.
4. **GraphStore continua pausado** até concluir a consolidação documental e os testes mínimos de boot/import/registry das Fases 2A–2B. A remoção estrutural de módulos legados (Fases 2C–2E) não precisa estar concluída para retomar GraphStore, desde que o core esteja protegido.
5. **Nenhuma limpeza automática foi autorizada.** Toda remoção futura exige branch separada, checklist de validação e rollback documentado.

---

*Documento consolidado em 2026-06-25 a partir de 4 relatórios independentes de validação modular.*
