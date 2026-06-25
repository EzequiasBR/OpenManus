# Module Disposition Plan — v0.1

> **Objetivo:** Criar um plano de decisão por módulo para o fork local OpenManus antes de qualquer limpeza estrutural, remoção de dependências ou continuação da integração GraphStore.
>
> **Baseado em:** `REPOSITORY_INVENTORY.md`, `REPOSITORY_AUDIT.md`, `DEPENDENCY_AUDIT.md`, `GRAPHSTORE_EXISTING_PATTERN_AUDIT.md`, `GRAPHSTORE_CLOSED_BINARY_INTEGRATION_DECISION_v0_1.md`, `MODULE_VALIDATION_CONSOLIDATED_DECISION_v0_1.md`, `scripts/validation/validate_modules.py`, `reports/dependency_snapshots/pip_freeze_current_2026_06_24.txt`
>
> **Regra:** Nenhum código foi alterado. Nenhuma limpeza foi executada. Este documento é apenas planejamento.
>
> **Data:** 25/06/2026

> **Estado desta revisão:** a validação modular foi executada por dois agentes independentes, com metodologias complementares, e consolidada em `MODULE_VALIDATION_CONSOLIDATED_DECISION_v0_1.md`. Este plano já incorpora essa consolidação e **não autoriza limpeza automática**.

---

## Classificações

| Código | Significado | Ação |
|--------|-------------|------|
| **KEEP_CORE** | Módulo necessário para funcionamento atual da Manus | Manter, testar, proteger |
| **KEEP_PROTECTED** | Módulo que não deve ser removido agora, mesmo exigindo desacoplamento futuro | Manter, proteger, investigar depois |
| **KEEP_VALIDATED_TOOL** | Módulo/ferramenta já validado no fork local | Manter, criar teste formal |
| **KEEP_OPTIONAL** | Útil, mas opcional | Manter, pode virar extras |
| **KEEP_LOCAL_RUNTIME_OUTPUT** | Diretório/artefato local necessário ao runtime atual | Preservar; não tratar como lixo |
| **KEEP_VALIDATION_UTILS** | Utilitário de validação usado para auditoria e comparação independente | Manter, versionar e reutilizar |
| **QUARANTINE_FOR_FIX** | Deve continuar no repositório, mas fora da validação padrão até correção | Isolar, corrigir ou desacoplar em fase própria |
| **LEGACY_DEPENDENCY** | Caminho legado ainda referenciado por imports ou entry points | Mapear, desacoplar, só então decidir |
| **INVESTIGATE** | Requer análise adicional antes de decisão | Investigar antes de qualquer ação |
| **DEFER_FUTURE** | Pode ser útil em fase futura, mas não entra no MVP atual | Documentar, não remover |
| **REMOVE_CANDIDATE_AFTER_PROOF_ONLY** | Candidato à remoção futura somente após prova de não-uso e validação de boot | Testar, confirmar não-uso, remover em branch separada |

---

## 1. Core Runtime

### 1.1 `app/config.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/config.py` (~399 linhas) |
| **Origem** | Original, modificado localmente (commit `4a05092`) |
| **Função** | Singleton de configuração: carregamento TOML, `env:` resolver, settings Pydantic (LLM, Sandbox, Daytona, MCP, RunFlow) |
| **Dependências** | `pydantic`, `tomli` (stdlib `tomllib`), `os`, `threading`, `pathlib`, `json` |
| **Evidência de uso** | Importado por `app/agent/manus.py`, `app/llm.py`, `app/logger.py`, `app/tool/daytona_sandbox.py`, `app/tool/image_generator.py`, `main.py`, `run_flow.py`, `run_mcp.py` |
| **Risco se remover** | Crash total da aplicação |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. Criar testes unitários para parsing TOML e `resolve_env()`. |

### 1.2 `app/llm.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/llm.py` (~766 linhas) |
| **Origem** | Original |
| **Função** | Cliente LLM central (OpenAI/Azure/Ollama/Bedrock), token counting (tiktoken), retry (tenacity), multimodal |
| **Dependências** | `openai`, `tiktoken`, `tenacity`, `pydantic` |
| **Evidência de uso** | Importado por `app/agent/toolcall.py` (todos os agentes) |
| **Risco se remover** | Crash total — nenhum LLM functionaria |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. Testar conectividade Groq como teste de regressão. |

### 1.3 `app/schema.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/schema.py` (~187 linhas) |
| **Origem** | Original |
| **Função** | Modelos de dados: `Message`, `ToolCall`, `AgentState`, `Memory`, `ToolChoice`, `Response` |
| **Dependências** | `pydantic` |
| **Evidência de uso** | Importado por agents, tools, flows, prompt |
| **Risco se remover** | Crash total — toda comunicação LLM depende destes modelos |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. |

### 1.4 `app/exceptions.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/exceptions.py` (~13 linhas) |
| **Origem** | Original |
| **Função** | `ToolError`, `OpenManusError`, `TokenLimitExceeded` |
| **Evidência de uso** | Importado por `app/tool/base.py`, `app/agent/toolcall.py` |
| **Risco se remover** | Quebra captura de exceções específicas |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. |

### 1.5 `app/logger.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/logger.py` (~42 linhas) |
| **Origem** | Original |
| **Função** | Logger loguru singleton (console + arquivo rotacionado) |
| **Dependências** | `loguru` |
| **Evidência de uso** | Importado como `from app.logger import logger` em agents e tools |
| **Risco se remover** | Perda de logging estruturado |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. Investigar convivência com `app/utils/logger.py` (structlog) — possível duplicação. |

### 1.6 `app/__init__.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/__init__.py` |
| **Origem** | Original |
| **Função** | Restringe Python 3.11–3.13 |
| **Risco se remover** | Baixo (validação de versão apenas) |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. |

---

## 2. Agentes

### 2.1 `app/agent/base.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/base.py` (~200 linhas) |
| **Origem** | Original, modificado localmente (commit `4a05092`) |
| **Função** | `BaseAgent` — classe abstrata: memória, máquina de estados, step loop, cleanup |
| **Evidência de uso** | Base de toda hierarquia: `ReActAgent` → `ToolCallAgent` → `Manus`, `BrowserAgent`, etc. |
| **Risco se remover** | Crash total de todos os agentes |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. Nenhuma alteração sem testar todos os agentes que herdam dela. |

### 2.2 `app/agent/react.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/react.py` (~150 linhas) |
| **Origem** | Original |
| **Função** | `ReActAgent` — loop think/act abstrato |
| **Evidência de uso** | Herdado por `ToolCallAgent` |
| **Risco se remover** | Crash de todos os agentes que dependem do loop |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. |

### 2.3 `app/agent/toolcall.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/toolcall.py` (~250 linhas) |
| **Origem** | Original |
| **Função** | `ToolCallAgent` — chamada de tools via LLM, limites de token, retries |
| **Evidência de uso** | Herdado por `Manus`, `BrowserAgent`, `MCPAgent`, `SWEAgent`, `DataAnalysis`, `SandboxManus` |
| **Risco se remover** | Crash de todos os agentes concretos |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. |

### 2.4 `app/agent/manus.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/manus.py` |
| **Origem** | Original, modificado localmente (commits `6b403e6`, `8cb20ba`) |
| **Função** | `Manus` — agente versátil com 7 tools registradas + MCP dinâmico |
| **Tools registradas** | `PythonExecute`, `BrowserUseTool`, `StrReplaceEditor`, `AskHuman`, `ImageGeneratorTool`, `Terminate`, `DaytonaSandboxTool` |
| **Evidência de uso** | Entry point `main.py` — agente principal |
| **Risco se remover** | Perda do agente principal |
| **Classificação** | **KEEP_CORE** |
| **Ação** | Manter. Criar teste de inicialização. Documentar ferramentas registradas. |

### 2.5 `app/agent/browser.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/browser.py` (~200 linhas) |
| **Origem** | Original, modificado localmente (commit `4a05092`) |
| **Função** | `BrowserAgent` — automação de navegador via `BrowserUseTool` |
| **Evidência de uso** | Usado pelo `Manus` para tarefas de navegação |
| **Risco se remover** | Perda de capacidade de automação de browser |
| **Classificação** | **KEEP_OPTIONAL** |
| **Ação** | Manter. Depende de `browser-use` + `playwright`. Pode falhar em Windows sem config. |

### 2.6 `app/agent/mcp.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/mcp.py` (~100 linhas) |
| **Origem** | Original |
| **Função** | `MCPAgent` — conexão a servidores MCP via stdio/SSE |
| **Evidência de uso** | Entry point `run_mcp.py` |
| **Risco se remover** | Perda do entry point MCP dedicado |
| **Classificação** | **KEEP_OPTIONAL** |
| **Ação** | Manter. Usado pelo Manus via `MCPClients`. |

### 2.7 `app/agent/swe.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/swe.py` (~30 linhas) |
| **Origem** | Original |
| **Função** | `SWEAgent` — agente de programação (Bash + StrReplaceEditor) |
| **Evidência de uso** | Nenhum entry point conhecido o utiliza diretamente |
| **Risco se remover** | Perda de agente especializado de programação |
| **Classificação** | **KEEP_OPTIONAL** |
| **Ação** | Manter. Herdado de `ToolCallAgent`. Útil em cenários de engenharia de software. |

### 2.8 `app/agent/data_analysis.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/data_analysis.py` (~30 linhas) |
| **Origem** | Original |
| **Função** | `DataAnalysis` — agente de análise/visualização de dados |
| **Evidência de uso** | Usado pelo `PlanningFlow` quando `use_data_analysis_agent=true` |
| **Risco se remover** | Perda de agente de análise |
| **Classificação** | **KEEP_OPTIONAL** |
| **Ação** | Manter. Requer `chart_visualization/` (Node.js + Puppeteer). |

### 2.9 `app/agent/sandbox_agent.py`

| Campo | Valor |
|-------|-------|
| **Caminho** | `app/agent/sandbox_agent.py` (~30 linhas) |
| **Origem** | Original, herdado do branch sandbox |
| **Função** | `SandboxManus` — agente baseado em sandbox Daytona SDK |
| **Evidência de uso** | Entry point `sandbox_main.py`. **Não usado na configuração local.** |
| **Dependências ausentes** | Requer SDK `daytona` não instalado |
| **Risco se remover** | Entry point `sandbox_main.py` quebraria (já quebra sem SDK) |
| **Classificação** | **INVESTIGATE** |
| **Ação** | Não remover. Tratar como caminho legado/acoplado ao SDK Daytona e investigar antes de qualquer decisão estrutural. |

---

## 3. Tools

### 3.1 Tools Core (registradas no Manus)

| Caminho | Tool | Origem | Classificação | Observação |
|---------|------|--------|---------------|------------|
| `app/tool/base.py` | `BaseTool`, `ToolResult` | Original | **KEEP_CORE** | Classe base de todas as tools |
| `app/tool/tool_collection.py` | `ToolCollection` | Original | **KEEP_CORE** | Gerenciamento de tools |
| `app/tool/terminate.py` | `Terminate` | Original | **KEEP_CORE** | Finaliza interação |
| `app/tool/bash.py` | `Bash` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Execução shell; revisar adequação ao ambiente Windows |
| `app/tool/python_execute.py` | `PythonExecute` | Original | **KEEP_PROTECTED** | Registrada no Manus; não remover antes de testes mínimos de boot/import |
| `app/tool/str_replace_editor.py` | `StrReplaceEditor` | Original | **KEEP_PROTECTED** | Registrada no Manus e ligada ao fluxo de edição/arquivos |
| `app/tool/ask_human.py` | `AskHuman` | Original | **KEEP_CORE** | Input do usuário |
| `app/tool/browser_use_tool.py` | `BrowserUseTool` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Depende de `browser-use` + `playwright`; ainda registrada no Manus |
| `app/tool/web_search.py` | `WebSearch` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Chamadas de API externa; backend de busca opcional |
| `app/tool/create_chat_completion.py` | `CreateChatCompletion` | Original | **KEEP_PROTECTED** | Saída LLM estruturada usada como tool padrão de `ToolCallAgent` |
| `app/tool/planning.py` | `PlanningTool` | Original | **KEEP_OPTIONAL** | Gerencia planos multi-passo |
| `app/tool/file_operators.py` | `FileOperator` | Original | **KEEP_PROTECTED / INVESTIGATE** | Abstração de I/O acoplada ao `SANDBOX_CLIENT` |
| `app/tool/mcp.py` | `MCPClientTool`, `MCPClients` | Original | **KEEP_OPTIONAL** | Protocolo MCP client |

**Nota:** Nenhuma tool core possui testes unitários. Risco médio-alto.

### 3.2 Tools Adicionadas Localmente

| Caminho | Tool | Origem | Classificação | Observação |
|---------|------|--------|---------------|------------|
| `app/tool/daytona_sandbox.py` | `DaytonaSandboxTool` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | Validada via scripts. Contrato documentado. |
| `app/tool/image_generator.py` | `ImageGeneratorTool` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | Validada manualmente. Sem teste formal. |

### 3.3 Tools Opcionais (não registradas no Manus)

| Caminho | Tool | Origem | Classificação | Observação |
|---------|------|--------|---------------|------------|
| `app/tool/crawl4ai.py` | `Crawl4aiTool` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Lazy import. Falha graciosa se ausente. |
| `app/tool/computer_use_tool.py` | `ComputerUseTool` | Original | **INVESTIGATE** | Automação de desktop. Risco de segurança. Não registrada no Manus. Requer confirmação de uso. |

### 3.4 `app/tool/search/` (Motores de Busca)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `base.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Classe base do backend de busca |
| `google_search.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Requer API key Google |
| `baidu_search.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Requer API key Baidu |
| `bing_search.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Requer API key Bing |
| `duckduckgo_search.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Sem API key |

**Nota:** Gerenciados por `app/tool/web_search.py` com fallback. Nenhum é importado diretamente pelo Manus — todos via `WebSearch`.

### 3.5 `app/tool/sandbox/` (SDK Daytona Original — Caminho Legado)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `sb_shell_tool.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Depende de SDK `daytona` não instalado |
| `sb_files_tool.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Depende de SDK `daytona` não instalado |
| `sb_browser_tool.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Depende de SDK `daytona` não instalado |
| `sb_vision_tool.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Depende de SDK `daytona` não instalado |

### 3.6 `app/tool/chart_visualization/` (Visualização de Gráficos)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `__init__.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Re-exporta |
| `chart_prepare.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Gera CSV + JSON |
| `data_visualization.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Spawns `npx ts-node` |
| `python_execute.py` | Original | **KEEP_OPTIONAL / INVESTIGATE** | Execução Python |
| `package.json` | Original | **KEEP_OPTIONAL** | Dependências Node |
| `tsconfig.json` | Original | **KEEP_OPTIONAL** | Config TypeScript |
| `src/chartVisualize.ts` | Original | **KEEP_OPTIONAL** | Renderização VChart |

**Nota:** Requer Node.js + Puppeteer instalados. Só usado pelo `DataAnalysis` agent quando `use_data_analysis_agent=true`.

---

## 4. Integrações

### 4.1 `app/integrations/`

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `__init__.py` | **Adicionado localmente** | **KEEP_CORE** | Vazio, necessário para pacote |
| `daytona_http.py` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | Cliente HTTP Daytona (~490 linhas). Validado. |

### 4.2 `app/daytona/` (SDK Daytona Original — Caminho Legado)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `sandbox.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Requer SDK `daytona` não instalado |
| `tool_base.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Requer SDK `daytona` não instalado |
| `README.md` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Documentação do fluxo SDK |

**Evidência consolidada:** `app/daytona/` não é o caminho validado atual do Manus, mas ainda é importado por `app/agent/sandbox_agent.py`, `app/tool/computer_use_tool.py` e `app/tool/sandbox/*`. Portanto, é legado/acoplado e não pode ser removido ainda.

---

## 5. Flows

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/flow/__init__.py` | Original | **KEEP_CORE** | Vazio |
| `app/flow/base.py` | Original | **KEEP_CORE** | Classe base abstrata |
| `app/flow/flow_factory.py` | Original | **KEEP_CORE** | Factory method |
| `app/flow/planning.py` | Original | **KEEP_CORE** | Orquestra agentes. Entry point `run_flow.py`. |

---

## 6. Prompts

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/prompt/__init__.py` | Original | **KEEP_CORE** | Vazio |
| `app/prompt/manus.py` | Original | **KEEP_CORE** | System prompt do Manus |
| `app/prompt/toolcall.py` | Original | **KEEP_CORE** | Next step prompt |
| `app/prompt/browser.py` | Original | **KEEP_OPTIONAL** | System prompt do BrowserAgent |
| `app/prompt/swe.py` | Original | **KEEP_OPTIONAL** | Prompts do SWEAgent |
| `app/prompt/planning.py` | Original | **KEEP_OPTIONAL** | System prompt do Planning |
| `app/prompt/mcp.py` | Original | **KEEP_OPTIONAL** | System prompt do MCPAgent |
| `app/prompt/visualization.py` | Original | **KEEP_OPTIONAL** | Prompts do DataAnalysis |

**Nota:** Todos são apenas strings de texto. Risco mínimo.

---

## 7. Sandbox Docker Local

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/sandbox/__init__.py` | Original | **QUARANTINE_FOR_FIX** | Pacote do sandbox Docker local |
| `app/sandbox/client.py` | Original | **QUARANTINE_FOR_FIX** | Factory (BaseSandboxClient, LocalSandboxClient) |
| `app/sandbox/core/sandbox.py` | Original | **QUARANTINE_FOR_FIX** | DockerSandbox lifecycle |
| `app/sandbox/core/terminal.py` | Original | **QUARANTINE_FOR_FIX** | AsyncDockerizedTerminal |
| `app/sandbox/core/manager.py` | Original | **QUARANTINE_FOR_FIX** | SandboxManager (pool) |
| `app/sandbox/core/exceptions.py` | Original | **QUARANTINE_FOR_FIX** | Exceções |

**Nota consolidada:** Docker existe no PC e já foi validado manualmente em fases anteriores, mas `app/sandbox/` não é confiável agora. Em algumas validações o Docker estava desligado ou com named pipe indisponível; em outras, com Docker ativo, o fluxo falhou na camada sandbox/terminal/socket. Decisão final: **não remover**, deixar em quarentena para correção/desacoplamento futuro.

---

## 8. MCP

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/mcp/__init__.py` | Original | **KEEP_OPTIONAL** | Vazio |
| `app/mcp/server.py` | Original | **KEEP_OPTIONAL** | Servidor FastMCP. Entry point `run_mcp_server.py`. |

---

## 9. Utils

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/utils/__init__.py` | Original | **KEEP_CORE** | Comentário apenas |
| `app/utils/files_utils.py` | Original | **KEEP_CORE** | Limpeza de path, exclusão |
| `app/utils/logger.py` | Original | **INVESTIGATE** | Segundo logger (structlog). Coconcorre com `app/logger.py` (loguru). Investigar qual é o usado, se ambos são necessários. |

---

## 10. Protocolo A2A — Arquivado

O protocolo A2A foi movido para `archive/openmanus/a2a_protocol_unvalidated/` por ser **DEFER_FUTURE**: não possui contrato funcional, não foi testado localmente e não há integração com o entry point principal.

| Caminho original | Destino no archive | Classificação | Observação |
|---|---|---|---|
| `protocol/a2a/__init__.py` | `archive/openmanus/a2a_protocol_unvalidated/a2a/__init__.py` | **DEFER_FUTURE** | Vazio |
| `protocol/a2a/app/main.py` | `archive/openmanus/a2a_protocol_unvalidated/a2a/app/main.py` | **DEFER_FUTURE** | Servidor Starlette + uvicorn |
| `protocol/a2a/app/agent.py` | `archive/openmanus/a2a_protocol_unvalidated/a2a/app/agent.py` | **DEFER_FUTURE** | A2AManus wrapper |
| `protocol/a2a/app/agent_executor.py` | `archive/openmanus/a2a_protocol_unvalidated/a2a/app/agent_executor.py` | **DEFER_FUTURE** | ManusExecutor |
| `protocol/a2a/app/README.md` | `archive/openmanus/a2a_protocol_unvalidated/a2a/app/README.md` | **DEFER_FUTURE** | Documentação |

**Nota:** Módulo experimental sem contrato funcional. Preservado para referência futura, mas sem previsão de reativação. O diretório `protocol/a2a/` original foi removido.

---

## 11. Entry Points

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `main.py` | Original | **KEEP_CORE** | Entry point principal: `Manus` agent |
| `run_flow.py` | Original | **KEEP_OPTIONAL** | PlanningFlow com agentes |
| `run_mcp.py` | Original | **KEEP_OPTIONAL** | MCPAgent via stdio/SSE |
| `run_mcp_server.py` | Original | **KEEP_OPTIONAL** | Servidor MCP (FastMCP) |
| `sandbox_main.py` | Original (herdado) | **LEGACY_DEPENDENCY / INVESTIGATE** | Entry point do caminho legado `SandboxManus`; não remover antes de mapear dependências |
| `test_groq.py` | **Adicionado localmente** | **INVESTIGATE** | Listado no `.gitignore` mas commitado. Decidir: remover tracking ou versionar. |

---

## 12. Scripts

### 12.1 Scripts de Teste/Regressão

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `scripts/test_daytona_http.py` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | Smoke test DaytonaHTTPClient |
| `scripts/test_daytona_sandbox_tool.py` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | 3 cenários da DaytonaSandboxTool |
| `scripts/test_manus_daytona_tool.py` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | End-to-end Manus + daytona_sandbox |

### 12.2 Scripts de Diagnóstico (Candidatos a Consolidação)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `scripts/create_daytona_sandbox.py` | **Adicionado localmente** | **DEFER_FUTURE** | Coberto por testes formais |
| `scripts/delete_daytona_sandbox.py` | **Adicionado localmente** | **DEFER_FUTURE** | Coberto por testes formais |
| `scripts/inspect_daytona_file_upload.py` | **Adicionado localmente** | **DEFER_FUTURE** | Exploratório |
| `scripts/inspect_daytona_toolbox_routes.py` | **Adicionado localmente** | **DEFER_FUTURE** | Exploratório |
| `scripts/test_daytona_code_execution_flow.py` | **Adicionado localmente** | **DEFER_FUTURE** | Coberto por `test_daytona_sandbox_tool.py` |
| `scripts/test_daytona_file_api.py` | **Adicionado localmente** | **DEFER_FUTURE** | Exploratório |
| `scripts/test_daytona_toolbox_execute.py` | **Adicionado localmente** | **DEFER_FUTURE** | Coberto por `test_daytona_sandbox_tool.py` |

### 12.3 Utilitários de Validação Modular

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `scripts/validation/validate_modules.py` | **Adicionado localmente** | **KEEP_VALIDATION_UTILS** | Utilitário usado na validação modular consolidada; não remover |

---

## 13. Testes

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `tests/sandbox/` | Original | **QUARANTINE_FOR_FIX** | Única suíte formal; falha no ambiente atual e deve sair da validação padrão até correção/desacoplamento. |

---

## 14. Configurações

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `config/config.toml` | **Adicionado localmente** | **KEEP_CORE** | Config ativa. Ignorado pelo `.gitignore`. |
| `config/config.example.toml` | Original | **KEEP_CORE** | Exemplo master versionado |
| `config/config.example-daytona.toml` | Original | **KEEP_OPTIONAL** | Exemplo Daytona |
| `config/config.example-azure.toml` | Original | **KEEP_OPTIONAL** | Exemplo Azure |
| `config/config.example-baidu.toml` | Original | **KEEP_OPTIONAL** | Exemplo Baidu |
| `config/config.example-gemini.toml` | Original | **KEEP_OPTIONAL** | Exemplo Gemini |
| `config/config.example-groq.toml` | Original | **KEEP_OPTIONAL** | Exemplo Groq |
| `config/config.example-jiekou.toml` | Original | **KEEP_OPTIONAL** | Exemplo JiekouAI |
| `config/config.example-ollama.toml` | Original | **KEEP_OPTIONAL** | Exemplo Ollama |
| `config/config.example-openai.toml` | Original | **KEEP_OPTIONAL** | Exemplo OpenAI |
| `config/config.example-openai-compatible.toml` | Original | **KEEP_OPTIONAL** | Exemplo OpenAI-compatível |
| `config/config.example-bytedance.toml` | Original | **KEEP_OPTIONAL** | Exemplo ByteDance |
| `config/config.example-github.toml` | Original | **KEEP_OPTIONAL** | Exemplo GitHub Models |
| `config/config.example.zhipu.toml` | Original | **KEEP_OPTIONAL** | Exemplo Zhipu |
| `config/mcp.example.json` | Original | **KEEP_OPTIONAL** | Config de servidores MCP |
| `.pre-commit-config.yaml` | Original | **KEEP_OPTIONAL** | hooks pre-commit |

---

## 15. Docs e Relatórios

### 15.1 Documentação Atual

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `README.md` | Original | **KEEP_CORE** | README oficial |
| `README_ja.md` | Original | **KEEP_OPTIONAL** | Japonês |
| `README_ko.md` | Original | **KEEP_OPTIONAL** | Coreano |
| `README_zh.md` | Original | **KEEP_OPTIONAL** | Chinês |
| `docs/PROJECT_STATUS.md` | **Adicionado localmente** | **KEEP_CORE** | Status do fork |
| `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` | **Adicionado localmente** | **KEEP_VALIDATED_TOOL** | Contrato Daytona |
| `docs/REPOSITORY_INVENTORY.md` | **Adicionado localmente** | **KEEP_CORE** | Inventário técnico |
| `docs/REPOSITORY_AUDIT.md` | **Adicionado localmente** | **KEEP_CORE** | Auditoria técnica |
| `docs/DEPENDENCY_AUDIT.md` | **Adicionado localmente** | **KEEP_CORE** | Auditoria de dependências |
| `docs/GRAPHSTORE_EXISTING_PATTERN_AUDIT.md` | **Adicionado localmente** | **KEEP_CORE** | Auditoria de padrões |
| `docs/GRAPHSTORE_CLOSED_BINARY_INTEGRATION_DECISION_v0_1.md` | **Adicionado localmente** | **KEEP_CORE** | Decisão GraphStore |
| `docs/MODULE_VALIDATION_CONSOLIDATED_DECISION_v0_1.md` | **Adicionado localmente** | **KEEP_CORE** | Consolidação das duas validações independentes |
| `docs/MODULE_DISPOSITION_PLAN_v0_1.md` | **Adicionado localmente** | **KEEP_CORE** | Este documento |

### 15.2 Relatórios

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `reports/dependency_snapshots/pip_freeze_current_2026_06_24.txt` | **Adicionado localmente** | **KEEP_CORE** | Snapshot de dependências |

### 15.3 Documentação Upstream (não modificada)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `CODE_OF_CONDUCT.md` | Original | **KEEP_OPTIONAL** | Código de conduta |
| `LICENSE` | Original | **KEEP_CORE** | MIT |
| `app/daytona/README.md` | Original | **LEGACY_DEPENDENCY / INVESTIGATE** | Instruções SDK do caminho legado |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/README.md` | Original | **DEFER_FUTURE** | Guia A2A (arquivado) |
| `examples/` | Original | **DEFER_FUTURE** | Exemplos de uso |

---

## 16. Outros

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/bedrock.py` | Original | **KEEP_OPTIONAL** | Cliente AWS Bedrock. Só necessário se usado. |
| `Dockerfile` | Original | **KEEP_OPTIONAL** | Container. Não usado localmente. |
| `.github/` | Original | **KEEP_OPTIONAL** | CI/CD upstream. Não usado no fork. |
| `.gitattributes` | Original | **KEEP_OPTIONAL** | Git attributes |
| `.vscode/` | Original | **KEEP_OPTIONAL** | Configurações VS Code |
| `.local_notes/` | **Adicionado localmente** | **KEEP_OPTIONAL** | Notas locais |
| `assets/` | Original | **KEEP_OPTIONAL** | Assets do README |
| `output_images/` | — | **KEEP_LOCAL_RUNTIME_OUTPUT** | Diretório local de runtime preservado para a geração de imagens |
| `.bak/` | — | **KEEP_OPTIONAL** | Backups |

---

## 17. Resumo por Classificação

| Classificação | Quantidade | Módulos Principais |
|---------------|------------|---------------------|
| **KEEP_CORE** | ~25 | `app/agent/`, `app/flow/`, `app/prompt/`, `app/config.py`, `app/llm.py`, `app/schema.py`, `app/tool/base.py`, `app/tool/tool_collection.py`, `app/tool/terminate.py`, docs centrais, `main.py` |
| **KEEP_PROTECTED** | ~5 | `app/tool/create_chat_completion.py`, `app/tool/python_execute.py`, `app/tool/str_replace_editor.py`, `app/tool/file_operators.py`, módulos base da futura Skill Adapter |
| **KEEP_VALIDATED_TOOL** | ~6 | `daytona_sandbox.py`, `image_generator.py`, `daytona_http.py`, scripts de teste Daytona |
| **KEEP_OPTIONAL** | ~30 | MCP, Bedrock, browser/search/crawl/chart tools, agentes opcionais, exemplos de config, Dockerfile |
| **KEEP_LOCAL_RUNTIME_OUTPUT** | 1 | `output_images/` |
| **KEEP_VALIDATION_UTILS** | 1 | `scripts/validation/validate_modules.py` |
| **QUARANTINE_FOR_FIX** | ~8 | `app/sandbox/`, `tests/sandbox/`, `sandbox_main.py` |
| **LEGACY_DEPENDENCY** | ~8 | `app/daytona/`, `app/tool/sandbox/`, partes herdadas do caminho Daytona SDK |
| **INVESTIGATE** | ~6 | `app/agent/sandbox_agent.py`, `app/tool/computer_use_tool.py`, `app/utils/logger.py`, browser/search/chart opcionais acoplados |
| **DEFER_FUTURE** | ~12 | `archive/openmanus/a2a_protocol_unvalidated/`, `examples/`, scripts exploratórios Daytona, GraphStore futuro |
| **REMOVE_CANDIDATE_AFTER_PROOF_ONLY** | 0 | Nenhum módulo tem prova suficiente para remoção |

---

## 18. Skill Adapter e API Execution Layer

> **Status:** Arquitetura futura obrigatória. Nada implementado ainda.
>
> **Classificação conceitual:** `KEEP_PROTECTED_FOR_FUTURE` para módulos existentes que servirão de base.
>
> **Nota:** Esta seção não autoriza implementação nem limpeza. Apenas documenta a camada futura.

### 18.1 Objetivo

- Permitir que uma skill/protocolo seja transformada em payload estruturado para tools/APIs.
- Permitir uso de skills para geração de imagem/desenho.
- Permitir validação do resultado e correção/retry quando necessário.

### 18.2 Fluxo Futuro

```
Usuário
  └── Manus/Agente
        └── Skill Router
              └── Skill Adapter
                    └── Action Payload
                          └── Tool/API (Pollinations, Daytona, GraphStore, etc.)
                                └── Raw Result
                                      └── Validator
                                            ├── Final (sucesso)
                                            └── Correction/Retry (falha)
```

### 18.3 Diferença entre Skill Adapter e Tool Adapter

| Camada | Função | Exemplo |
|--------|--------|---------|
| **Skill Adapter** | Traduz protocolo/intenção/restrições em payload executável | `SkillRouter.recebe("gerar_desenho")` → valida entrada, monta prompt, escolhe tool |
| **Tool Adapter** | Chama ferramenta concreta com payload já montado | `ImageGeneratorTool.execute(prompt)` ou `DaytonaSandboxTool.execute(code)` |

O Skill Adapter **decide o que fazer**; o Tool Adapter **executa a chamada**.

### 18.4 Módulos Atuais que Devem ser Protegidos (Base da Camada)

| Módulo | Função na Camada Futura | Classificação Atual |
|--------|-------------------------|---------------------|
| `app/agent/manus.py` | Roteador de entrada para skills | **KEEP_CORE** |
| `app/agent/toolcall.py` | Dispatcher de tools chamado pelo Skill Adapter | **KEEP_CORE** |
| `app/tool/` (como um todo) | Catálogo de Tool Adapters | **KEEP_CORE / KEEP_VALIDATED_TOOL / KEEP_OPTIONAL** |
| `app/integrations/` | Wrappers de APIs externas | **KEEP_CORE / KEEP_VALIDATED_TOOL** |
| `app/tool/image_generator.py` | Prova de conceito de skill de imagem | **KEEP_VALIDATED_TOOL** |
| `app/tool/daytona_sandbox.py` | Prova de conceito de execução remota como skill | **KEEP_VALIDATED_TOOL** |
| `app/schema.py` | Base para schemas de Action Payload | **KEEP_CORE** |
| `app/config.py` | Configuração de skills e adapters | **KEEP_CORE** |

### 18.5 Módulos Futuros Previstos

| Módulo | Função | Classificação |
|--------|--------|---------------|
| `app/skills/` | Pacote raiz da camada de skills | **DEFER_FUTURE** |
| `app/skills/router.py` | `SkillRouter` — recebe intenção, roteia para adapter correto | **DEFER_FUTURE** |
| `app/skills/adapters/` | Adapters concretos (imagem, código, busca, memória) | **DEFER_FUTURE** |
| `app/skills/schemas.py` | Schemas Pydantic de Action Payload | **DEFER_FUTURE** |
| `app/validation/` | Validadores de resultado com suporte a retry | **DEFER_FUTURE** |
| `app/integrations/graphstore_cli.py` | Adapter CLI do GraphStore | **DEFER_FUTURE** (já documentado) |
| `app/tool/graphstore_memory.py` | Tool de memória persistente | **DEFER_FUTURE** (já documentado) |

### 18.6 Impacto na Limpeza

A existência desta camada futura **restringe** o que pode ser simplificado ou removido agora:

- **Não remover** nem simplificar tools de imagem (`app/tool/image_generator.py`).
- **Não remover** Daytona validado (`app/tool/daytona_sandbox.py`, `app/integrations/daytona_http.py`).
- **Não remover** padrões de tool call (`app/agent/toolcall.py`, `app/tool/base.py`).
- **Não remover** schemas usados por chamadas estruturadas (`app/schema.py`, `app/tool/base.py`).
- **Não remover** documentação relacionada a skills ou protocolos antes de criar contrato separado.

### 18.7 Relação com GraphStore

```
Skill Adapter
  ├── executa skill (imagem, código, busca)
  ├── valida resultado
  └── registra em GraphStore:
        ├── decisão tomada
        ├── resultado da execução
        ├── validação (aprovado/rejeitado)
        └── memória da skill para reuse futuro
```

**GraphStore não substitui Skill Adapter.** GraphStore é camada de **memória persistente**. Skill Adapter é camada de **execução e roteamento**. Eles são complementares: o Skill Adapter executa, o GraphStore memorializa.

### 18.8 Próximo Documento Recomendado

```
docs/SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT_v0_1.md
```

Escopo sugerido: schema de Action Payload, contratos de adapter, validação mínima com `ImageGeneratorTool`, integração com `ToolCallAgent`.

---

## 19. Critérios Antes da Limpeza

> Nenhuma limpeza deve ser executada até que todos os critérios abaixo sejam atendidos.

### Checklist Obrigatória

- [ ] `git status --short` limpo (sem alterações não commitadas)
- [ ] Testes existentes passando:
  - [ ] `python -m pytest tests/ -v`
  - [ ] `python scripts/validation/validate_modules.py`
  - [ ] `python scripts/test_daytona_http.py`
  - [ ] `python scripts/test_daytona_sandbox_tool.py`
  - [ ] `python scripts/test_manus_daytona_tool.py`
- [ ] Backup/commit antes de qualquer mudança
- [ ] Remoção em branch separada (nunca na main)
- [ ] Uma categoria por vez (não misturar KEEP_OPTIONAL com QUARANTINE_FOR_FIX ou LEGACY_DEPENDENCY)
- [ ] Rollback simples (`git revert` ou `git checkout`)
- [ ] Validação de boot:
  ```bash
  python -c "from app.agent.manus import Manus; m = Manus(); print('Manus OK')"
  ```
- [ ] Validação de Groq:
  ```bash
  python -c "import asyncio; from app.llm import LLM; l=LLM(); asyncio.run(l.ask(['test']))"
  ```
- [ ] Validação de Pollinations:
  ```bash
  python -c "import asyncio; from app.tool.image_generator import ImageGeneratorTool; t=ImageGeneratorTool(); asyncio.run(t.execute(prompt='test'))"
  ```
- [ ] Validação de Daytona:
  ```bash
  python scripts/test_daytona_http.py
  ```
- [ ] Validação de import/compile (todos os módulos):
  ```bash
  python -c "
  import app.config
  import app.schema
  import app.exceptions
  import app.logger
  import app.llm
  import app.agent.base
  import app.agent.react
  import app.agent.toolcall
  import app.agent.manus
  import app.tool.base
  import app.tool.tool_collection
  import app.tool.terminate
  import app.tool.bash
  import app.tool.python_execute
  import app.tool.str_replace_editor
  import app.tool.ask_human
  import app.tool.daytona_sandbox
  import app.tool.image_generator
  import app.integrations.daytona_http
  print('Todos os imports OK')
  "
  ```
- [ ] Revisão manual antes de push

---

## 20. Não Limpar Ainda

> Estes itens devem permanecer intocados até validação completa.

- **Runtime de agentes:** `app/agent/base.py`, `app/agent/react.py`, `app/agent/toolcall.py`, `app/agent/manus.py` — qualquer alteração afeta toda hierarquia.
- **Configuração central:** `app/config.py` — qualquer erro de parsing quebra toda aplicação.
- **Tools validadas:** `app/tool/daytona_sandbox.py`, `app/tool/image_generator.py` — sem testes formais, mas validadas manualmente.
- **Integração Daytona:** `app/integrations/daytona_http.py` — sem alternativa no momento.
- **Geração de imagem:** `app/tool/image_generator.py` — integração validada.
- **Output local de imagem:** `output_images/` — preservar como pasta local de runtime.
- **Padrões de tool call:** `app/agent/toolcall.py`, `app/tool/base.py` — base da futura camada de Skill Adapter.
- **Módulos base da futura camada Skill Adapter:** `app/agent/manus.py`, `app/agent/toolcall.py`, `app/tool/`, `app/integrations/`, `app/schema.py`, `app/config.py` — serão usados como fundação da Skill Adapter e API Execution Layer.
- **Qualquer documentação de skills/protocolos:** Não remover antes de criar contrato separado (`SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT`).
- **Qualquer módulo usado por testes:** Verificar dependências de `tests/sandbox/` antes de alterar `app/sandbox/`.
- **Qualquer módulo cuja origem ainda não esteja clara:** Módulos marcados como **INVESTIGATE** não devem ser alterados.
- **Ferramentas protegidas:** `app/tool/create_chat_completion.py`, `app/tool/python_execute.py`, `app/tool/str_replace_editor.py`, `app/tool/file_operators.py` não devem ser removidas nesta fase.
- **Utilitário de validação:** `scripts/validation/validate_modules.py` deve ser preservado para comparação entre relatórios.
- **`requirements.txt` e `setup.py`:** Não alterar sem seguir a checklist da seção 19.
- **Módulos marcados como QUARANTINE_FOR_FIX:** Não remover — apenas isolar de carregamento padrão.
- **Módulos marcados como LEGACY_DEPENDENCY:** Não remover até mapear todos os importadores e entry points.

---

## 21. Ordem Recomendada de Limpeza Futura

### Fase 0 — Documentação e Decisão por Módulo (atual)

- [x] `docs/REPOSITORY_INVENTORY.md`
- [x] `docs/REPOSITORY_AUDIT.md`
- [x] `docs/DEPENDENCY_AUDIT.md`
- [x] `docs/GRAPHSTORE_EXISTING_PATTERN_AUDIT.md`
- [x] `docs/GRAPHSTORE_CLOSED_BINARY_INTEGRATION_DECISION_v0_1.md`
- [x] `docs/MODULE_VALIDATION_CONSOLIDATED_DECISION_v0_1.md`
- [x] `docs/MODULE_DISPOSITION_PLAN_v0_1.md`

### Fase 1 — Consolidação Sem Remoção

**Alvo:** Atualizar documentação, checklist e nomenclatura sem mover ou remover módulos.

**Ações:**
- Preservar classificações consolidadas
- Não autorizar limpeza automática
- Manter `scripts/validation/validate_modules.py` como utilitário comparativo

### Fase 2A — Consolidação do Plano

**Alvo:** Este documento e os relatórios de decisão.

**Ações:**
- Incorporar achados dos dois agentes independentes
- Manter coerência entre classificações, Docker, Daytona e imagem
- Revisar checklist de limpeza com base na validação consolidada

### Fase 2B — Criar Testes Mínimos de Boot/Import/Registry

**Alvo:** Core e tools validadas.

**Ações:**
- Criar testes mínimos de boot para `Manus`
- Criar testes mínimos de import/registry para `ToolCallAgent`, `ToolCollection` e tools validadas
- Garantir validação do core sem depender de `tests/sandbox/`

### Fase 2C — Isolar Sandbox Docker Local da Validação Padrão

**Alvo:** `app/sandbox/` e `tests/sandbox/`

**Ações:**
- Marcar `tests/sandbox/*` como dependentes de Docker
- Retirar sandbox Docker do caminho padrão de validação
- Manter `app/sandbox/` e `tests/sandbox/` como `QUARANTINE_FOR_FIX`

### Fase 2D — Mapear Daytona Legado e Decidir Refactor/Desacoplamento

**Alvo:** `app/daytona/`, `app/agent/sandbox_agent.py`, `app/tool/computer_use_tool.py`, `app/tool/sandbox/`

**Ações:**
- Listar importadores ativos de `app.daytona.*`
- Confirmar se `sandbox_main.py` e tools legadas ainda têm uso real
- Separar explicitamente o caminho validado (`daytona_http.py` + `daytona_sandbox.py`) do caminho legado SDK

### Fase 2E — Avaliar Remoções Controladas Somente Depois de Prova

**Alvo:** Apenas módulos já comprovadamente não usados.

**Ações:**
- Exigir prova de não-uso
- Exigir testes mínimos de boot/import/registry passando sem o módulo
- Executar sempre em branch separada com rollback documentado

### Fase 3 — Retomar GraphStore Binário Fechado

**Alvo:** Nova funcionalidade

**Ações:**
- Retomar a integração GraphStore somente após consolidação modular
- Criar `app/integrations/graphstore_cli.py` (adapter CLI)
- Criar `app/tool/graphstore_memory.py` (tool)
- Criar `scripts/setup_graphstore_memory.py` (bootstrap)
- Atualizar `app/config.py` com `GraphStoreSettings`
- Atualizar `config/config.example.toml` com seção `[graphstore]`
- Atualizar `.gitignore` com `.local_data/`

### Futuro — Skill Adapter e Provider Registry

**Alvo:** Arquitetura futura obrigatória (seção 18)

**Ações:**
- Criar `docs/SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT_v0_1.md`
- Criar `USER_CONFIGURABLE_SKILLS_AND_PROVIDER_REGISTRY_v0_1.md`
- Definir schema de Action Payload, adapters, providers, validadores e retry

---

## 22. Backlog Arquitetural Pós-Limpeza

> **Status:** Nenhum documento foi criado ainda. Apenas itens de backlog identificados.
>
> **Regra:** Nenhum destes documentos deve ser criado antes da conclusão da consolidação modular e do bootstrap mínimo das Fases 2A–2B.

### 22.1 Documentos Futuros Identificados

| Documento | Escopo | Depende de |
|-----------|--------|------------|
| `USER_CONFIGURABLE_SKILLS_AND_PROVIDER_REGISTRY_v0_1.md` | Registry de skills, providers e tools configurável pelo usuário | Futuro — Skill Adapter e Provider Registry |
| `SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT_v0_1.md` | Contrato da camada Skill Adapter | Futuro — Skill Adapter e Provider Registry |

### 22.2 Capacidades Futuras (Não Implementadas)

| Capacidade | Descrição | Prioridade |
|------------|-----------|------------|
| **Registry de skills** | Interface para adicionar/remover/ativar/desativar skills sem editar código | Pós Fase 5 |
| **Troca de providers em runtime** | Trocar provedores de IA e tools sem modificar backend | Pós Fase 5 |
| **Registry seguro** | Skills, providers e tools registrados com validação de compatibilidade | Pós Fase 6 |
| **Validação pré-ativação** | Verificar compatibilidade entre skill, provider e tool antes de ativar | Pós Fase 6 |
| **Separação config vs código** | Configuração do usuário isolada do código-fonte do projeto | Pós Fase 4 |

### 22.3 Relação com a Limpeza Atual

- Nenhum dos itens acima **bloqueia** a consolidação das Fases 2A–2E.
- A limpeza deve preservar os módulos base identificados na seção 18.4.
- A criação destes documentos e capacidades deve ocorrer **após** a estabilização do fork, não antes.

---

## 23. Apêndice A — Mapa Visual de Dependências entre Módulos

```
main.py
 └── app.agent.manus.Manus  [KEEP_CORE]
      ├── app.agent.toolcall.ToolCallAgent  [KEEP_CORE]
      │    ├── app.agent.react.ReActAgent  [KEEP_CORE]
      │    │    └── app.agent.base.BaseAgent  [KEEP_CORE]
      │    └── app.llm.LLM  [KEEP_CORE]
      ├── app.tool.* (7 tools registradas)  [KEEP_CORE / KEEP_VALIDATED_TOOL]
      ├── app.integrations.daytona_http.DaytonaHTTPClient  [KEEP_VALIDATED_TOOL]
      ├── app.tool.mcp.MCPClients  [KEEP_OPTIONAL]
      └── app.config.Config  [KEEP_CORE]

app.daytona.*  [LEGACY_DEPENDENCY / INVESTIGATE]  ←── ainda possui importadores legados
app.tool.sandbox.*  [LEGACY_DEPENDENCY / INVESTIGATE]  ←── depende do SDK daytona legado
sandbox_main.py  [LEGACY_DEPENDENCY / INVESTIGATE]  ←── entry point herdado, não remover sem prova

protocol.a2a.*  [DEFER_FUTURE → ARQUIVADO]  ←── movido para archive/openmanus/a2a_protocol_unvalidated/
examples/  [DEFER_FUTURE]  ←── diretório separado
```
