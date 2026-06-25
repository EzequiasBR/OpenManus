# REPOSITORY_INVENTORY

> Documento gerado em 24/06/2026.
> Inventário técnico do repositório OpenManus — adaptação local com integrações externas.
> Nenhum arquivo foi modificado durante esta análise.

---

## 1. Visão geral da árvore do projeto

```
OpenManus/
├── .github/                    # CI/CD e templates de issues/PR
├── app/                        # Código-fonte principal do OpenManus
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   ├── bedrock.py
│   ├── schema.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── agent/                  # Agentes (hierarquia de classes)
│   ├── tool/                   # Ferramentas (tools) do agente
│   │   ├── search/             # Motores de busca
│   │   ├── sandbox/            # Tools sandbox (SDK Daytona original)
│   │   └── chart_visualization/ # Visualização de gráficos (TS + Python)
│   ├── flow/                   # Orquestração de fluxos multi-agente
│   ├── prompt/                 # Prompts de sistema para cada agente
│   ├── sandbox/                # Sandbox Docker local
│   ├── daytona/                # Sandbox Daytona via SDK (original, não usada)
│   ├── integrations/           # Integrações externas leves (HTTP direto)
│   ├── mcp/                    # Servidor MCP do OpenManus
│   └── utils/                  # Utilitários
├── archive/                   # Código arquivado (A2A, etc.)
│   └── openmanus/
│       └── a2a_protocol_unvalidated/  # A2A — DEFER_FUTURE, sem contrato funcional
├── config/                     # Arquivos de configuração TOML
├── docs/                       # Documentação local
├── examples/                   # Exemplos de uso e benchmarks
├── scripts/                    # Scripts de teste/diagnóstico (Daytona)
├── tests/                      # Testes unitários (sandbox Docker)
├── .pre-commit-config.yaml
├── .gitignore
├── Dockerfile
├── LICENSE                     # MIT
├── main.py                     # Entry point: Manus agent
├── run_flow.py                 # Entry point: PlanningFlow
├── run_mcp.py                  # Entry point: MCPAgent
├── run_mcp_server.py           # Entry point: MCPServer
├── sandbox_main.py             # Entry point: SandboxManus
├── test_groq.py                # Script de teste Groq (no .gitignore)
├── README.md
├── requirements.txt
└── setup.py
```

### Observações sobre organização

- **Código-fonte** (`app/`): bem modularizado, separado por responsabilidade (agent, tool, flow, prompt, sandbox).
- **Configurações** (`config/`): múltiplos exemplos por provedor LLM; o ativo é `config.toml` (ignorado via `.gitignore`).
- **Scripts de diagnóstico** (`scripts/`): 10 arquivos focados em testes Daytona, mantidos separados do código principal.
- **Testes unitários** (`tests/`): apenas 4 arquivos, todos cobrindo a sandbox Docker local. Não há testes para agents, tools, flows ou integrações HTTP.
- **Docs** (`docs/`): apenas 2 arquivos criados localmente (PROJECT_STATUS.md e contrato Daytona).
- **Protocolo A2A** (`archive/openmanus/a2a_protocol_unvalidated/`): implementação experimental arquivada por ser **DEFER_FUTURE** — sem contrato funcional, sem testes, sem integração. O diretório `protocol/a2a/` original foi removido.
- **`app/daytona/`**: implementação original baseada no SDK Daytona. **Não está em uso.** A adaptação local substituiu pelo HTTP direto em `app/integrations/` + `app/tool/daytona_sandbox.py`.

---

## 2. Inventário por categoria

### 2.1 Core do OpenManus

| Caminho | Tipo | Função aparente | Origem | Teste relacionado | Observações |
|---|---|---|---|---|---|
| `app/__init__.py` | Python | Restringe Python 3.11–3.13 | Original | Não | |
| `app/config.py` | Python | Modelos de configuração (LLM, Sandbox, Daytona, MCP, RunFlow) e carregamento TOML com `env:` resolver | Original | Não | ~227 linhas |
| `app/llm.py` | Python | Cliente LLM (OpenAI/Azure/Ollama/Bedrock), TokenCounter (tiktoken), retry, multimodal | Original | Não | ~480 linhas |
| `app/bedrock.py` | Python | Cliente AWS Bedrock (Converse API → formato OpenAI) | Original | Não | ~150 linhas |
| `app/schema.py` | Python | Modelos de dados: Message, ToolCall, AgentState, Memory, ToolChoice, Response | Original | Não | ~200 linhas |
| `app/exceptions.py` | Python | ToolError, OpenManusError, TokenLimitExceeded | Original | Não | ~30 linhas |
| `app/logger.py` | Python | Logger loguru (console DEBUG + arquivo com rotação) | Original | Não | ~40 linhas |
| `app/utils/__init__.py` | Python | Vazio | Original | Não | |
| `app/utils/files_utils.py` | Python | Limpeza de path, exclusão de arquivos | Original | Não | |
| `app/utils/logger.py` | Python | Logger structlog | Original | Não | Segundo logger no projeto |

### 2.2 Agentes

| Caminho | Tipo | Função aparente | Origem | Teste relacionado | Observações |
|---|---|---|---|---|---|
| `app/agent/__init__.py` | Python | Vazio | Original | Não | |
| `app/agent/base.py` | Python | `BaseAgent` — classe abstrata: memória, máquina de estados, step loop, cleanup | Original | Não | ~200 linhas |
| `app/agent/react.py` | Python | `ReActAgent` — loop think/act abstrato | Original | Não | ~150 linhas |
| `app/agent/toolcall.py` | Python | `ToolCallAgent` — chamada de tools via LLM, limites de token, retries | Original | Não | ~250 linhas |
| `app/agent/manus.py` | Python | `Manus` — agente versátil com 7 tools locais + MCP dinâmico | **Modificado localmente** | Não | Adicionado `DaytonaSandboxTool` e `ImageGeneratorTool`; usa `MCPClients` |
| `app/agent/browser.py` | Python | `BrowserAgent` — automação de navegador | Original | Não | ~200 linhas |
| `app/agent/mcp.py` | Python | `MCPAgent` — conexão a servidores MCP | Original | Não | ~100 linhas |
| `app/agent/swe.py` | Python | `SWEAgent` — programador autônomo (Bash + StrReplaceEditor) | Original | Não | ~30 linhas |
| `app/agent/data_analysis.py` | Python | `DataAnalysis` — agente de análise/visualização de dados | Original | Não | ~30 linhas |
| `app/agent/sandbox_agent.py` | Python | `SandboxManus` — agente baseado em sandbox Daytona SDK | Original | Não | ~30 linhas |

### 2.3 Tools

| Caminho | Tipo | Função aparente | Origem | Teste relacionado | Observações |
|---|---|---|---|---|---|
| `app/tool/__init__.py` | Python | Vazio | Original | Não | |
| `app/tool/base.py` | Python | `BaseTool` (ABC), `ToolResult`, `CLIResult`, `ToolFailure` | Original | Não | |
| `app/tool/tool_collection.py` | Python | `ToolCollection` — gerencia tools, `to_params()`, execução por nome | Original | Não | |
| `app/tool/terminate.py` | Python | `Terminate` — encerra interação com sucesso/falha | Original | Não | |
| `app/tool/bash.py` | Python | `Bash` — execução de shell com sessão, timeout, bg processes | Original | Não | |
| `app/tool/python_execute.py` | Python | `PythonExecute` — executa código Python com timeout | Original | Não | |
| `app/tool/str_replace_editor.py` | Python | `StrReplaceEditor` — view/create/replace/insert/undo em arquivos | Original | Não | |
| `app/tool/browser_use_tool.py` | Python | `BrowserUseTool` — automação de navegador via Playwright | Original | Não | |
| `app/tool/web_search.py` | Python | `WebSearch` — busca multi-motor com dedup e extração de conteúdo | Original | Não | |
| `app/tool/create_chat_completion.py` | Python | `CreateChatCompletion` — saída LLM estruturada com JSON type-mapped | Original | Não | |
| `app/tool/ask_human.py` | Python | `AskHuman` — solicita entrada do usuário | Original | Não | |
| `app/tool/planning.py` | Python | `PlanningTool` — CRUD de planos com rastreamento de passos | Original | Não | |
| `app/tool/file_operators.py` | Python | `FileOperator`, `LocalFileOperator`, `SandboxFileOperator` — abstração de I/O | Original | Não | |
| `app/tool/crawl4ai.py` | Python | `Crawl4aiTool` — crawling web com extração markdown | Original | Não | |
| `app/tool/computer_use_tool.py` | Python | `ComputerUseTool` — automação de desktop (mouse, teclado, screenshot) | Original | Não | |
| `app/tool/image_generator.py` | Python | `ImageGeneratorTool` — geração de imagem via Pollinations API | **Adicionado localmente** | Não | Nome tool: `generate_image` |
| `app/tool/daytona_sandbox.py` | Python | `DaytonaSandboxTool` — execução Python em sandbox remota Daytona via HTTP | **Adicionado localmente** | `scripts/test_daytona_sandbox_tool.py`, `scripts/test_manus_daytona_tool.py` | Nome tool: `daytona_sandbox`. ~233 linhas. Contrato dokumentado em `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` |
| `app/tool/mcp.py` | Python | `MCPClientTool`, `MCPClients` — protocolo MCP client | Original | Não | |

#### 2.3.1 Search tools

| Caminho | Tipo | Função aparente | Origem |
|---|---|---|---|
| `app/tool/search/__init__.py` | Python | Vazio | Original |
| `app/tool/search/base.py` | Python | `SearchToolBase` — classe base para buscadores | Original |
| `app/tool/search/google_search.py` | Python | Google Custom Search | Original |
| `app/tool/search/baidu_search.py` | Python | Baidu Search | Original |
| `app/tool/search/bing_search.py` | Python | Bing Search | Original |
| `app/tool/search/duckduckgo_search.py` | Python | DuckDuckGo Search | Original |

#### 2.3.2 Sandbox tools (SDK Daytona original — NÃO usada pela configuração atual)

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `app/tool/sandbox/__init__.py` | Python | Provavelmente vazio | Original | Não verificado |
| `app/tool/sandbox/sb_shell_tool.py` | Python | `SandboxShellTool` — execução shell via tmux na sandbox Daytona (SDK) | Original | ~419 linhas. Usa `app.daytona.tool_base` e SDK `daytona` |
| `app/tool/sandbox/sb_files_tool.py` | Python | `SandboxFilesTool` — operações de arquivo na sandbox Daytona (SDK) | Original | |
| `app/tool/sandbox/sb_browser_tool.py` | Python | `SandboxBrowserTool` — automação de navegador na sandbox Daytona (SDK) | Original | |
| `app/tool/sandbox/sb_vision_tool.py` | Python | `SandboxVisionTool` — visão computacional na sandbox Daytona (SDK) | Original | |

#### 2.3.3 Chart visualization

| Caminho | Tipo | Função aparente | Origem |
|---|---|---|---|
| `app/tool/chart_visualization/__init__.py` | Python | Vazio | Original |
| `app/tool/chart_visualization/chart_prepare.py` | Python | `VisualizationPrepare` — gera CSV + JSON metadata | Original |
| `app/tool/chart_visualization/data_visualization.py` | Python | `DataVisualization` — spawns `npx ts-node` para renderizar gráfico | Original |
| `app/tool/chart_visualization/python_execute.py` | Python | `NormalPythonExecute` — execução Python para processamento de dados não-visual | Original |
| `app/tool/chart_visualization/package.json` | JSON | Dependências Node (VMind, VChart, Puppeteer) | Original |
| `app/tool/chart_visualization/package-lock.json` | JSON | Lock das dependências Node | Original |
| `app/tool/chart_visualization/tsconfig.json` | JSON | Configuração TypeScript | Original |
| `app/tool/chart_visualization/README.md` | Markdown | Instruções de instalação (EN, JA, KO, ZH) | Original |
| `app/tool/chart_visualization/src/chartVisualize.ts` | TypeScript | Renderiza gráfico VChart via Puppeteer | Original |
| `app/tool/chart_visualization/test/chart_demo.py` | Python | Demo de gráfico | Original |
| `app/tool/chart_visualization/test/report_demo.py` | Python | Demo de relatório | Original |

### 2.4 Integrations

| Caminho | Tipo | Função aparente | Origem | Teste relacionado | Observações |
|---|---|---|---|---|---|
| `app/integrations/__init__.py` | Python | Vazio | **Adicionado localmente** | Não | |
| `app/integrations/daytona_http.py` | Python | `DaytonaHTTPClient` — cliente HTTP mínimo para Daytona API (sandbox CRUD, code execution, file upload/download) | **Adicionado localmente** | `scripts/test_daytona_http.py` e outros | ~490 linhas. Substitui o SDK Daytona oficial |

### 2.5 Sandbox original (Docker local)

| Caminho | Tipo | Função aparente | Origem | Teste relacionado | Observações |
|---|---|---|---|---|---|
| `app/sandbox/__init__.py` | Python | Vazio | Original | Não | |
| `app/sandbox/client.py` | Python | `BaseSandboxClient`, `LocalSandboxClient`, factory | Original | `tests/sandbox/test_client.py` | |
| `app/sandbox/core/__init__.py` | Python | Provavelmente vazio | Original | Não | |
| `app/sandbox/core/exceptions.py` | Python | Exceções de sandbox | Original | Não | |
| `app/sandbox/core/manager.py` | Python | `SandboxManager` — pool management | Original | `tests/sandbox/test_sandbox_manager.py` | |
| `app/sandbox/core/sandbox.py` | Python | `DockerSandbox` — ciclo de vida do container | Original | `tests/sandbox/test_sandbox.py` | |
| `app/sandbox/core/terminal.py` | Python | `AsyncDockerizedTerminal` — execução assíncrona Docker com websocket | Original | `tests/sandbox/test_docker_terminal.py` | |

### 2.6 Daytona (SDK original — NÃO usada)

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `app/daytona/__init__.py` | Python | Provavelmente vazio | Original | |
| `app/daytona/sandbox.py` | Python | Criação/gerência de sandbox Daytona via SDK (`daytona` package) | Original | ~165 linhas. Importa de `daytona` library |
| `app/daytona/tool_base.py` | Python | `SandboxToolsBase` — classe base para tools que usam sandbox Daytona SDK | Original | ~138 linhas. Usada por `app/tool/sandbox/` |
| `app/daytona/README.md` | Markdown | Instruções para usar agente com sandbox Daytona via SDK | Original | Menciona `pip install daytona==0.21.8` |

### 2.7 Flows

| Caminho | Tipo | Função aparente | Origem | Teste relacionado |
|---|---|---|---|---|
| `app/flow/__init__.py` | Python | Vazio | Original | Não |
| `app/flow/base.py` | Python | `BaseFlow` — classe abstrata para fluxos | Original | Não |
| `app/flow/flow_factory.py` | Python | `FlowFactory` — cria fluxos por tipo | Original | Não |
| `app/flow/planning.py` | Python | `PlanningFlow` — fluxo multi-passo que delega a agentes (Manus, DataAnalysis) | Original | Não |

### 2.8 Prompts

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `app/prompt/__init__.py` | Python | Vazio | Original | |
| `app/prompt/manus.py` | Python | System prompt e next-step prompt do Manus | Original | ~50 linhas |
| `app/prompt/toolcall.py` | Python | Next step prompt do ToolCallAgent | Original | ~40 linhas |
| `app/prompt/browser.py` | Python | System prompt do BrowserAgent | Original | ~20 linhas |
| `app/prompt/swe.py` | Python | System + next step prompts do SWEAgent | Original | ~90 linhas |
| `app/prompt/planning.py` | Python | System prompt do Planning | Original | ~50 linhas |
| `app/prompt/mcp.py` | Python | System prompt do MCPAgent | Original | ~10 linhas |
| `app/prompt/visualization.py` | Python | Prompts de visualização do DataAnalysis | Original | ~50 linhas |

### 2.9 MCP

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `app/mcp/__init__.py` | Python | Vazio | Original | |
| `app/mcp/server.py` | Python | `MCPServer` — expõe tools do OpenManus como servidor MCP via FastMCP | Original | |

### 2.10 Scripts

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `scripts/create_daytona_sandbox.py` | Python | Cria sandbox Daytona via HTTP | **Adicionado localmente** | Diagnóstico |
| `scripts/delete_daytona_sandbox.py` | Python | Deleta sandbox Daytona via HTTP | **Adicionado localmente** | Diagnóstico |
| `scripts/inspect_daytona_file_upload.py` | Python | Testa 5 variantes de upload | **Adicionado localmente** | Diagnóstico, 154 linhas |
| `scripts/inspect_daytona_toolbox_routes.py` | Python | Sonda rotas Toolbox | **Adicionado localmente** | Diagnóstico, 139 linhas |
| `scripts/test_daytona_code_execution_flow.py` | Python | Fluxo completo: create → code → exec → result → delete | **Adicionado localmente** | Teste de integração, 163 linhas |
| `scripts/test_daytona_file_api.py` | Python | Upload/download/validação de arquivos | **Adicionado localmente** | Teste de integração, 116 linhas |
| `scripts/test_daytona_http.py` | Python | Smoke test da API HTTP Daytona | **Adicionado localmente** | Teste de integração, 36 linhas |
| `scripts/test_daytona_sandbox_tool.py` | Python | Testa DaytonaSandboxTool com 3 cenários | **Adicionado localmente** | Teste de integração, 49 linhas |
| `scripts/test_daytona_toolbox_execute.py` | Python | Executa comandos na sandbox | **Adicionado localmente** | Teste de integração, 110 linhas |
| `scripts/test_manus_daytona_tool.py` | Python | End-to-end: Manus usando daytona_sandbox | **Adicionado localmente** | Teste de integração, 33 linhas |

### 2.11 Configurações

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `config/config.toml` | TOML | Configuração ativa (Groq + Daytona + MCP) | **Adicionado localmente** | Ignorado pelo `.gitignore` |
| `config/config.example.toml` | TOML | Exemplo completo com todos os provedores | Original | |
| `config/config.example-azure.toml` | TOML | Exemplo Azure | Original | |
| `config/config.example-baidu.toml` | TOML | Exemplo Baidu | Original | |
| `config/config.example-bytedance.toml` | TOML | Exemplo ByteDance | Original | |
| `config/config.example-gemini.toml` | TOML | Exemplo Google Gemini | Original | |
| `config/config.example-github.toml` | TOML | Exemplo GitHub Models | Original | |
| `config/config.example-groq.toml` | TOML | Exemplo Groq | Original | |
| `config/config.example-jiekou.toml` | TOML | Exemplo JiekouAI | Original | |
| `config/config.example-ollama.toml` | TOML | Exemplo Ollama | Original | |
| `config/config.example-openai-compatible.toml` | TOML | Exemplo OpenAI-compatível | Original | |
| `config/config.example-openai.toml` | TOML | Exemplo OpenAI | Original | |
| `config/config.example.zhipu.toml` | TOML | Exemplo Zhipu | Original | |
| `config/mcp.example.json` | JSON | Configuração de servidores MCP (stdio) | Original | |
| `.pre-commit-config.yaml` | YAML | hooks pre-commit (black, isort, autoflake) | Original | |

### 2.12 Schemas

Não há diretório `schemas/` separado. Os schemas de dados estão centralizados em `app/schema.py`.

### 2.13 Docs

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `docs/PROJECT_STATUS.md` | Markdown | Status do projeto, integrações validadas, regras de estabilidade | **Adicionado localmente** | 363 linhas |
| `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` | Markdown | Contrato da DaytonaSandboxTool v0.2.1 | **Adicionado localmente** | 342 linhas |

### 2.14 Testes

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `tests/sandbox/__init__.py` | Python | Provavelmente vazio | Original | |
| `tests/sandbox/test_sandbox.py` | Python | Testes do DockerSandbox | Original | |
| `tests/sandbox/test_client.py` | Python | Testes do LocalSandboxClient | Original | |
| `tests/sandbox/test_docker_terminal.py` | Python | Testes do AsyncDockerizedTerminal | Original | |
| `tests/sandbox/test_sandbox_manager.py` | Python | Testes do SandboxManager | Original | |

### 2.15 Exemplos / Assets

| Caminho | Tipo | Função aparente | Origem |
|---|---|---|---|
| `examples/benchmarks/__init__.py` | Python | Vazio | Original |
| `examples/use_case/readme.md` | Markdown | Instruções de caso de uso | Original |
| `examples/use_case/pictures/japan-travel-plan-1.png` | PNG | Screenshot de exemplo | Original |
| `examples/use_case/pictures/japan-travel-plan-2.png` | PNG | Screenshot de exemplo | Original |
| `examples/use_case/japan-travel-plan/japan_travel_guide_instructions.txt` | Texto | Instruções para guia de viagem | Original |
| `examples/use_case/japan-travel-plan/japan_travel_handbook.html` | HTML | Guia de viagem gerado (Desktop) | Original |
| `examples/use_case/japan-travel-plan/japan_travel_handbook_mobile.html` | HTML | Guia de viagem gerado (Mobile) | Original |
| `examples/use_case/japan-travel-plan/japan_travel_handbook_print.html` | HTML | Guia de viagem gerado (Print) | Original |

### 2.16 Protocolo A2A — Arquivado

O protocolo A2A foi movido para `archive/openmanus/a2a_protocol_unvalidated/` por ser **DEFER_FUTURE**: sem contrato funcional, sem testes, sem integração com o entry point principal.

| Caminho (no archive) | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `archive/openmanus/a2a_protocol_unvalidated/a2a/__init__.py` | Python | Vazio | Original | |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/__init__.py` | Python | Vazio | Original | |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/main.py` | Python | Servidor A2A (Starlette + uvicorn) | Original | 131 linhas |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/agent.py` | Python | `A2AManus` — wrapper Manus para A2A | Original | 32 linhas |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/agent_executor.py` | Python | `ManusExecutor` — executor A2A | Original | 72 linhas |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/README.md` | Markdown | Guia de setup e exemplos curl | Original | 194 linhas |

O diretório `protocol/a2a/` original foi removido.

### 2.17 CI/CD

| Caminho | Tipo | Função aparente | Origem |
|---|---|---|---|
| `.github/dependabot.yml` | YAML | Dependabot config | Original |
| `.github/PULL_REQUEST_TEMPLATE.md` | Markdown | Template de PR | Original |
| `.github/ISSUE_TEMPLATE/config.yml` | YAML | Config de templates de issue | Original |
| `.github/ISSUE_TEMPLATE/request_new_features.yaml` | YAML | Template de feature request | Original |
| `.github/ISSUE_TEMPLATE/show_me_the_bug.yaml` | YAML | Template de bug report | Original |
| `.github/workflows/build-package.yaml` | YAML | Build + publish no PyPI (release) | Original |
| `.github/workflows/pre-commit.yaml` | YAML | pre-commit em push/PR | Original |
| `.github/workflows/environment-corrupt-check.yaml` | YAML | Testa pip install em 3.11/3.12/3.13 | Original |
| `.github/workflows/pr-autodiff.yaml` | YAML | Diff bilíngue via o3-mini | Original |
| `.github/workflows/stale.yaml` | YAML | Fecha issues inativas (45 dias) | Original |
| `.github/workflows/top-issues.yaml` | YAML | Label e destaque de top issues | Original |

### 2.18 Entry points

| Caminho | Tipo | Função aparente | Origem | Observações |
|---|---|---|---|---|
| `main.py` | Python | CLI: cria `Manus` agent e executa prompt | Original | |
| `run_flow.py` | Python | CLI: cria `PlanningFlow` com agentes (Manus opcional + DataAnalysis) | Original | |
| `run_mcp.py` | Python | CLI: cria `MCPAgent` conectado via stdio/SSE | Original | |
| `run_mcp_server.py` | Python | CLI: inicia OpenManus como servidor MCP (FastMCP) | Original | |
| `sandbox_main.py` | Python | CLI: cria `SandboxManus` agent (sandbox Daytona SDK) | Original | |
| `test_groq.py` | Python | Teste rápido de conectividade Groq | **Adicionado localmente** | No `.gitignore` |

### 2.19 Infraestrutura

| Caminho | Tipo | Função aparente | Origem |
|---|---|---|---|
| `Dockerfile` | Dockerfile | Python 3.12-slim, uv, dependências | Original |
| `requirements.txt` | Texto | 42 dependências Python | Original |
| `setup.py` | Python | Configuração do pacote, entry point `openmanus = main:main` | Original |
| `LICENSE` | Texto | MIT | Original |

---

## 3. Tools registradas no Manus (configuração local)

Com base na leitura de `app/agent/manus.py`, as tools registradas no `ToolCollection` do `Manus` são:

| Nome da tool | Classe | Arquivo |
|---|---|---|
| `python_execute` | `PythonExecute` | `app/tool/python_execute.py` |
| `browser_use` | `BrowserUseTool` | `app/tool/browser_use_tool.py` |
| `str_replace_editor` | `StrReplaceEditor` | `app/tool/str_replace_editor.py` |
| `ask_human` | `AskHuman` | `app/tool/ask_human.py` |
| `generate_image` | `ImageGeneratorTool` | `app/tool/image_generator.py` |
| `terminate` | `Terminate` | `app/tool/terminate.py` |
| `daytona_sandbox` | `DaytonaSandboxTool` | `app/tool/daytona_sandbox.py` |

Além disso, o Manus conecta-se dinamicamente a servidores MCP configurados (via `config/mcp.example.json`), cujas tools são adicionadas em tempo de execução como `MCPClientTool`.

---

## 4. Arquivos relacionados às integrações validadas

### 4.1 `app/integrations/daytona_http.py`

- **Tipo**: Python (~490 linhas)
- **Classe**: `DaytonaHTTPClient`
- **Função**: Cliente HTTP mínimo para Daytona API. Substitui o SDK Python oficial para evitar conflitos de dependência.
- **Endpoints implementados**: validate_key, list_sandboxes, create_sandbox, get_sandbox, delete_sandbox, execute_command, create_folder, upload_file, download_file, file_info, delete_path, get_project_dir, get_user_home_dir, get_work_dir.
- **Origem**: **Adicionado localmente**.
- **Teste relacionado**: `scripts/test_daytona_http.py`
- **Observações**: Contém tratamento de erro via `DaytonaHTTPError` (RuntimeError). Usa `httpx` como cliente HTTP.

### 4.2 `app/tool/daytona_sandbox.py`

- **Tipo**: Python (~233 linhas)
- **Classe**: `DaytonaSandboxTool`
- **Função**: Tool do Manus que executa código Python em sandbox remota efêmera Daytona via HTTP.
- **Ação implementada**: `run_python_code`
- **Origem**: **Adicionado localmente**.
- **Teste relacionado**: `scripts/test_daytona_sandbox_tool.py`, `scripts/test_manus_daytona_tool.py`
- **Contrato**: Documentado em `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md`
- **Observações**: Cria sandbox temporária, faz upload de `task.py`, executa `python3 task.py`, tenta baixar `result.txt`, faz cleanup. Atende ao contrato de isolamento (não reusa sandbox entre chamadas).

### 4.3 `app/tool/image_generator.py`

- **Tipo**: Python (~99 linhas)
- **Classe**: `ImageGeneratorTool`
- **Função**: Gera imagem a partir de prompt textual via Pollinations API. Salva em `output_images/`.
- **Nome da tool**: `generate_image`
- **Origem**: **Adicionado localmente**.
- **Teste relacionado**: Nenhum script de teste dedicado.
- **Observações**: Usa `httpx` assíncrono. Suporta chave de API via `POLLINATIONS_API_KEY`.

### 4.4 Scripts Daytona

| Script | Função |
|---|---|
| `scripts/create_daytona_sandbox.py` | Cria sandbox via HTTP |
| `scripts/delete_daytona_sandbox.py` | Deleta sandbox via HTTP |
| `scripts/inspect_daytona_file_upload.py` | Testa upload de arquivos (5 variantes) |
| `scripts/inspect_daytona_toolbox_routes.py` | Sonda rotas Toolbox |
| `scripts/test_daytona_code_execution_flow.py` | Ciclo completo: create → exec → result → delete |
| `scripts/test_daytona_file_api.py` | Upload/download/validação |
| `scripts/test_daytona_http.py` | Smoke test básico da API |
| `scripts/test_daytona_sandbox_tool.py` | Testa DaytonaSandboxTool isolada (3 cenários) |
| `scripts/test_daytona_toolbox_execute.py` | Execução de comandos na sandbox |
| `scripts/test_manus_daytona_tool.py` | End-to-end: Manus + daytona_sandbox |

### 4.5 Scripts de teste do Manus

| Script | Função |
|---|---|
| `scripts/test_manus_daytona_tool.py` | Verifica se Manus seleciona `daytona_sandbox`, executa código, e retorna resultado esperado. Critérios de aprovação documentados no contrato. |

### 4.6 Arquivos de documentação existentes

| Arquivo | Conteúdo |
|---|---|
| `README.md` | README oficial do OpenManus (instalação, configuração, quick start) |
| `docs/PROJECT_STATUS.md` | Estado da adaptação local, integrações validadas, variáveis de ambiente, regras de estabilidade |
| `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` | Contrato formal da DaytonaSandboxTool: parâmetros, respostas, cleanup, isolamento, testes aprovados |
| `app/daytona/README.md` | Instruções originais para usar sandbox Daytona via SDK (não aplicável à configuração atual) |
| `archive/openmanus/a2a_protocol_unvalidated/a2a/app/README.md` | Guia do protocolo A2A (arquivado) |

---

## 5. Mapa de herança de agentes

```
BaseAgent (app/agent/base.py)
 └── ReActAgent (app/agent/react.py)
      └── ToolCallAgent (app/agent/toolcall.py)
           ├── Manus (app/agent/manus.py)
           ├── BrowserAgent (app/agent/browser.py)
           ├── MCPAgent (app/agent/mcp.py)
           ├── SWEAgent (app/agent/swe.py)
           ├── DataAnalysis (app/agent/data_analysis.py)
           └── SandboxManus (app/agent/sandbox_agent.py)
```

---

## 6. Mapa de dependências entre módulos

### 6.1 Cadeia principal do Manus (configuração local)

```
main.py
 └── app.agent.manus.Manus
      ├── app.agent.toolcall.ToolCallAgent
      │    ├── app.agent.react.ReActAgent
      │    │    └── app.agent.base.BaseAgent
      │    ├── app.tool.tool_collection.ToolCollection
      │    └── app.llm.LLM
      ├── app.tool.python_execute.PythonExecute
      ├── app.tool.browser_use_tool.BrowserUseTool
      ├── app.tool.str_replace_editor.StrReplaceEditor
      ├── app.tool.ask_human.AskHuman
      ├── app.tool.image_generator.ImageGeneratorTool
      ├── app.tool.terminate.Terminate
      ├── app.tool.daytona_sandbox.DaytonaSandboxTool
      │    └── app.integrations.daytona_http.DaytonaHTTPClient
      ├── app.tool.mcp.MCPClients
      ├── app.prompt.manus
      ├── app.config
      └── app.logger
```

### 6.2 Cadeia do SandboxManus (não usada na configuração atual)

```
sandbox_main.py
 └── app.agent.sandbox_agent.SandboxManus
      ├── app.agent.toolcall.ToolCallAgent → ...
      ├── app.tool.sandbox.sb_shell_tool.SandboxShellTool
      ├── app.tool.sandbox.sb_files_tool.SandboxFilesTool
      ├── app.tool.sandbox.sb_browser_tool.SandboxBrowserTool
      ├── app.tool.sandbox.sb_vision_tool.SandboxVisionTool
      ├── app.daytona.tool_base.SandboxToolsBase
      │    └── app.daytona.sandbox (daytona SDK)
      └── app.utils.logger
```

### 6.3 Cadeia da sandbox Docker local

```
app.sandbox.client.LocalSandboxClient
 └── app.sandbox.core.sandbox.DockerSandbox
      └── app.sandbox.core.terminal.AsyncDockerizedTerminal
           └── docker SDK
 └── app.sandbox.core.manager.SandboxManager
```

---

## 7. Variáveis de ambiente requeridas

| Variável | Onde é usada | Propósito |
|---|---|---|
| `GROQ_API_KEY` | `app/config.py` → `env:GROQ_API_KEY` | LLM Groq |
| `POLLINATIONS_API_KEY` | `app/tool/image_generator.py` | Geração de imagem |
| `DAYTONA_API_KEY` | `app/integrations/daytona_http.py` | Sandbox remota Daytona |
| `DAYTONA_ORGANIZATION_ID` | `app/integrations/daytona_http.py` | Organização Daytona (opcional) |

---

## 8. Observações sobre arquivos não utilizados (na configuração local)

Os arquivos abaixo pertencem ao fluxo original do OpenManus baseado no SDK Daytona e **não são utilizados** na configuração local atual (que usa HTTP direto):

| Arquivo | Motivo |
|---|---|
| `app/daytona/sandbox.py` | Usa `from daytona import ...` (SDK oficial) |
| `app/daytona/tool_base.py` | Usa `from daytona import ...` (SDK oficial) |
| `app/tool/sandbox/sb_shell_tool.py` | Depende de `app.daytona.tool_base` (SDK) |
| `app/tool/sandbox/sb_files_tool.py` | Depende de `app.daytona.tool_base` (SDK) |
| `app/tool/sandbox/sb_browser_tool.py` | Depende de `app.daytona.tool_base` (SDK) |
| `app/tool/sandbox/sb_vision_tool.py` | Depende de `app.daytona.tool_base` (SDK) |
| `sandbox_main.py` | Cria `SandboxManus` que usa as tools acima |

Estes arquivos são mantidos porque pertencem ao repositório original. A configuração local optou por uma implementação paralela (`app/integrations/daytona_http.py` + `app/tool/daytona_sandbox.py`) que não conflita com eles.

---

## 9. Pontos que precisam de auditoria posterior

1. **Dual logger system**: `app/logger.py` (loguru) e `app/utils/logger.py` (structlog) coexistem. É necessário confirmar se ambos são necessários ou se há confusão de responsabilidades.

2. **Segunda definição de `DaytonaHTTPError`**: O arquivo `app/daytona/sandbox.py` não define nem importa `DaytonaHTTPError`, mas ferramentas de análise estática podem sinalizar que `app/integrations/daytona_http.py` define `DaytonaHTTPError` enquanto `app/tool/daytona_sandbox.py` o importa. Confirmar se o fluxo de exceção está completo.

3. **Testes insuficientes**: `tests/` contém apenas 4 testes focados na sandbox Docker local. Não há testes unitários para:
   - Nenhum agente (Manus, BrowserAgent, SWEAgent, etc.)
   - Nenhuma tool (PythonExecute, StrReplaceEditor, BrowserUseTool, DaytonaSandboxTool, etc.)
   - Flow (PlanningFlow)
   - Integração Daytona HTTP
   - Geração de imagem
   - Config/app/config.py
   - LLM client
4. **Scripts de diagnóstico não consolidados**: `scripts/` contém 10 scripts de diagnóstico que validam aspectos específicos da API Daytona. Em momento oportuno, podem ser consolidados em um suite de testes formal.

5. **`app/daytona/` vs `app/integrations/`**: Duas implementações paralelas para Daytona. A configuração local usa apenas `app/integrations/daytona_http.py`, mas `app/daytona/` permanece no repositório. Auditar se há risco de importação acidental.

6. **`app/tool/sandbox/` vs `app/tool/daytona_sandbox.py`**: Duas abordagens concorrentes (SDK vs HTTP). A configuração local usa apenas `app/tool/daytona_sandbox.py`. Confirmar que nenhum agente importa acidentalmente as tools do SDK.

7. **`config.toml` ignorado mas `config.example.toml` versionado**: Confirmar que `config.toml` não contém chaves reais e que o `.gitignore` o exclui corretamente (já confirmado: linhas 204, 212, 217 do `.gitignore`).

8. **`test_groq.py` no `.gitignore`**: Este arquivo está listado no `.gitignore` mas atualmente está presente no repositório. Verificar se foi commitado acidentalmente ou se é esperado.

9. **Chart visualization com dependências Node**: `app/tool/chart_visualization/` inclui `package.json`, `tsconfig.json` e `node_modules` (ignorado). Verificar se `npx ts-node` está disponível no ambiente e se a instalação dessas dependências está documentada.

10. **`output_images/` ignorado**: Diretório onde `ImageGeneratorTool` salva imagens. Confirmar que existe ou é criado em tempo de execução (já confirmado: `Path("output_images").mkdir(parents=True, exist_ok=True)` no `image_generator.py`).

11. **Compatibilidade `app/__init__.py` vs `setup.py`**: `app/__init__.py` permite 3.11–3.13, mas `setup.py` declara `python_requires=">=3.12"`. Leve inconsistência.

12. **MCP config**: `config/mcp.example.json` contém exemplos de configuração de servidores MCP. Confirmar que o formato é compatível com o parser em `app/config.py`.
