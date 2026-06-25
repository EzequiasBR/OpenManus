# DEPENDENCY_AUDIT

> Documento gerado em 24/06/2026.
> Auditoria técnica de dependências do OpenManus — adaptação local com integrações externas.
> Nenhum arquivo foi modificado durante esta auditoria.
> **Esta auditoria não autoriza limpeza automática. Ela identifica riscos, inconsistências e pontos que precisam de decisão estratégica antes de qualquer alteração em dependências.**

---

## 1. Resumo executivo

### Estado atual

O projeto declara 42 dependências em `requirements.txt` e 15 em `setup.py`. A auditoria baseada em imports reais identificou:

| Categoria | Quantidade |
|---|---|
| Dependências com import direto comprovado | 23 |
| Dependências sem import direto confirmado nesta auditoria | 10 |
| Dependências transitivas (não importadas diretamente) | 2 |
| Dependência de backport/compatibilidade | 1 |
| Dependência build-only | 1 |
| Dependências test-only | 2 |

### Dependências essenciais (runtime core)

`pydantic`, `openai`, `tenacity`, `loguru`, `tiktoken`, `mcp`, `httpx`, `requests`, `beautifulsoup4`, `tomli` (backport)

### Dependências opcionais (por funcionalidade)

`boto3` (Bedrock), `docker` (sandbox local), `crawl4ai` (crawling), `browser-use` + `playwright` (automação de navegador), `uvicorn` + `fastapi` (A2A server — arquivado, DEFER_FUTURE, sem contrato funcional), `googlesearch-python`, `baidusearch`, `duckduckgo_search` (buscadores específicos)

### Dependências problemáticas

| Dependência | Problema |
|---|---|
| `browser-use==0.1.40` | Dependência grande, requer Playwright, instalação complexa no Windows |
| `crawl4ai==0.6.3` | Dependência pesada com binários nativos, falha frequente em Windows |
| `playwright==1.51.0` | Requer `playwright install` para baixar browsers (~400MB) |
| `docker==7.1.0` | Requer Docker Desktop em execução |

### Principais riscos

1. **10 dependências sem import direto confirmado**: `pyyaml`, `numpy`, `datasets`, `html2text`, `gymnasium`, `browsergym`, `unidiff`, `aiofiles`, `colorama`, `huggingface-hub`. Requerem investigação antes de qualquer ação.
2. **Inconsistência entre `requirements.txt` e `setup.py`**: 27 pacotes em `requirements.txt` não estão em `setup.py`; 0 pacotes em `setup.py` que não estão em `requirements.txt`.
3. **`pillow` só é usado por módulos não utilizados** (`app/tool/sandbox/sb_browser_tool.py`, `app/tool/sandbox/sb_vision_tool.py`), mas está em ambas as listas.
4. **`setuptools` em `requirements.txt`**: É uma dependência de build, não de runtime. Não deveria estar em `requirements.txt`.

---

## 2. Ambiente validado

| Aspecto | Valor |
|---|---|
| Sistema operacional | Windows |
| Shell | PowerShell |
| Ambiente Python | `venv` local do projeto |
| Versão Python | 3.12 (conforme `setup.py` e `app/__init__.py`) |
| Provedor LLM | Groq (via API compatível com OpenAI) |
| Geração de imagem | Pollinations (via HTTP direto) |
| Sandbox remota | Daytona (via HTTP API direta, sem SDK) |
| SDK Daytona | Não instalado no venv validado |
| Estratégia de chaves | Variáveis de ambiente (`env:` prefixo em TOML) |
| Gerenciador de pacotes | `pip` |

### Dependências instaladas e validadas no ambiente local

Todas as 42 dependências de `requirements.txt` foram instaladas via `pip install -r requirements.txt`. O comando `python -m pip check` não reportou conflitos no ambiente validado.

---

## 3. Comparação entre `requirements.txt` e `setup.py`

### 3.1 Dependências presentes em ambos (14)

| Pacote | Versão em `requirements.txt` | Versão em `setup.py` |
|---|---|---|
| `pydantic` | `~=2.10.6` | `~=2.10.4` |
| `openai` | `~=1.66.3` | `>=1.58.1,<1.67.0` |
| `tenacity` | `~=9.0.0` | `~=9.0.0` |
| `pyyaml` | `~=6.0.2` | `~=6.0.2` |
| `loguru` | `~=0.7.3` | `~=0.7.3` |
| `numpy` | (sem versão) | (sem versão) |
| `datasets` | `~=3.4.1` | `>=3.2,<3.5` |
| `html2text` | `~=2024.2.26` | `~=2024.2.26` |
| `gymnasium` | `~=1.1.1` | `>=1.0,<1.2` |
| `pillow` | `~=10.4` | `>=10.4,<11.2` |
| `browsergym` | `~=0.13.3` | `~=0.13.3` |
| `uvicorn` | `~=0.34.0` | `~=0.34.0` |
| `unidiff` | `~=0.7.5` | `~=0.7.5` |
| `browser-use` | `~=0.1.40` | `~=0.1.40` |
| `googlesearch-python` | `~=1.3.0` | `~=1.3.0` |
| `aiofiles` | `~=24.1.0` | `~=24.1.0` |
| `pydantic_core` | `~=2.27.2` | `>=2.27.2,<2.28.0` |
| `colorama` | `~=0.4.6` | `~=0.4.6` |

### 3.2 Dependências presentes apenas em `requirements.txt` (24)

| Pacote | Versão | Função |
|---|---|---|
| `fastapi` | `~=0.115.11` | Servidor A2A (transitivo, arquivado, DEFER_FUTURE) |
| `tiktoken` | `~=0.9.0` | Token counting (LLM) |
| `baidusearch` | `~=1.0.3` | Buscador Baidu |
| `duckduckgo_search` | `~=7.5.3` | Buscador DuckDuckGo |
| `playwright` | `~=1.51.0` | Browser automation (transitivo via browser-use) |
| `docker` | `~=7.1.0` | Sandbox local |
| `pytest` | `~=8.3.5` | Testes |
| `pytest-asyncio` | `~=0.25.3` | Testes assíncronos |
| `mcp` | `~=1.5.0` | Protocolo MCP |
| `httpx` | `>=0.27.0` | Cliente HTTP (Daytona, imagens) |
| `tomli` | `>=2.0.0` | Backport tomllib para Python <3.11 |
| `boto3` | `~=1.37.18` | AWS Bedrock |
| `requests` | `~=2.32.3` | HTTP (web search) |
| `beautifulsoup4` | `~=4.13.3` | HTML parsing (web search) |
| `crawl4ai` | `~=0.6.3` | Web crawling |
| `huggingface-hub` | `~=0.29.2` | (sem import direto confirmado) |
| `setuptools` | `~=75.8.0` | Build-only |

### 3.3 Dependências presentes apenas em `setup.py`

Nenhuma. Todas as 15 dependências de `setup.py` estão também em `requirements.txt`.

### 3.4 Inconsistências de versão

| Pacote | `requirements.txt` | `setup.py` | Impacto |
|---|---|---|---|
| `pydantic` | `~=2.10.6` | `~=2.10.4` | Baixo. `~=2.10.4` permite 2.10.4 até 2.10.x. `~=2.10.6` é mais restritivo. O runtime usará a versão instalada, que será >= 2.10.6 com `requirements.txt`. |
| `openai` | `~=1.66.3` | `>=1.58.1,<1.67.0` | Baixo. Ambos permitem 1.66.x. `setup.py` tem下限 mais baixo (1.58.x) e上限 1.67.0. `requirements.txt` fixa em ~1.66.3. |
| `datasets` | `~=3.4.1` | `>=3.2,<3.5` | Baixo. `requirements.txt` fixa em ~3.4.1; `setup.py` permite 3.2–3.4.x. |
| `gymnasium` | `~=1.1.1` | `>=1.0,<1.2` | Baixo. `requirements.txt` fixa em ~1.1.1; `setup.py` permite 1.0–1.1.x. |
| `pillow` | `~=10.4` | `>=10.4,<11.2` | Baixo. `requirements.txt` fixa em ~10.4; `setup.py` permite 10.4–11.1.x. |
| `pydantic_core` | `~=2.27.2` | `>=2.27.2,<2.28.0` | Baixo. Compatível. |
| `html2text` | `~=2024.2.26` | `~=2024.2.26` | Idêntico (mas sem import direto confirmado nesta auditoria). |
| `browsergym` | `~=0.13.3` | `~=0.13.3` | Idêntico (mas sem import direto confirmado nesta auditoria). |

### 3.5 Impacto técnico das diferenças

A principal diferença é que `requirements.txt` contém 24 pacotes que `setup.py` não declara. Isso significa que:

- **Quem instala via `pip install openmanus`** (a partir do PyPI) terá apenas 15 dependências, e funcionalidades como sandbox Docker, Daytona HTTP, MCP, crawling, testes e buscas alternativas não funcionarão.
- **Quem instala via `pip install -r requirements.txt`** terá todas as 42 dependências, mas 10 delas não tiveram import direto confirmado.
- **Risco médio**: A disparidade pode causar confusão sobre quais dependências são realmente necessárias.

---

## 4. Classificação das dependências

### 4.1 Core runtime (obrigatórias para qualquer execução)

| Pacote | Importado em | Risco |
|---|---|---|
| `pydantic` | ~25 arquivos (config, schema, tools, agents, flows) | Crítico |
| `pydantic_core` | `app/tool/browser_use_tool.py` | Crítico |
| `openai` | `app/llm.py` | Crítico |
| `tenacity` | `app/llm.py`, `app/tool/web_search.py` | Médio |
| `loguru` | `app/logger.py` | Crítico |
| `tiktoken` | `app/llm.py` | Alto |
| `httpx` | `app/integrations/daytona_http.py`, `app/tool/image_generator.py`, `archive/openmanus/a2a_protocol_unvalidated/a2a/app/main.py`, scripts | Alto |
| `tomli` | Backport de `tomllib` (stdlib Python ≥3.11) | Baixo |
| `pyyaml` | **Sem import direto confirmado nesta auditoria** | Requer investigação |
| `setuptools` | Apenas `setup.py` | Build-only |

### 4.2 LLM / API

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `openai` | `app/llm.py` | Sim (LLM principal) |
| `tiktoken` | `app/llm.py` | Sim (token counting) |
| `boto3` | `app/bedrock.py` | Não (só Bedrock) |
| `httpx` | Vários | Sim (Daytona, imagens) |

### 4.3 Browser automation

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `browser-use` | `app/tool/browser_use_tool.py` | Não (tool opcional) |
| `playwright` | Transitiva via browser-use | Não |
| `browsergym` | **Sem import direto confirmado nesta auditoria** | Requer investigação |

**Observação**: `browser-use==0.1.40` tem instalação complexa no Windows. A tool `BrowserUseTool` só falha em runtime se chamada, não no boot.

### 4.4 Sandbox Docker

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `docker` | `app/sandbox/core/*.py` (3 arquivos), `tests/sandbox/*.py` (2 arquivos) | Não (só sandbox local) |

**Observação**: A configuração validada não usa sandbox Docker. O pacote `docker` só é necessário se `[sandbox]` for configurado.

### 4.5 Daytona HTTP

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `httpx` | `app/integrations/daytona_http.py` | Sim (integração validada) |

**Observação**: A tool `DaytonaSandboxTool` está registrada no `Manus` e é usada ativamente.

### 4.6 Imagem / Visão

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `pillow` | `app/tool/sandbox/sb_browser_tool.py`, `app/tool/sandbox/sb_vision_tool.py` | Não — ambos os arquivos são do fluxo SDK Daytona original, **não usados na configuração local** |

**Observação**: `pillow` é uma dependência de módulos que não são executados na configuração validada. Pode ser candidata a revisão, mas requer confirmação de que nenhum outro módulo a usa indiretamente.

### 4.7 Crawling / Search

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `crawl4ai` | `app/tool/crawl4ai.py` (lazy import) | Não (tool opcional) |
| `requests` | `app/tool/web_search.py`, `app/tool/search/bing_search.py` | Sim (WebSearch) |
| `beautifulsoup4` | `app/tool/web_search.py`, `app/tool/search/bing_search.py` | Sim (WebSearch) |
| `googlesearch-python` | `app/tool/search/google_search.py` | Não (motor específico) |
| `baidusearch` | `app/tool/search/baidu_search.py` | Não (motor específico) |
| `duckduckgo_search` | `app/tool/search/duckduckgo_search.py` | Não (motor específico) |

**Observação**: `WebSearch` usa múltiplos motores com fallback. Se um motor não estiver instalado, o WebSearch tenta o próximo.

### 4.8 MCP

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `mcp` | `app/mcp/server.py`, `app/tool/mcp.py` | Sim (MCP client + server) |

**Nota:** O protocolo A2A foi movido para `archive/openmanus/a2a_protocol_unvalidated/` por ser **DEFER_FUTURE** — sem contrato funcional, sem testes, sem integração com o entry point principal. Suas dependências (`fastapi`, `uvicorn`) tornaram-se órfãs e devem ser revisadas em limpeza futura.

### 4.9 Desenvolvimento / Testes

| Pacote | Importado em | Obrigatória? |
|---|---|---|
| `pytest` | 4 arquivos de teste | Não (desenvolvimento) |
| `pytest-asyncio` | 4 arquivos de teste | Não (desenvolvimento) |

### 4.10 Opcionais por funcionalidade (summary)

| Funcionalidade | Dependências | Ativa na config atual? |
|---|---|---|
| Sandbox Docker | `docker` | Não |
| AWS Bedrock | `boto3` | Não |
| Crawling web | `crawl4ai` | Sim (tool registrada) |
| Browser automation | `browser-use`, `playwright` | Sim (tool registrada) |
| A2A protocol server | `fastapi`, `uvicorn`, `httpx` | Não (arquivado, DEFER_FUTURE) |
| Google search | `googlesearch-python` | Sim (ferramenta registrada) |
| Baidu search | `baidusearch` | Sim |
| DuckDuckGo search | `duckduckgo_search` | Sim |
| Vision (sandbox SDK) | `pillow` | Não (fluxo não usado) |

---

## 5. Dependências sensíveis ou problemáticas

### 5.1 `pydantic` (~=2.10.6)

| Aspecto | Detalhe |
|---|---|
| **Status** | Crítico. Usado em ~25 arquivos. |
| **Risco** | Baixo. Pydantic 2.x é maduro e estável. |
| **Versão alternativa** | `~=2.10.4` no `setup.py`. Compatível. |
| **Recomendação** | Manter. Se houver conflito com `browser-use` ou `crawl4ai`, priorizar a versão exigida por eles. |

### 5.2 `pillow` (~=10.4)

| Aspecto | Detalhe |
|---|---|
| **Status** | Instalada, mas **não usada por nenhum módulo ativo** na configuração validada. |
| **Risco** | Baixo para o ambiente atual. Pode ser necessária se no futuro o fluxo de visão computacional for ativado. |
| **Recomendação** | Manter por enquanto. Reavaliar quando a limpeza de módulos não utilizados for feita. |

### 5.3 `crawl4ai` (~=0.6.3)

| Aspecto | Detalhe |
|---|---|
| **Status** | Instalada, importada via lazy import em `app/tool/crawl4ai.py`. |
| **Risco** | **Médio-Alto**. Dependência pesada com binários nativos. Pode falhar no Windows com `Visual C++ Redistributable` ausente. Documentação oficial lista requisitos específicos de plataforma. |
| **Comportamento se ausente** | A tool `Crawl4aiTool` tem fallback: se o import falhar, retorna mensagem de erro. O boot do agente não quebra. |
| **Recomendação** | Pode ser movida para opcionais se não for usada ativamente. Testar instalação em Windows limpo antes de atualizar. |

### 5.4 `browser-use` (~=0.1.40)

| Aspecto | Detalhe |
|---|---|
| **Status** | Instalada, importada em `app/tool/browser_use_tool.py`. |
| **Risco** | **Médio-Alto**. Dependência complexa que requer `playwright`. Versão 0.1.40 pode ter bugs não documentados. Mudanças de versão podem quebrar a tool. |
| **Comportamento se ausente** | O boot do Manus falha se `browser-use` não estiver instalada, pois `BrowserUseTool` é importado diretamente em `app/agent/manus.py`. |
| **Recomendação** | Manter versão fixada. Atualizar com cautela e testar `BrowserUseTool` após cada atualização. |

### 5.5 `playwright` (~=1.51.0)

| Aspecto | Detalhe |
|---|---|
| **Status** | Dependência transitiva de `browser-use`. |
| **Risco** | **Médio**. `playwright install` baixa ~400MB de browsers. Pode falhar em Windows sem permissões adequadas. |
| **Recomendação** | Manter. A instalação dos browsers é opcional (a documentação diz `playwright install` como passo opcional). |

### 5.6 `docker` (~=7.1.0)

| Aspecto | Detalhe |
|---|---|
| **Status** | Instalada, importada em `app/sandbox/core/*.py`. |
| **Risco** | **Médio**. O SDK Python `docker` requer Docker Engine em execução. No Windows, requer Docker Desktop. |
| **Comportamento se ausente** | A sandbox Docker local não é usada na configuração validada (`use_local = false`). O boot do agente não falha se Docker não estiver disponível. |
| **Recomendação** | Pode ser movida para opcionais. |

### 5.7 `httpx` (>=0.27.0)

| Aspecto | Detalhe |
|---|---|
| **Status** | Essencial. Usado pela integração Daytona HTTP, ImageGenerator e A2A server. |
| **Risco** | Baixo. Biblioteca madura e compatível. |
| **Recomendação** | Manter. A versão mínima `>=0.27.0` é segura. |

### 5.8 `openai` (~=1.66.3)

| Aspecto | Detalhe |
|---|---|
| **Status** | Essencial. Usado pelo cliente LLM central (`app/llm.py`). |
| **Risco** | **Médio**. A API OpenAI SDK muda com frequência. A versão `~=1.66.3` é compatível com Groq. Atualizações podem quebrar compatibilidade com `base_url` customizado. |
| **Recomendação** | Manter versão fixada. Testar com Groq, OpenAI e Ollama antes de atualizar. |

### 5.9 SDK Daytona (não instalado)

| Aspecto | Detalhe |
|---|---|
| **Status** | **Não instalado** no venv validado. |
| **Risco se instalado** | Pode conflitar com dependências existentes (relato observado, requer verificação). |
| **Risco se ausente** | Módulos `app/daytona/` e `app/tool/sandbox/` não funcionam, mas não são usados. `sandbox_main.py` quebra com `ModuleNotFoundError`. |
| **Recomendação** | Não instalar no venv principal enquanto a implementação HTTP for suficiente. Se houver necessidade futura do SDK, criar venv separado ou testar em ambiente isolado. |

---

## 6. Nota técnica sobre Daytona

### Escolha técnica atual

O ambiente validado **não usa o SDK Python da Daytona** (`daytona`). Em vez disso, usa comunicação HTTP direta implementada em `app/integrations/daytona_http.py`.

### Motivo documentado

A escolha foi baseada em:
1. **Conflitos de dependência observados** no venv principal ao instalar o SDK `daytona==0.21.8`.
2. **Estabilidade**: A implementação HTTP tem menos camadas e dependências, reduzindo superfície de falha.
3. **Simplicidade**: O cliente HTTP tem ~490 linhas e usa apenas `httpx`, que já estava em `requirements.txt`.

### Isso não é uma proibição universal

Usuários ou ambientes futuros podem optar pelo SDK Daytona se:
- Validarem que não há conflitos com as demais dependências.
- Preferirem a funcionalidade completa do SDK (sandbox persistente, VNC, etc.).
- Estiverem em ambiente onde o SDK é estável.

### Testes mínimos para trocar a abordagem

Se alguém quiser substituir a implementação HTTP pelo SDK:

1. Instalar `daytona==0.21.8` em ambiente isolado.
2. Executar `python -m pip check` para verificar conflitos.
3. Testar `app/daytona/sandbox.py` diretamente:
   ```python
   python -c "from app.daytona.sandbox import create_sandbox; print('OK')"
   ```
4. Testar `SandboxManus`:
   ```bash
   python sandbox_main.py
   ```
5. Executar scripts de teste da tool HTTP para garantir que a substituição não quebrou o fluxo:
   ```bash
   python scripts/test_daytona_sandbox_tool.py
   ```
6. Verificar se `app/tool/daytona_sandbox.py` (tool atual) continua funcionando ou precisa ser adaptada.

---

## 7. Política técnica de dependências

### Regras gerais

1. **Não atualizar dependências críticas sem teste** — especialmente `pydantic`, `openai`, `browser-use`, `mcp`.
2. **Sempre executar `python -m pip check`** antes e depois de alterar `requirements.txt`.
3. **Rodar testes relacionados** antes de commitar qualquer alteração de dependência.
4. **Registrar conflitos conhecidos** neste documento à medida que forem descobertos.
5. **Manter chaves de API fora do código** — usar variáveis de ambiente com prefixo `env:` no TOML.
6. **Separar dependências obrigatórias de opcionais** — idealmente em arquivos distintos.

### Conflitos conhecidos (até o momento)

| Conflito | Status |
|---|---|
| SDK `daytona==0.21.8` com dependências existentes | Relatado, não verificado em detalhe |
| `crawl4ai` com versões específicas de `playwright` | Requer verificação |
| `browser-use==0.1.40` com `pydantic` >2.11 | Requer verificação |

### Dependências obrigatórias vs opcionais

**Obrigatórias** (core sempre necessário):
`pydantic`, `pydantic_core`, `openai`, `tenacity`, `loguru`, `tiktoken`, `httpx`, `mcp`, `tomli`, `requests`, `beautifulsoup4`, `pyyaml` (sem import direto confirmado), `numpy` (sem import direto confirmado)

**Opcionais por funcionalidade**:
- `docker` → sandbox local
- `boto3` → AWS Bedrock
- `crawl4ai` → crawling web
- `browser-use`, `playwright` → automação de navegador
- `googlesearch-python`, `baidusearch`, `duckduckgo_search` → buscadores específicos
- `fastapi`, `uvicorn` → servidor A2A (arquivado, DEFER_FUTURE)
- `pillow` → visão computacional (fluxo não usado atualmente)
- `datasets`, `html2text`, `gymnasium`, `browsergym`, `unidiff`, `aiofiles`, `colorama`, `huggingface-hub` → **requerem investigação antes de qualquer decisão** (ver §4)

**Testes/desenvolvimento**:
- `pytest`, `pytest-asyncio`, `setuptools`

---

## 8. Checklist antes de alterar `requirements.txt`

### Pré-alteração

- [ ] `python -m pip check` — sem conflitos
- [ ] `python -m pip freeze > pip_freeze_before.txt` — snapshot do estado atual
- [ ] Boot do Manus: `python -c "from app.agent.manus import Manus; m = Manus(); print('Manus OK')"`
- [ ] Testar `generate_image`:
  ```bash
  python -c "import asyncio; from app.tool.image_generator import ImageGeneratorTool; t=ImageGeneratorTool(); asyncio.run(t.execute(prompt='test'))"
  ```
- [ ] Testar `daytona_sandbox`:
  ```bash
  python scripts/test_daytona_sandbox_tool.py
  ```
- [ ] Testar scripts Daytona essenciais:
  ```bash
  python scripts/test_daytona_http.py
  ```

### Pós-alteração

- [ ] `python -m pip check` — sem novos conflitos
- [ ] `python -m pip freeze > pip_freeze_after.txt` — comparar com snapshot anterior
- [ ] Boot do Manus novamente
- [ ] Testar `generate_image` novamente
- [ ] Testar `daytona_sandbox` novamente
- [ ] Testar scripts Daytona novamente
- [ ] Verificar se `browser-use` ainda importa corretamente:
  ```bash
  python -c "from browser_use import Browser; print('browser-use OK')"
  ```
- [ ] Verificar se `crawl4ai` ainda importa:
  ```bash
  python -c "import crawl4ai; print('crawl4ai OK')"
  ```

---

## 9. Recomendações futuras

> Nenhuma ação deve ser tomada automaticamente com base nestas recomendações. São sugestões para planejamento futuro.

### 9.1 Separar arquivos de requirements por perfil

| Arquivo | Conteúdo sugerido |
|---|---|
| `requirements.txt` | Apenas core runtime obrigatório |
| `requirements-dev.txt` | `pytest`, `pytest-asyncio`, `setuptools`, ferramentas de lint |
| `requirements-optional.txt` ou `requirements-all.txt` | Todas as dependências opcionais |

Isso permitiria:
```bash
pip install -r requirements.txt              # instalação mínima
pip install -r requirements-all.txt          # instalação completa
pip install -r requirements.txt -r requirements-dev.txt  # desenvolvimento
```

### 9.2 Sincronizar `setup.py` com `requirements.txt`

- Adicionar em `setup.py` as dependências que estão apenas em `requirements.txt` e são realmente necessárias: `tiktoken`, `httpx`, `mcp`, `docker`, `boto3`, `requests`, `beautifulsoup4`, `crawl4ai`, `playwright`, `baidusearch`, `duckduckgo_search`, `tomli`.
- Ou, alternativamente, alinhar `requirements.txt` com `setup.py` e usar `extras_require` no `setup.py` para grupos opcionais.

### 9.3 Investigar dependências sem import direto confirmado (antes de qualquer remoção)

| Pacote | Risco estimado (baseado apenas em import estático) |
|---|---|
| `pyyaml` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `numpy` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `datasets` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `html2text` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `gymnasium` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `browsergym` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `unidiff` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `aiofiles` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `colorama` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `huggingface-hub` | Aparentemente baixo — sem import direto confirmado nesta auditoria |
| `setuptools` | Aparentemente baixo — build-only, não deveria estar em requirements |

**Condição**: Remover apenas após confirmar que nenhum código as importa dinamicamente (ex.: `__import__`, `importlib`) e que nenhuma dependência transitiva as exige.

### 9.4 Registrar explicitamente dependências do chart_visualization

O submódulo `app/tool/chart_visualization/` tem seu próprio `package.json` com dependências Node.js. Essas dependências não fazem parte do `requirements.txt` e devem ser documentadas separadamente:
- `@visactor/vchart`
- `@visactor/vmind`
- `puppeteer`
- `ts-node`

### 9.5 Próximos passos (ordem sugerida)

1. Investigar dependências sem import direto confirmado antes de qualquer remoção.
2. Separar `requirements-dev.txt` com `pytest`, `pytest-asyncio`.
3. Separar `requirements-optional.txt` com `docker`, `boto3`, `crawl4ai`, buscadores específicos.
4. Sincronizar `setup.py` com `requirements.txt` (ou decidir manter apenas `requirements.txt` como fonte da verdade).
5. Mover `setuptools` de `requirements.txt` para `requirements-dev.txt`.
6. Documentar as dependências Node.js do chart_visualization.

---

## Apêndice A: Mapa completo dependência ↔ arquivos importadores

| Dependência | Arquivos que importam | Risco |
|---|---|---|
| `pydantic` | `app/config.py`, `app/schema.py`, `app/tool/base.py`, `app/tool/web_search.py`, `app/tool/browser_use_tool.py`, `app/tool/create_chat_completion.py`, `app/tool/computer_use_tool.py`, `app/tool/sandbox/sb_browser_tool.py`, `app/tool/sandbox/sb_files_tool.py`, `app/tool/sandbox/sb_vision_tool.py`, `app/tool/search/base.py`, `app/tool/chart_visualization/data_visualization.py`, `app/agent/base.py`, `app/agent/browser.py`, `app/agent/data_analysis.py`, `app/agent/manus.py`, `app/agent/mcp.py`, `app/agent/react.py`, `app/agent/sandbox_agent.py`, `app/agent/toolcall.py`, `app/agent/swe.py`, `app/flow/base.py`, `app/flow/planning.py`, `app/daytona/tool_base.py`, `archive/openmanus/a2a_protocol_unvalidated/a2a/app/agent.py` | Crítico |
| `openai` | `app/llm.py`, `test_groq.py` | Crítico |
| `tenacity` | `app/llm.py`, `app/tool/web_search.py` | Alto |
| `loguru` | `app/logger.py` (usado em todo o projeto) | Crítico |
| `tiktoken` | `app/llm.py` | Alto |
| `httpx` | `app/integrations/daytona_http.py`, `app/tool/image_generator.py`, `archive/openmanus/a2a_protocol_unvalidated/a2a/app/main.py`, `scripts/inspect_daytona_file_upload.py`, `scripts/inspect_daytona_toolbox_routes.py` | Alto |
| `mcp` | `app/mcp/server.py`, `app/tool/mcp.py` | Alto |
| `docker` | `app/sandbox/core/manager.py`, `app/sandbox/core/sandbox.py`, `app/sandbox/core/terminal.py`, `tests/sandbox/test_docker_terminal.py`, `tests/sandbox/test_sandbox.py` | Médio |
| `boto3` | `app/bedrock.py` | Baixo |
| `browser-use` | `app/tool/browser_use_tool.py` | Médio |
| `crawl4ai` | `app/tool/crawl4ai.py` (lazy) | Baixo |
| `requests` | `app/tool/web_search.py`, `app/tool/search/bing_search.py` | Médio |
| `beautifulsoup4` | `app/tool/web_search.py`, `app/tool/search/bing_search.py` | Médio |
| `googlesearch-python` | `app/tool/search/google_search.py` | Baixo |
| `baidusearch` | `app/tool/search/baidu_search.py` | Baixo |
| `duckduckgo_search` | `app/tool/search/duckduckgo_search.py` | Baixo |
| `pillow` | `app/tool/sandbox/sb_browser_tool.py`, `app/tool/sandbox/sb_vision_tool.py` | **Arquivos não usados** |
| `uvicorn` | `archive/openmanus/a2a_protocol_unvalidated/a2a/app/main.py` (lazy) | Baixo (arquivado) |
| `fastapi` | Transitiva (via A2A, arquivado) | Baixo (arquivado) |
| `playwright` | Transitiva (via browser-use) | Médio |
| `tomli` | Backport (via `import tomllib` em `app/config.py`) | Baixo |
| `pytest` | 4 testes em `tests/sandbox/` | Teste |
| `pytest-asyncio` | 4 testes em `tests/sandbox/` | Teste |
| `setuptools` | `setup.py` | Build |
| `pyyaml` | **Nenhum** | Requer investigação |
| `numpy` | **Nenhum** | Requer investigação |
| `datasets` | **Nenhum** | Requer investigação |
| `html2text` | **Nenhum** | Requer investigação |
| `gymnasium` | **Nenhum** | Requer investigação |
| `browsergym` | **Nenhum** | Requer investigação |
| `unidiff` | **Nenhum** | Requer investigação |
| `aiofiles` | **Nenhum** | Requer investigação |
| `colorama` | **Nenhum** | Requer investigação |
| `huggingface-hub` | **Nenhum** | Requer investigação |

---

## Apêndice B: Árvore de dependências transitivas (parcial)

```
openai
  └── httpx (transitivo)

browser-use
  ├── playwright
  ├── pydantic (já listado)
  └── browsergym (sem import direto confirmado, mas pode ser requerido)

crawl4ai
  ├── playwright
  ├── beautifulsoup4 (já listado)
  ├── httpx (já listado)
  └── aiofiles (sem import direto confirmado, mas pode ser requerido)

mcp
  └── httpx (para SSE)

docker
  └── requests (já listado, para API Docker)
```
