# Module Disposition Plan — v0.1

> **Objetivo:** Criar um plano de decisão por módulo para o fork local OpenManus antes de qualquer limpeza estrutural, remoção de dependências ou continuação da integração GraphStore.
>
> **Baseado em:** `REPOSITORY_INVENTORY.md`, `REPOSITORY_AUDIT.md`, `DEPENDENCY_AUDIT.md`, `GRAPHSTORE_EXISTING_PATTERN_AUDIT.md`, `GRAPHSTORE_CLOSED_BINARY_INTEGRATION_DECISION_v0_1.md`, `reports/dependency_snapshots/pip_freeze_current_2026_06_24.txt`
>
> **Regra:** Nenhum código foi alterado. Nenhuma limpeza foi executada. Este documento é apenas planejamento.
>
> **Data:** 25/06/2026

---

## Classificações

| Código | Significado | Ação |
|--------|-------------|------|
| **KEEP_CORE** | Módulo necessário para funcionamento atual da Manus | Manter, testar, proteger |
| **KEEP_VALIDATED_TOOL** | Módulo/ferramenta já validado no fork local | Manter, criar teste formal |
| **KEEP_OPTIONAL** | Útil, mas opcional | Manter, pode virar extras |
| **QUARANTINE** | Deve existir no repositório, mas não carregado por padrão | Mover para disabled/ ou proteger import |
| **INVESTIGATE** | Requer análise adicional antes de decisão | Investigar antes de qualquer ação |
| **DEFER_FUTURE** | Pode ser útil em fase futura, mas não entra no MVP atual | Documentar, não remover |
| **REMOVE_CANDIDATE** | Candidato à remoção futura somente após teste e confirmação | Testar, confirmar não-uso, remover em branch separada |

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
| **Classificação** | **QUARANTINE** |
| **Ação** | Não remover. Documentar que depende de SDK não instalado. Proteger import contra crash acidental. |

---

## 3. Tools

### 3.1 Tools Core (registradas no Manus)

| Caminho | Tool | Origem | Classificação | Observação |
|---------|------|--------|---------------|------------|
| `app/tool/base.py` | `BaseTool`, `ToolResult` | Original | **KEEP_CORE** | Classe base de todas as tools |
| `app/tool/tool_collection.py` | `ToolCollection` | Original | **KEEP_CORE** | Gerenciamento de tools |
| `app/tool/terminate.py` | `Terminate` | Original | **KEEP_CORE** | Finaliza interação |
| `app/tool/bash.py` | `Bash` | Original | **KEEP_CORE** | Execução shell |
| `app/tool/python_execute.py` | `PythonExecute` | Original | **KEEP_CORE** | Execução Python |
| `app/tool/str_replace_editor.py` | `StrReplaceEditor` | Original | **KEEP_CORE** | Edição de arquivos |
| `app/tool/ask_human.py` | `AskHuman` | Original | **KEEP_CORE** | Input do usuário |
| `app/tool/browser_use_tool.py` | `BrowserUseTool` | Original | **KEEP_OPTIONAL** | Depende de `browser-use` + `playwright` |
| `app/tool/web_search.py` | `WebSearch` | Original | **KEEP_OPTIONAL** | Chamadas de API externa |
| `app/tool/create_chat_completion.py` | `CreateChatCompletion` | Original | **KEEP_CORE** | Saída LLM estruturada |
| `app/tool/planning.py` | `PlanningTool` | Original | **KEEP_OPTIONAL** | Gerencia planos multi-passo |
| `app/tool/file_operators.py` | `FileOperator` | Original | **KEEP_OPTIONAL** | Abstração de I/O |
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
| `app/tool/crawl4ai.py` | `Crawl4aiTool` | Original | **KEEP_OPTIONAL** | Lazy import. Falha graciosa se ausente. |
| `app/tool/computer_use_tool.py` | `ComputerUseTool` | Original | **INVESTIGATE** | Automação de desktop. Risco de segurança. Não registrada no Manus. Requer confirmação de uso. |

### 3.4 `app/tool/search/` (Motores de Busca)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `base.py` | Original | **KEEP_CORE** | Classe base |
| `google_search.py` | Original | **KEEP_OPTIONAL** | Requer API key Google |
| `baidu_search.py` | Original | **KEEP_OPTIONAL** | Requer API key Baidu |
| `bing_search.py` | Original | **KEEP_OPTIONAL** | Requer API key Bing |
| `duckduckgo_search.py` | Original | **KEEP_OPTIONAL** | Sem API key |

**Nota:** Gerenciados por `app/tool/web_search.py` com fallback. Nenhum é importado diretamente pelo Manus — todos via `WebSearch`.

### 3.5 `app/tool/sandbox/` (SDK Daytona Original — Não Usado)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `sb_shell_tool.py` | Original (herdado) | **QUARANTINE** | Depende de SDK `daytona` não instalado |
| `sb_files_tool.py` | Original (herdado) | **QUARANTINE** | Depende de SDK `daytona` não instalado |
| `sb_browser_tool.py` | Original (herdado) | **QUARANTINE** | Depende de SDK `daytona` não instalado |
| `sb_vision_tool.py` | Original (herdado) | **QUARANTINE** | Depende de SDK `daytona` não instalado |

### 3.6 `app/tool/chart_visualization/` (Visualização de Gráficos)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `__init__.py` | Original | **KEEP_OPTIONAL** | Re-exporta |
| `chart_prepare.py` | Original | **KEEP_OPTIONAL** | Gera CSV + JSON |
| `data_visualization.py` | Original | **KEEP_OPTIONAL** | Spawns `npx ts-node` |
| `python_execute.py` | Original | **KEEP_OPTIONAL** | Execução Python |
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

### 4.2 `app/daytona/` (SDK Daytona Original — Não Usado)

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `sandbox.py` | Original (herdado) | **QUARANTINE** | Requer SDK `daytona` não instalado |
| `tool_base.py` | Original (herdado) | **QUARANTINE** | Requer SDK `daytona` não instalado |
| `README.md` | Original (herdado) | **QUARANTINE** | Documentação do fluxo SDK |

**Evidência de não-uso:** Nenhum arquivo em `app/agent/manus.py`, `app/tool/daytona_sandbox.py` ou `app/tool/image_generator.py` importa de `app.daytona`.

---

## 5. Flows

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/flow/__init__.py` | Original | **KEEP_CORE** | Vazio |
| `app/flow/base.py` | Original | **KEEP_CORE** | Classe base abstrata |
| `app/flow/flow_factory.py` | Original | **KEEP_CORE** | Factory method |
| `app/flow/planning.py` | Original | **KEEP_OPTIONAL** | Orquestra agentes. Entry point `run_flow.py`. |

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
| `app/sandbox/__init__.py` | Original | **KEEP_OPTIONAL** | Vazio |
| `app/sandbox/client.py` | Original | **KEEP_OPTIONAL** | Factory (BaseSandboxClient, LocalSandboxClient) |
| `app/sandbox/core/sandbox.py` | Original | **KEEP_OPTIONAL** | DockerSandbox lifecycle |
| `app/sandbox/core/terminal.py` | Original | **KEEP_OPTIONAL** | AsyncDockerizedTerminal |
| `app/sandbox/core/manager.py` | Original | **KEEP_OPTIONAL** | SandboxManager (pool) |
| `app/sandbox/core/exceptions.py` | Original | **KEEP_OPTIONAL** | Exceções |

**Nota:** `app/sandbox/` é o único módulo com testes unitários em `tests/sandbox/`. Não usado na configuração local (`use_sandbox = false`). Requer Docker Desktop em execução.

---

## 8. MCP

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/mcp/__init__.py` | Original | **KEEP_CORE** | Vazio |
| `app/mcp/server.py` | Original | **KEEP_OPTIONAL** | Servidor FastMCP. Entry point `run_mcp_server.py`. |

---

## 9. Utils

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `app/utils/__init__.py` | Original | **KEEP_CORE** | Comentário apenas |
| `app/utils/files_utils.py` | Original | **KEEP_CORE** | Limpeza de path, exclusão |
| `app/utils/logger.py` | Original | **INVESTIGATE** | Segundo logger (structlog). Coconcorre com `app/logger.py` (loguru). Investigar qual é o usado, se ambos são necessários. |

---

## 10. Protocolo A2A

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `protocol/a2a/__init__.py` | Original | **DEFER_FUTURE** | Vazio |
| `protocol/a2a/app/main.py` | Original | **DEFER_FUTURE** | Servidor Starlette + uvicorn |
| `protocol/a2a/app/agent.py` | Original | **DEFER_FUTURE** | A2AManus wrapper |
| `protocol/a2a/app/agent_executor.py` | Original | **DEFER_FUTURE** | ManusExecutor |
| `protocol/a2a/app/README.md` | Original | **DEFER_FUTURE** | Documentação |

**Nota:** Módulo experimental separado do core. Não integrado ao entry point principal. Útil para interoperabilidade agente-a-agente no futuro.

---

## 11. Entry Points

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `main.py` | Original | **KEEP_CORE** | Entry point principal: `Manus` agent |
| `run_flow.py` | Original | **KEEP_OPTIONAL** | PlanningFlow com agentes |
| `run_mcp.py` | Original | **KEEP_OPTIONAL** | MCPAgent via stdio/SSE |
| `run_mcp_server.py` | Original | **KEEP_OPTIONAL** | Servidor MCP (FastMCP) |
| `sandbox_main.py` | Original (herdado) | **QUARANTINE** | SandboxManus — requer SDK daytona não instalado |
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

---

## 13. Testes

| Caminho | Origem | Classificação | Observação |
|---------|--------|---------------|------------|
| `tests/sandbox/` | Original | **KEEP_OPTIONAL** | 4 testes da sandbox Docker local. Únicos testes formais. |

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
| `app/daytona/README.md` | Original | **QUARANTINE** | Instruções SDK (não aplicável) |
| `protocol/a2a/app/README.md` | Original | **DEFER_FUTURE** | Guia A2A |
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
| `output_images/` | — | **KEEP_OPTIONAL** | Diretório gerado em runtime |
| `.bak/` | — | **KEEP_OPTIONAL** | Backups |

---

## 17. Resumo por Classificação

| Classificação | Quantidade | Módulos Principais |
|---------------|------------|---------------------|
| **KEEP_CORE** | ~25 | config, llm, schema, exceptions, logger, agent/base, agent/react, agent/toolcall, agent/manus, tool/base, tool/terminate, tool/bash, tool/python_execute, tool/str_replace_editor, tool/ask_human, tool/create_chat_completion, integrations/__init__, flow/base, flow/flow_factory, prompt/manus, prompt/toolcall, utils/files_utils, main.py, docs recentes, config.toml, config.example.toml, README.md |
| **KEEP_VALIDATED_TOOL** | ~6 | daytona_sandbox.py, image_generator.py, daytona_http.py, 3 scripts de teste de regressão |
| **KEEP_OPTIONAL** | ~35 | browser agent, MCP agent, SWE agent, DataAnalysis, sandbox Docker, search tools, crawl4ai, chart_visualization, browser_use_tool, web_search, planning, file_operators, mcp.py/mcp server, A2A, bedrock, exemplos de config, Dockerfile, CI/CD, READMEs traduzidos |
| **QUARANTINE** | ~9 | app/daytona/ (3), app/tool/sandbox/ (4), sandbox_agent.py, sandbox_main.py, app/daytona/README.md |
| **INVESTIGATE** | ~3 | app/utils/logger.py (structful vs loguru), computer_use_tool.py, test_groq.py |
| **DEFER_FUTURE** | ~12 | protocol/a2a/, examples/, scripts de diagnóstico Daytona (7) |
| **REMOVE_CANDIDATE** | 0 | Nenhum módulo tem evidência suficiente para remoção |

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
  - [ ] `python scripts/test_daytona_http.py`
  - [ ] `python scripts/test_daytona_sandbox_tool.py`
  - [ ] `python scripts/test_manus_daytona_tool.py`
- [ ] Backup/commit antes de qualquer mudança
- [ ] Remoção em branch separada (nunca na main)
- [ ] Uma categoria por vez (não misturar KEEP_OPTIONAL com QUARANTINE)
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
- **Padrões de tool call:** `app/agent/toolcall.py`, `app/tool/base.py` — base da futura camada de Skill Adapter.
- **Módulos base da futura camada Skill Adapter:** `app/agent/manus.py`, `app/agent/toolcall.py`, `app/tool/`, `app/integrations/`, `app/schema.py`, `app/config.py` — serão usados como fundação da Skill Adapter e API Execution Layer.
- **Qualquer documentação de skills/protocolos:** Não remover antes de criar contrato separado (`SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT`).
- **Qualquer módulo usado por testes:** Verificar dependências de `tests/sandbox/` antes de alterar `app/sandbox/`.
- **Qualquer módulo cuja origem ainda não esteja clara:** Módulos marcados como **INVESTIGATE** não devem ser alterados.
- **`requirements.txt` e `setup.py`:** Não alterar sem seguir a checklist da seção 19.
- **Módulos marcados como QUARANTINE:** Não remover — apenas isolar de carregamento padrão.

---

## 21. Ordem Recomendada de Limpeza Futura

### Fase 0 — Documentação e Decisão por Módulo (atual)

- [x] `docs/REPOSITORY_INVENTORY.md`
- [x] `docs/REPOSITORY_AUDIT.md`
- [x] `docs/DEPENDENCY_AUDIT.md`
- [x] `docs/GRAPHSTORE_EXISTING_PATTERN_AUDIT.md`
- [x] `docs/GRAPHSTORE_CLOSED_BINARY_INTEGRATION_DECISION_v0_1.md`
- [x] `docs/MODULE_DISPOSITION_PLAN_v0_1.md`

### Fase 1 — Quarentena de Módulos Opcionais Não Usados por Padrão

**Alvo:** Módulos **QUARANTINE** — `app/daytona/`, `app/tool/sandbox/`, `sandbox_agent.py`, `sandbox_main.py`

**Ações:**
- Mover diretórios para `app/disabled/` ou similar (não remover)
- Verificar que nenhum import ativo os referencia
- Atualizar `.gitignore` se necessário
- Rodar checklist completa da seção 19

### Fase 1.5 — Investigação Obrigatória

**Alvo:** Módulos **INVESTIGATE**

**Ações:**
- `app/utils/logger.py`: Mapear qual logger cada arquivo importa (loguru vs structlog). Decidir unificação.
- `app/tool/computer_use_tool.py`: Confirmar se é usado por algum agente. Se não, mover para `QUARANTINE`.
- `test_groq.py`: Decidir se remove tracking (`git rm --cached`) ou remove do `.gitignore`.

### Fase 2 — Revisão de Dependências Opcionais

**Alvo:** Dependências marcadas como opcionais na `DEPENDENCY_AUDIT.md`

**Ações:**
- Separar `requirements-dev.txt` com `pytest`, `pytest-asyncio`
- Separar `requirements-optional.txt` com `docker`, `boto3`, `crawl4ai`, buscadores
- Mover `setuptools` de `requirements.txt` para `requirements-dev.txt`
- Investigar 10 dependências sem import direto confirmado (ver DEPENDENCY_AUDIT.md §9.3)

### Fase 3 — Remoção Controlada de Candidatos Confirmados

**Alvo:** Somente após fases 1 e 2 validadas

**Ações:**
- Remover módulos QUARANTINE que tiverem confirmação de não-uso por 30 dias
- Consolidar scripts de diagnóstico em suite de testes formal
- Remover scripts de diagnóstico redundantes

### Fase 4 — Simplificação de Documentação e Setup

**Alvo:** Configurações e exemplos

**Ações:**
- Consolidar exemplos de config TOML (manter apenas os mais relevantes)
- Atualizar README.md para refletir o estado do fork
- Arquivar documentação upstream não aplicável

### Fase 5 — Criação do Contrato Skill Adapter (antes ou junto com GraphStore)

**Alvo:** Arquitetura futura obrigatória (seção 18)

**Ações:**
- Criar `docs/SKILL_ADAPTER_AND_API_EXECUTION_CONTRACT_v0_1.md`
- Definir schema de Action Payload (Pydantic)
- Validar conceito mínimo com `ImageGeneratorTool` como prova
- Mapear como `ToolCallAgent` e `app/agent/manus.py` rotearão para `SkillRouter`
- Definir interface do `Validator` (validação + retry)

### Fase 6 — Continuação da Integração GraphStore

**Alvo:** Nova funcionalidade

**Ações:**
- Criar `app/integrations/graphstore_cli.py` (adapter CLI)
- Criar `app/tool/graphstore_memory.py` (tool)
- Criar `scripts/setup_graphstore_memory.py` (bootstrap)
- Atualizar `app/config.py` com `GraphStoreSettings`
- Atualizar `config/config.example.toml` com seção `[graphstore]`
- Atualizar `.gitignore` com `.local_data/`

---

## 22. Apêndice A — Mapa Visual de Dependências entre Módulos

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

app.daytona.*  [QUARANTINE]  ←── NENHUM import ativo
app.tool.sandbox.*  [QUARANTINE]  ←── NENHUM import ativo
sandbox_main.py  [QUARANTINE]  ←── entry point isolado

protocol.a2a.*  [DEFER_FUTURE]  ←── diretório separado
examples/  [DEFER_FUTURE]  ←── diretório separado
```
