# REPOSITORY_AUDIT

> Documento gerado em 24/06/2026.
> Auditoria técnica do repositório OpenManus — adaptação local com integrações externas.
> Baseado em `docs/REPOSITORY_INVENTORY.md` e leitura direta do código-fonte.
> Nenhum arquivo foi modificado durante esta auditoria.

---

## 1. Resumo executivo

### Estado atual do projeto

O repositório é uma adaptação local do OpenManus (v0.1.0, MIT, FoundationAgents). O fork original foi estendido com 3 integrações externas funcionais (Groq, Pollinations, Daytona HTTP) e documentação de suporte. O core do OpenManus permanece intacto, exceto pelo arquivo `app/agent/manus.py` que foi modificado para registrar as novas tools.

### Módulos validados

| Módulo | Status | Evidência |
|---|---|---|
| Groq (LLM) | Funcional | `config.toml` ativo, `test_groq.py` |
| Pollinations (generate_image) | Funcional | Tool registrada no Manus, sem teste dedicado |
| Daytona HTTP API | Funcional | `scripts/test_daytona_http.py` aprovado |
| DaytonaSandboxTool v0.2.1 | Funcional | `scripts/test_daytona_sandbox_tool.py` + `scripts/test_manus_daytona_tool.py` aprovados |
| Sandbox Docker local | Original intacto | 4 testes em `tests/sandbox/` |
| A2A protocol | Original intacto | Não testado localmente |

### Riscos principais

1. **Cobertura de testes insuficiente**: Nenhum teste unitário para agents, tools, flows ou integrações locais.
2. **Duas implementações Daytona paralelas**: `app/daytona/` (SDK, não usada) e `app/integrations/` (HTTP, ativa). Risco de importação acidental.
3. **Dependências externas pesadas**: `browser-use`, `crawl4ai`, `playwright`, `docker` podem falhar em Windows sem configuração adicional.
4. **`test_groq.py` commitado apesar de estar no `.gitignore`**: Pode indicar vazamento de configuração.
5. **Dual logger system**: `app/logger.py` (loguru) e `app/utils/logger.py` (structlog) — risco de inconsistência de saída.

### Próximos passos recomendados

1. Estabilizar testes de regressão para as integrações locais.
2. Unificar logger system ou documentar a separação de responsabilidades.
3. Consolidar scripts de diagnóstico em suíte de testes formal.
4. Auditar e documentar a convivência das duas implementações Daytona.
5. Corrigir `.gitignore` para `test_groq.py` (remover do tracking ou do gitignore).

---

## 2. Módulos funcionais validados

### 2.1 Groq

| Aspecto | Observação |
|---|---|
| **Arquivo de configuração** | `config/config.toml` — modelo `llama-3.3-70b-versatile`, base_url `https://api.groq.com/openai/v1` |
| **Chave** | `env:GROQ_API_KEY` — resolvida em runtime por `app/config.py:resolve_env()` |
| **Cliente LLM** | `app/llm.py` — compatível com OpenAI SDK |
| **Teste** | `test_groq.py` — teste rápido de conectividade (requer `GROQ_API_KEY`) |
| **Risco** | Baixo. O provedor é configurável via TOML. A troca para outro LLM requer apenas alteração em `config.toml`. |
| **Observação** | `config.toml` está no `.gitignore` e **não** deve ser commitado. |

### 2.2 Pollinations / generate_image

| Aspecto | Observação |
|---|---|
| **Arquivo** | `app/tool/image_generator.py` (~99 linhas) |
| **Tool registrada como** | `generate_image` |
| **API** | `https://gen.pollinations.ai/image/...` com parâmetros query |
| **Chave** | `POLLINATIONS_API_KEY` — opcional, passada como query param `&key=` |
| **Saída** | Salva em `output_images/desenho_<uuid>.jpg/png/webp` |
| **Resposta** | Caminho local + URL usada (com chave redactada) |
| **Teste dedicado** | Nenhum |
| **Risco** | Médio. Sem teste automatizado. Depende de API externa (Pollinations). Timeout de 120s pode travar o agente. |
| **Observação** | `output_images/` está no `.gitignore`. O diretório é criado em runtime (`mkdir(parents=True, exist_ok=True)`). |

### 2.3 Daytona HTTP API

| Aspecto | Observação |
|---|---|
| **Arquivo** | `app/integrations/daytona_http.py` (~490 linhas) |
| **Classe** | `DaytonaHTTPClient` |
| **Chave** | `DAYTONA_API_KEY` (obrigatória), `DAYTONA_ORGANIZATION_ID` (opcional) |
| **Endpoint base** | `https://app.daytona.io/api` |
| **Toolbox base** | `https://proxy.app.daytona.io/toolbox` |
| **Transporte** | `httpx` síncrono (`httpx.Client`) |
| **Teste relacionado** | `scripts/test_daytona_http.py` (smoke test) |
| **Risco** | Baixo-Médio. Sem testes unitários (apenas script de integração). Cria sandboxes reais na conta Daytona (custo potencial). |
| **Observação** | Substitui o SDK Python `daytona` para evitar conflitos de dependência. |

### 2.4 DaytonaSandboxTool

| Aspecto | Observação |
|---|---|
| **Arquivo** | `app/tool/daytona_sandbox.py` (~233 linhas) |
| **Tool registrada como** | `daytona_sandbox` |
| **Ação única** | `run_python_code` |
| **Fluxo** | `Manus → daytona_sandbox → DaytonaHTTPClient → sandbox efêmera → execução Python → stdout/result.txt → cleanup → deleção` |
| **Limites** | `MAX_CODE_CHARS=20000`, `MAX_STDOUT_CHARS=12000`, `MAX_RESULT_FILE_CHARS=12000`, `DEFAULT_TIMEOUT=30`, `MAX_TIMEOUT=120` |
| **Contrato** | Documentado em `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` |
| **Testes aprovados** | `scripts/test_daytona_sandbox_tool.py` (3 cenários), `scripts/test_manus_daytona_tool.py` (end-to-end via Manus) |
| **Risco** | Baixo. Bem isolada, contrato claro, testes de integração aprovados. |
| **Observação** | Não reusa sandbox entre chamadas. Cada execução cria sandbox efêmera com nome `openmanus-tool-xxxxxxxx`. |

### 2.5 Scripts de teste aprovados

| Script | O que valida | Risco se falhar |
|---|---|---|
| `scripts/test_daytona_http.py` | API key, conexão, listagem | Baixo — smoke test |
| `scripts/test_daytona_toolbox_execute.py` | Execução remota de comandos | Baixo |
| `scripts/test_daytona_file_api.py` | Upload/download/validação | Baixo |
| `scripts/test_daytona_code_execution_flow.py` | Ciclo completo de execução | Baixo |
| `scripts/test_daytona_sandbox_tool.py` | DaytonaSandboxTool isolada (3 cenários) | Médio — valida contrato |
| `scripts/test_manus_daytona_tool.py` | Manus → daytona_sandbox end-to-end | Médio — valida integração |

---

## 3. Módulos originais do OpenManus

### 3.1 Agentes

| Agente | Arquivo | Risco de alteração | Observação |
|---|---|---|---|
| `BaseAgent` | `app/agent/base.py` | Alto | Base de toda hierarquia. Qualquer alteração afeta todos os agentes. Sem testes. |
| `ReActAgent` | `app/agent/react.py` | Alto | Loop think/act. Núcleo do comportamento do agente. Sem testes. |
| `ToolCallAgent` | `app/agent/toolcall.py` | Alto | Dispatcher de tools. Herdado por todos os agentes concretos. Sem testes. |
| `Manus` | `app/agent/manus.py` | **Modificado localmente** | Adicionadas `DaytonaSandboxTool` e `ImageGeneratorTool`. Também adicionado suporte a MCP. |
| `BrowserAgent` | `app/agent/browser.py` | Médio | Depende de `browser-use` e Playwright. Pode falhar sem browser. |
| `MCPAgent` | `app/agent/mcp.py` | Baixo | Simples, conecta a servidores MCP. |
| `SWEAgent` | `app/agent/swe.py` | Médio | Usa Bash + StrReplaceEditor. |
| `DataAnalysis` | `app/agent/data_analysis.py` | Médio | Depende do chart_visualization (Node.js + Puppeteer). |
| `SandboxManus` | `app/agent/sandbox_agent.py` | **Não usado localmente** | Depende do SDK Daytona. |

**Fato observado**: Nenhum agente possui testes unitários em `tests/`. Apenas `SandboxManus` tem testes indiretos via scripts em `scripts/` (que testam a tool, não o agente).

### 3.2 Tools originais

| Tool | Arquivo | Risco | Observação |
|---|---|---|---|
| `Bash` | `app/tool/bash.py` | Médio | Executa comandos shell arbitrários. Risco de segurança se não sanitizado. |
| `PythonExecute` | `app/tool/python_execute.py` | Médio | Executa código Python arbitrário. |
| `StrReplaceEditor` | `app/tool/str_replace_editor.py` | Médio | Modifica arquivos no sistema de arquivos local. |
| `BrowserUseTool` | `app/tool/browser_use_tool.py` | Médio | Depende de Playwright + browser. Pode não funcionar em Windows sem config. |
| `WebSearch` | `app/tool/web_search.py` | Baixo | Chamadas de API externa. |
| `CreateChatCompletion` | `app/tool/create_chat_completion.py` | Baixo | Wrapper do LLM. |
| `AskHuman` | `app/tool/ask_human.py` | Baixo | Apenas input do usuário. |
| `PlanningTool` | `app/tool/planning.py` | Médio | Gerencia planos multi-passo. |
| `Terminate` | `app/tool/terminate.py` | Baixo | Apenas finaliza execução. |
| `Crawl4aiTool` | `app/tool/crawl4ai.py` | Médio | Depende de `crawl4ai` (pode exigir Playwright/aiohttp). |
| `ComputerUseTool` | `app/tool/computer_use_tool.py` | Alto | Automação de desktop (mouse, teclado, screenshot). Risco de segurança. |
| `FileOperator` | `app/tool/file_operators.py` | Médio | Abstração de I/O — LocalFileOperator + SandboxFileOperator. |

**Fato observado**: Nenhuma tool original possui testes unitários.

### 3.3 Search tools

| Tool | Arquivo | Risco | Observação |
|---|---|---|---|
| `GoogleSearchTool` | `app/tool/search/google_search.py` | Baixo | Requer API key do Google Custom Search. |
| `BaiduSearchTool` | `app/tool/search/baidu_search.py` | Baixo | Requer API key do Baidu. |
| `BingSearchTool` | `app/tool/search/bing_search.py` | Baixo | Requer API key do Bing. |
| `DuckDuckGoSearchTool` | `app/tool/search/duckduckgo_search.py` | Baixo | Não requer API key. |

**Observação**: `app/tool/web_search.py` (WebSearch) gerencia todos os motores com falloff. Nenhum teste unitário.

### 3.4 Flows

| Flow | Arquivo | Risco | Observação |
|---|---|---|---|
| `BaseFlow` | `app/flow/base.py` | Alto | Classe base abstrata. |
| `FlowFactory` | `app/flow/flow_factory.py` | Médio | Factory method. |
| `PlanningFlow` | `app/flow/planning.py` | Alto | Orquestra agentes (Manus, DataAnalysis). Sem testes. |

### 3.5 Sandbox Docker local

| Componente | Arquivo | Risco | Teste | Observação |
|---|---|---|---|---|
| `DockerSandbox` | `app/sandbox/core/sandbox.py` | Médio | `test_sandbox.py` | Requer Docker runtime. |
| `AsyncDockerizedTerminal` | `app/sandbox/core/terminal.py` | Médio | `test_docker_terminal.py` | Requer Docker. |
| `SandboxManager` | `app/sandbox/core/manager.py` | Médio | `test_sandbox_manager.py` | Pool management. |
| `LocalSandboxClient` | `app/sandbox/client.py` | Médio | `test_client.py` | Factory. |
| `BaseSandboxClient` | `app/sandbox/client.py` | Médio | `test_client.py` | ABC. |

**OBS**: Os 4 testes em `tests/sandbox/` são os **únicos** testes unitários formais do repositório. Eles dependem de Docker instalado. A configuração atual (`config.toml`) não usa sandbox (`use_local` não definido, default `false`).

### 3.6 Daytona SDK original (NÃO usado)

| Componente | Arquivo | Risco | Observação |
|---|---|---|---|
| `create_sandbox` | `app/daytona/sandbox.py` | **Não usado** | Requer `pip install daytona==0.21.8`. |
| `SandboxToolsBase` | `app/daytona/tool_base.py` | **Não usado** | Depende do SDK daytona. |
| `README.md` | `app/daytona/README.md` | **Não usado** | Instruções para fluxo SDK. |

**Risco**: Presença de `from daytona import ...` e `from app.daytona import ...` em arquivos não utilizados. Se alguém executar `sandbox_main.py` sem o SDK instalado, receberá `ModuleNotFoundError`. Se o SDK estiver instalado, pode conflitar com a implementação HTTP.

### 3.7 MCP

| Componente | Arquivo | Risco | Observação |
|---|---|---|---|
| `MCPClientTool` | `app/tool/mcp.py` | Baixo | Wrapper de tools MCP. |
| `MCPClients` | `app/tool/mcp.py` | Médio | Gerencia conexões SSE/stdio. |
| `MCPServer` | `app/mcp/server.py` | Baixo | Servidor FastMCP. |

**Observação**: O `MCPServer` expõe tools do OpenManus (bash, browser, str_replace_editor, terminate) como servidor MCP. Isso pode ser um risco de segurança se exposto em rede.

### 3.8 Protocolo A2A

| Componente | Arquivo | Risco | Observação |
|---|---|---|---|
| Servidor A2A | `protocol/a2a/app/main.py` | Baixo | Starlette + uvicorn. |
| `A2AManus` | `protocol/a2a/app/agent.py` | Baixo | Wrapper. |
| `ManusExecutor` | `protocol/a2a/app/agent_executor.py` | Baixo | Implementação A2A. |

**Observação**: Módulo experimental separado. Não integrado ao entry point principal. Requer uvicorn e Starlette.

---

## 4. Módulos adicionados ou modificados localmente

### 4.1 `app/integrations/daytona_http.py` (novo)

| Aspecto | Detalhe |
|---|---|
| **Tamanho** | ~490 linhas |
| **Classes** | `DaytonaHTTPError` (RuntimeError), `DaytonaHTTPClient` |
| **Dependências** | `httpx` (já presente em `requirements.txt`) |
| **Padrão** | Cliente HTTP síncrono (usa `httpx.Client` diretamente, sem async) |
| **Tratamento de erro** | `DaytonaHTTPError` com mensagens descritivas, timeout e HTTP error handling |
| **Risco** | **Baixo-Médio**. Sem testes unitários. Métodos como `create_sandbox()` e `delete_sandbox()` fazem chamadas reais à API Daytona (custos potenciais). |
| **Observação** | Usa `_toolbox_request()` para chamadas Toolbox (execução remota, arquivos). A URL Toolbox contém o sandbox_id diretamente na URL. |

### 4.2 `app/tool/daytona_sandbox.py` (novo)

| Aspecto | Detalhe |
|---|---|
| **Tamanho** | ~233 linhas |
| **Classe** | `DaytonaSandboxTool` (extends `BaseTool`) |
| **Nome da tool** | `daytona_sandbox` |
| **Ação** | `run_python_code` (única) |
| **Dependências** | `app/integrations.daytona_http.DaytonaHTTPClient` |
| **Importações proibidas** | `from daytona import ...`, `from app.daytona import ...`, `from app.sandbox import ...`, `from app.tool.sandbox import ...` |
| **Resposta** | JSON com `ok`, `exitCode`, `stdout`, `result_file_found`, `cleanup` |
| **Limites de segurança** | `MAX_CODE_CHARS=20000`, `MAX_STDOUT_CHARS=12000`, `MAX_RESULT_FILE_CHARS=12000`, `MAX_TIMEOUT=120` |
| **Cleanup obrigatório** | Remove diretório remoto + solicita deleção da sandbox, mesmo em erro |
| **Risco** | **Baixo**. Bem isolada, contrato claro, testes de integração aprovados. |
| **Observação** | Cada execução é isolada (sandbox efêmera). A tool é usada exclusivamente pelo `Manus` agent. |

### 4.3 `app/tool/image_generator.py` (novo)

| Aspecto | Detalhe |
|---|---|
| **Tamanho** | ~99 linhas |
| **Classe** | `ImageGeneratorTool` (extends `BaseTool`) |
| **Nome da tool** | `generate_image` |
| **API** | Pollinations (`https://gen.pollinations.ai/image/...`) |
| **Dependências** | `httpx` assíncrono (`httpx.AsyncClient`) |
| **Chave** | `POLLINATIONS_API_KEY` (opcional) |
| **Saída** | Salva em `output_images/desenho_<uuid>.jpg/png/webp` |
| **Tratamento de erro** | Timeout, HTTPError, content-type validation |
| **Risco** | **Médio**. Sem teste dedicado. Depende de API externa (Pollinations). Timeout de 120s. |
| **Observação** | A chave é redactada na resposta (`***REDACTED***`). Salvamento local pode encher disco. |

### 4.4 `app/agent/manus.py` (modificado)

| Aspecto | Detalhe |
|---|---|
| **Modificações identificadas** | Adicionados imports e tools: `DaytonaSandboxTool`, `ImageGeneratorTool`, `MCPClients`, `MCPClientTool` |
| **ToolCollection** | 7 tools registradas (PythonExecute, BrowserUseTool, StrReplaceEditor, AskHuman, ImageGeneratorTool, Terminate, DaytonaSandboxTool) |
| **MCP** | `initialize_mcp_servers()` carrega servidores MCP do `config/mcp.json` |
| **Risco** | **Médio**. Sem testes. Alteração no ToolCollection pode afetar comportamento do agente (mais tools = mais escolhas para o LLM). A integração MCP adiciona complexidade. |
| **Observação** | O `MCPClients` é adicionado via `available_tools.add_tools()` em runtime. Se `mcp.json` não existir, `MCPSettings.load_server_config()` retorna dict vazio. |

### 4.5 `app/tool/__init__.py` (modificado)

| Aspecto | Detalhe |
|---|---|
| **Modificações identificadas** | Adicionados exports: `ImageGeneratorTool`, `DaytonaSandboxTool` |
| **`__all__`** | 12 símbolos exportados |
| **Risco** | **Baixo**. Apenas re-exportação. |
| **Observação** | `Crawl4aiTool` e `PlanningTool` foram adicionados pelo upstream (não por nós). |

### 4.6 Configurações relacionadas a `env:`

| Arquivo | Seção | Chave `env:` |
|---|---|---|
| `config/config.toml` | `[llm]` | `api_key = "env:GROQ_API_KEY"` |
| `config/config.toml` | `[llm.vision]` | `api_key = "env:GROQ_API_KEY"` |
| `config/config.toml` | `[daytona]` | `daytona_api_key = "env:DAYTONA_API_KEY"` |
| `config/config.example.toml` | — | Não usa `env:` (chaves literais) |

**Mecanismo**: `app/config.py:resolve_env()` identifica valores iniciados com `env:`, extrai o nome da variável e chama `os.environ.get()`. Se a variável não existir, levanta `ValueError`.

**Risco**: Baixo. Mecanismo testado pelo uso. Falta de variável de ambiente trava o boot com erro claro.

---

## 5. Análise de risco por área

### 5.1 Risco: Muito Alto (requer teste antes de qualquer alteração)

| Área | Motivo | Teste necessário |
|---|---|---|
| `app/agent/base.py` | Base de toda hierarquia de agentes | Testar todos os agentes que herdam dela |
| `app/agent/react.py` | Núcleo do loop think/act | Testar comportamento de step() em todos os agentes |
| `app/agent/toolcall.py` | Dispatcher de tools | Testar execução de todas as tools registradas |
| `app/flow/planning.py` | Orquestra agentes | Testar fluxo multi-passo completo |

### 5.2 Risco: Alto

| Área | Motivo | Teste necessário |
|---|---|---|
| `app/llm.py` | Cliente LLM central (~480 linhas) | Testar chamada, retry, token counting, multimodal |
| `app/config.py` | Carregamento de config (~399 linhas) | Testar parsing TOML, `env:` resolver |
| `app/agent/manus.py` | Modificado localmente, sem testes | Testar inicialização, MCP, todas as tools |
| `app/schema.py` | Modelos de dados compartilhados | Testar serialização/desserialização |
| `app/tool/computer_use_tool.py` | Automação de desktop (risco de segurança) | Testar em ambiente isolado |
| `app/tool/bash.py` | Execução shell arbitrária | Testar sanitização de comandos |

### 5.3 Risco: Médio

| Área | Motivo | Teste necessário |
|---|---|---|
| `app/tool/browser_use_tool.py` | Depende de Playwright + browser | Testar instalação do Playwright |
| `app/tool/crawl4ai.py` | Depende de crawl4ai | Testar import e chamada básica |
| `app/tool/str_replace_editor.py` | Modifica arquivos locais | Testar operações de I/O |
| `app/tool/python_execute.py` | Executa código arbitrário | Testar timeout e isolamento |
| `app/tool/image_generator.py` | **Adicionado localmente**, sem teste | Testar chamada HTTP e salvamento |
| `app/tool/daytona_sandbox.py` | **Adicionado localmente** | Já testado via scripts |
| `app/integrations/daytona_http.py` | **Adicionado localmente**, sem teste unitário | Testar cada método HTTP |
| `app/sandbox/core/` | Requer Docker em runtime | Testar com Docker disponível |
| `app/tool/mcp.py` | Conexões de rede externas | Testar conexão SSE/stdio |
| `app/mcp/server.py` | Expõe tools como servidor MCP | Testar segurança de rede |
| `protocol/a2a/` | Experimental, não testado localmente | Testar servidor Starlette |
| `chart_visualization/` | Requer Node.js + Puppeteer | Testar instalação de dependências |

### 5.4 Risco: Baixo

| Área | Motivo |
|---|---|
| `app/prompt/` | Apenas strings de texto (prompts). Alterar prompts pode afetar comportamento, mas não quebra execução. |
| `app/agent/browser.py` | Especializado, impacto limitado. |
| `app/agent/swe.py` | Especializado, ~30 linhas. |
| `app/agent/data_analysis.py` | Especializado, ~30 linhas. |
| `app/agent/mcp.py` | Simples, ~100 linhas. |
| `app/exceptions.py` | Apenas classes de exceção. |
| `app/logger.py` / `app/utils/logger.py` | Apenas logging. |
| `config/exemplos` | Não usados em runtime. |
| `scripts/` | Scripts de diagnóstico, não importados pelo core. |
| `.github/` | CI/CD, não afeta runtime. |
| `Dockerfile` | Apenas para container. |

---

## 6. Auditoria de dependências

### 6.1 `requirements.txt` (42 dependências)

| Dependência | Versão | Risco | Observação |
|---|---|---|---|
| `pydantic~=2.10.6` | 2.10.x | Baixo | Core do OpenManus |
| `openai~=1.66.3` | 1.66.x | Baixo | SDK OpenAI (compatível com Groq) |
| `httpx>=0.27.0` | 0.27+ | Baixo | Usado pela integração Daytona HTTP |
| `browser-use~=0.1.40` | 0.1.40 | Médio | Dependência grande. Requer Playwright. Pode ter conflitos no Windows. |
| `crawl4ai~=0.6.3` | 0.6.3 | Médio | Dependência grande. Pode exigir binários extras. |
| `playwright~=1.51.0` | 1.51 | Médio | Requer `playwright install` para baixar browsers. |
| `docker~=7.1.0` | 7.1 | Baixo | SDK Docker. Só necessário se usar sandbox local. |
| `boto3~=1.37.18` | 1.37 | Baixo | SDK AWS. Só necessário se usar Bedrock. |
| `mcp~=1.5.0` | 1.5 | Baixo | Protocolo MCP. |
| `pillow~=10.4` | 10.4 | Baixo | Processamento de imagem. |
| `numpy` | — | Baixo | Computação numérica. |
| `setuptools~=75.8.0` | 75.8 | Baixo | Build tool. |

**Dependências não utilizadas na configuração local atual** (mas necessárias para compatibilidade com o código original):

| Dependência | Usada por | Risco se removida |
|---|---|---|
| `boto3` | `app/bedrock.py` | Quebra se alguém usar Bedrock |
| `docker` | `app/sandbox/core/` | Quebra se alguém usar sandbox Docker |
| `browser-use` | `app/tool/browser_use_tool.py` | Quebra BrowserUseTool |
| `playwright` | `browser-use`, `chart_visualization` | Quebra browser e charts |
| `crawl4ai` | `app/tool/crawl4ai.py` | Quebra Crawl4aiTool |
| `gymnasium`, `browsergym` | Tools de browser | Quebra BrowserUseTool |

### 6.2 `setup.py`

| Aspecto | Observação |
|---|---|
| `python_requires` | `>=3.12` |
| `install_requires` | 15 dependências listadas (vs 42 no `requirements.txt`) |
| `entry_points` | `openmanus = main:main` |
| **Inconsistência** | `requirements.txt` tem 42 pacotes, `setup.py` tem 15. Pacotes como `docker`, `mcp`, `httpx`, `boto3`, `crawl4ai` estão em `requirements.txt` mas não em `setup.py`. |
| **Risco** | Médio. `requirements.txt` é o fonte da verdade para desenvolvimento. `setup.py` é usado para instalação como pacote PyPI — dependências faltando podem quebrar a instalação via pip. |

### 6.3 SDK Daytona (não instalado)

**Fato**: O SDK `daytona==0.21.8` **não** está em `requirements.txt` e não está instalado no venv validado.

**Arquivos que o importam**:
- `app/daytona/sandbox.py`: `from daytona import ...`
- `app/daytona/tool_base.py`: `from daytona import ...`

**Orientação técnica**: A escolha de não instalar o SDK Daytona foi baseada em conflitos de dependência observados no ambiente local. Isso é uma decisão correta para o ambiente atual desde que:
1. Nenhum código em uso importe esses módulos (verificado: `sandbox_main.py` e `app/agent/sandbox_agent.py` não são entry points usados).
2. Testes de regressão cubram a implementação HTTP alternativa.
3. A documentação (`docs/PROJECT_STATUS.md`) mantenha registro claro desta decisão.

### 6.4 Pydantic

**Versão**: `~=2.10.6` (requirements.txt) / `~=2.10.4` (setup.py)
**Risco**: Baixo. Pydantic 2.x é estável. A diferença de versão entre requirements e setup é tolerável (2.10.4 vs 2.10.6).

### 6.5 Pillow

**Versão**: `~=10.4`
**Risco**: Baixo. Usado para processamento de imagem. Pode ser necessário para visão computacional e tratamento de screenshots.

### 6.6 browser-use + playwright

**Risco**: Médio-Alto no Windows.
**Observação**: `browser-use==0.1.40` depende de `playwright`. No Windows, `playwright install` pode falhar sem configuração adicional (PowerShell execution policy, antivírus). A documentação recomenda `playwright install` como passo opcional.

### 6.7 crawl4ai

**Risco**: Médio. `crawl4ai==0.6.3` é uma dependência relativamente pesada que pode exigir binários específicos de sistema.

---

## 7. Auditoria de scripts

### 7.1 Scripts funcionais (testes de regressão)

Estes scripts validam funcionalidades core da adaptação local e **devem ser mantidos**:

| Script | Função | Deve rodar antes de alterar |
|---|---|---|
| `scripts/test_daytona_http.py` | Smoke test da API Daytona | Qualquer alteração em `app/integrations/daytona_http.py` |
| `scripts/test_daytona_sandbox_tool.py` | DaytonaSandboxTool isolada | Qualquer alteração em `app/tool/daytona_sandbox.py` |
| `scripts/test_manus_daytona_tool.py` | Manus + DaytonaSandboxTool end-to-end | Qualquer alteração em `app/agent/manus.py` ou `app/tool/daytona_sandbox.py` |

### 7.2 Scripts de diagnóstico

Estes scripts foram usados durante o desenvolvimento para explorar a API Daytona. **Não são testes de regressão**, mas documentam comportamentos observados:

| Script | Função | Pode ser arquivado |
|---|---|---|
| `scripts/create_daytona_sandbox.py` | Cria sandbox via HTTP | Sim — funcionalidade coberta pelos testes |
| `scripts/delete_daytona_sandbox.py` | Deleta sandbox via HTTP | Sim — funcionalidade coberta pelos testes |
| `scripts/inspect_daytona_file_upload.py` | 5 variantes de upload | Sim — exploratório |
| `scripts/inspect_daytona_toolbox_routes.py` | Sonda rotas Toolbox | Sim — exploratório |
| `scripts/test_daytona_code_execution_flow.py` | Ciclo completo | Sim — coberto por `test_daytona_sandbox_tool.py` |
| `scripts/test_daytona_file_api.py` | File API | Sim — exploratório |
| `scripts/test_daytona_toolbox_execute.py` | Execução de comandos | Sim — coberto por `test_daytona_sandbox_tool.py` |

### 7.3 Scripts que devem ser mantidos como teste de regressão

| Script | Motivo |
|---|---|
| `scripts/test_daytona_http.py` | Único teste direto do `DaytonaHTTPClient` |
| `scripts/test_daytona_sandbox_tool.py` | Único teste direto da `DaytonaSandboxTool` (3 cenários) |
| `scripts/test_manus_daytona_tool.py` | Único teste end-to-end do `Manus` com `daytona_sandbox` |

### 7.4 Scripts que podem futuramente ser arquivados

Após a criação de uma suíte de testes formal (`tests/`), os scripts de diagnóstico abaixo podem ser arquivados ou removidos:

- `scripts/create_daytona_sandbox.py`
- `scripts/delete_daytona_sandbox.py`
- `scripts/inspect_daytona_file_upload.py`
- `scripts/inspect_daytona_toolbox_routes.py`
- `scripts/test_daytona_code_execution_flow.py`
- `scripts/test_daytona_file_api.py`
- `scripts/test_daytona_toolbox_execute.py`

---

## 8. Candidatos à investigação antes de limpeza

> Nenhuma remoção é recomendada ainda. Apenas listagem do que precisa de confirmação antes de qualquer ação.

### 8.1 `app/daytona/` (3 arquivos)

| Arquivo | Pergunta pendente |
|---|---|
| `app/daytona/__init__.py` | Está vazio? Pode ser removido sem impacto? |
| `app/daytona/sandbox.py` | Alguém depende deste módulo além de `app/tool/sandbox/`? |
| `app/daytona/tool_base.py` | Alguém depende deste módulo além de `app/tool/sandbox/`? |
| `app/daytona/README.md` | Ainda é relevante se o SDK não é usado? |

**Confirmação necessária**: Fazer uma busca por `from app.daytona` ou `import app.daytona` em todos os arquivos `.py` para confirmar que apenas `app/tool/sandbox/` importa estes módulos.

### 8.2 `app/tool/sandbox/` (4 arquivos)

| Arquivo | Pergunta pendente |
|---|---|
| `sb_shell_tool.py` | Confirmar que nenhum agente ativo o importa |
| `sb_files_tool.py` | Confirmar que nenhum agente ativo o importa |
| `sb_browser_tool.py` | Confirmar que nenhum agente ativo o importa |
| `sb_vision_tool.py` | Confirmar que nenhum agente ativo o importa |

**Confirmação necessária**: Buscar por `from app.tool.sandbox` e `import app.tool.sandbox` em todo o código. Verificar se `SandboxManus` (`app/agent/sandbox_agent.py`) é o único consumidor.

### 8.3 `sandbox_main.py`

**Pergunta pendente**: É um entry point original que ninguém usa localmente? Confirmar que não há scripts ou referências que o chamem.

### 8.4 `test_groq.py`

**Pergunta pendente**: Está no `.gitignore` mas foi commitado. Decidir:
- Remover do tracking (`git rm --cached`) e manter no `.gitignore`, OU
- Remover do `.gitignore` e manter versionado.

### 8.5 Logger duplicado (`app/logger.py` vs `app/utils/logger.py`)

**Pergunta pendente**:
- `app/logger.py` usa `loguru`
- `app/utils/logger.py` usa `structlog`
- Qual é o logger "oficial"? Ambos são usados em arquivos diferentes?

**Confirmação necessária**: Mapear qual logger cada arquivo importa. Se ambos forem usados ativamente, documentar a separação. Se um for inativo, considerar unificação.

### 8.6 `app/tool/computer_use_tool.py`

**Pergunta pendente**: Está registrado em algum agente? Não está no `Manus`. Se não for usado, pode ser candidato a arquivamento.

### 8.7 `examples/`

**Pergunta pendente**: Os exemplos (japan-travel-plan) são relevantes para a configuração local? Foram gerados pelo OpenManus original e podem ser mantidos como demonstração.

---

## 9. Plano recomendado antes de limpeza

> Este plano é uma sugestão de ordem segura para evolução do repositório. Nenhuma ação deve ser tomada sem validação.

### Fase 1 — Estabilização de testes (prioridade alta)

| Passo | Ação | Verificação |
|---|---|---|
| 1.1 | Criar `tests/test_daytona_http.py` com pytest para `DaytonaHTTPClient` | `pytest tests/test_daytona_http.py -v` |
| 1.2 | Criar `tests/test_daytona_sandbox_tool.py` com pytest | `pytest tests/test_daytona_sandbox_tool.py -v` |
| 1.3 | Criar `tests/test_image_generator.py` com mock HTTP | `pytest tests/test_image_generator.py -v` |
| 1.4 | Garantir que scripts funcionais passem | `python scripts/test_daytona_http.py` |

### Fase 2 — Documentação e diagnóstico (prioridade média)

| Passo | Ação | Verificação |
|---|---|---|
| 2.1 | Mapear uso de `app/logger.py` vs `app/utils/logger.py` | grep por imports |
| 2.2 | Confirmar que `app/daytona/` só é importado por `app/tool/sandbox/` | `grep -r "from app.daytona\|import app.daytona" app/` |
| 2.3 | Confirmar que `app/tool/sandbox/` só é importado por `app/agent/sandbox_agent.py` | `grep -r "from app.tool.sandbox\|import app.tool.sandbox" app/` |
| 2.4 | Decidir situação do `test_groq.py` (remover tracking ou remover do `.gitignore`) | `git rm --cached test_groq.py` OU editar `.gitignore` |

### Fase 3 — Limpeza controlada (prioridade baixa)

| Passo | Ação | Condição |
|---|---|---|
| 3.1 | Arquivar scripts de diagnóstico em `scripts/archive/` | Após criação de testes formais |
| 3.2 | Unificar logger system | Após confirmação de uso |
| 3.3 | Consolidar configurações de exemplo duplicadas | Após estabilização dos testes |
| 3.4 | Revisar dependências não utilizadas em `requirements.txt` | Após mapeamento completo de imports |

### Ordem segura para alterações em módulos existentes

```
1. Rodar scripts de teste funcionais (test_daytona_http, etc.)
2. Rodar pytest (testes sandbox Docker)
3. Fazer alteração
4. Rodar scripts de teste novamente
5. Rodar pip check
6. Verificar git status
7. Commitar
```

---

## Apêndice A: Mapa de importação cruzada entre módulos locais e originais

| Arquivo local | Importa de | Risco de acoplamento |
|---|---|---|
| `app/integrations/daytona_http.py` | `httpx` | Baixo — apenas lib externa |
| `app/tool/daytona_sandbox.py` | `app.integrations.daytona_http`, `app.tool.base` | Médio — depende do BaseTool |
| `app/tool/image_generator.py` | `httpx`, `app.tool.base` | Médio — depende do BaseTool |
| `app/agent/manus.py` (modificado) | `app.tool.daytona_sandbox`, `app.tool.image_generator`, `app.tool.mcp` | Alto — vários acoplamentos |

| Módulo original | Importado por | Risco de quebra |
|---|---|---|
| `app/tool/base.py` | `daytona_sandbox.py`, `image_generator.py` | Alto — qualquer mudança na interface BaseTool quebra as tools locais |
| `app/agent/toolcall.py` | `manus.py` | Alto — qualquer mudança no fluxo think/act afeta o Manus |
| `app/config.py` | `manus.py` | Médio — mudanças no schema de config podem afetar inicialização |

## Apêndice B: Sumário de arquivos por origem

| Origem | Quantidade | Caminhos |
|---|---|---|
| Original (upstream) | ~80+ | Todo `app/` exceto modificações, `config/*.example*`, `.github/`, `tests/sandbox/`, `protocol/`, `examples/`, `Dockerfile`, `setup.py`, `requirements.txt`, `main.py`, `run_*.py`, `sandbox_main.py`, `README.md` |
| Adicionado localmente | 14 | `app/integrations/__init__.py`, `app/integrations/daytona_http.py`, `app/tool/daytona_sandbox.py`, `app/tool/image_generator.py`, `scripts/` (10 arquivos), `test_groq.py` |
| Modificado localmente | 2 | `app/agent/manus.py`, `app/tool/__init__.py` |
| Adicionado localmente (docs) | 2 | `docs/PROJECT_STATUS.md`, `docs/DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md` |
| Adicionado localmente (config) | 1 | `config/config.toml` (ignorado) |
