# GraphStore Existing Pattern Audit

> **Objetivo:** Verificar se o OpenManus atual já possui algum padrão reutilizável para integrar o GraphStore como recurso local persistente singleton.
>
> **Regra:** Nenhum código foi alterado. Apenas auditoria do projeto existente.
>
> **Data:** 25/06/2026

---

## Índice

1. [Padrões de Configuração](#1-padrões-de-configuração)
2. [Padrões de Tools](#2-padrões-de-tools)
3. [Padrões de Integrações](#3-padrões-de-integrações)
4. [Padrões de Estado Local](#4-padrões-de-estado-local)
5. [Padrões de Bootstrap](#5-padrões-de-bootstrap)
6. [Padrões de Exclusão do Git](#6-padrões-de-exclusão-do-git)
7. [Compatibilidade com Política GraphStore](#7-compatibilidade-com-política-graphstore)
8. [Conclusões e Recomendações](#8-conclusões-e-recomendações)

---

## 1. Padrões de Configuração

### 1.1 `app/config.py` — Singleton de Configuração

| Linha(s) | Padrão | Classificação |
|----------|--------|---------------|
| 212–230 | `Config` singleton com `_instance`, `_lock` (threading.Lock), `_initialized` | **Reutilizável diretamente** |
| 217–222 | `__new__` com double-checked locking | **Reutilizável diretamente** |
| 224–230 | `__init__` com guard `_initialized` para execução única | **Reutilizável diretamente** |
| 232–247 | `_get_config_path()` — procura em múltiplos locais com fallback | **Reutilizável com adaptação** |
| 11–22 | `resolve_env()` — resolve `env:VAR` em valores TOML | **Reutilizável diretamente** |
| 25–31 | `get_project_root()` + constantes `PROJECT_ROOT`, `WORKSPACE_ROOT` | **Reutilizável diretamente** |
| 34–209 | Settings aninhados via Pydantic `BaseModel` | **Reutilizável com adaptação** |
| 399 | `config = Config()` — instância module-level única | **Reutilizável diretamente** |

**Evidência (app/config.py:212–230):**
```python
class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True
```

### 1.2 Arquivos TOML

| Arquivo | Tamanho | Classificação |
|---------|---------|---------------|
| `config/config.toml` | 26 linhas | **Não aplicável** (formato existente, seção GraphStore seria adicionada) |
| `config/config.example.toml` | 113 linhas | **Não aplicável** (modelo de documentação de seções) |
| `config/config.example-daytona.toml` | 114 linhas | **Reutilizável com adaptação** (exemplo de seção externa completa) |
| Demais `.example-model-*.toml` | ~17 linhas | **Não aplicável** |

**Padrões observados:**
- Um `config.toml` ativo (não versionado) + `config.example.toml` (versionado) com seções comentadas.
- Exemplos de provedores externos (Daytona) em arquivos `.example-*.toml` separados.
- Seções são namespaced: `[llm]`, `[browser]`, `[search]`, `[sandbox]`, `[mcp]`, `[runflow]`, `[daytona]`.

### 1.3 Uso de Env Vars

| Padrão | Localização | Classificação |
|--------|-------------|---------------|
| `env:VAR_NAME` em valores TOML | `config.toml:5`, `config.toml:13`, `config.toml:25` | **Reutilizável diretamente** |
| `os.getenv("VAR")` em código | `daytona_http.py:26`, `daytona_http.py:29`, `image_generator.py:48` | **Reutilizável diretamente** |
| Sem `.env.example` | **Ausente** | **Ausente** |

### 1.4 Arquivos JSON de Configuração

| Arquivo | Classificação |
|---------|---------------|
| `config/mcp.example.json` | **Reutilizável com adaptação** (JSON externo carregado via `MCPSettings.load_server_config()`) |

**Evidência (app/config.py:163–186):**
```python
@classmethod
def load_server_config(cls) -> Dict[str, MCPServerConfig]:
    config_path = PROJECT_ROOT / "config" / "mcp.json"
    ...
```

---

## 2. Padrões de Tools

### 2.1 Estrutura Base

| Componente | Localização | Classificação |
|------------|-------------|---------------|
| `BaseTool` (ABC + BaseModel) | `app/tool/base.py:78–173` | **Reutilizável diretamente** |
| `ToolResult` (output, error, base64_image, system) | `app/tool/base.py:38–75` | **Reutilizável diretamente** |
| `success_response(data)` | `app/tool/base.py:147–161` | **Reutilizável diretamente** |
| `fail_response(msg)` | `app/tool/base.py:163–173` | **Reutilizável diretamente** |
| `to_param()` (OpenAI function calling) | `app/tool/base.py:124–137` | **Não aplicável** |
| `ToolFailure` (subclasse de ToolResult) | `app/tool/base.py:180–181` | **Reutilizável diretamente** |

**Evidência (app/tool/base.py:78–122):**
```python
class BaseTool(ABC, BaseModel):
    name: str
    description: str
    parameters: Optional[dict] = None

    async def __call__(self, **kwargs) -> Any:
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        ...
```

### 2.2 Como Tools Recebem Parâmetros

| Padrão | Exemplo | Classificação |
|--------|---------|---------------|
| `parameters: dict` com schema JSON | `image_generator.py:21–34` | **Reutilizável diretamente** |
| kwargs tipados no `execute()` | `daytona_sandbox.py:63–70` | **Reutilizável diretamente** |
| Validação manual de parâmetros | `daytona_sandbox.py:71–93` | **Reutilizável com adaptação** |

### 2.3 Como Tools Chamam Serviços Externos

| Padrão | Exemplo | Classificação |
|--------|---------|---------------|
| `httpx.AsyncClient` para HTTP assíncrono | `image_generator.py:53–54` | **Reutilizável diretamente** |
| Cliente HTTP síncrono module-level | `daytona_sandbox.py:95` cria `DaytonaHTTPClient()` | **Reutilizável com adaptação** |
| Injeção de dependência via import direto | `daytona_sandbox.py:6` importa `DaytonaHTTPClient` | **Reutilizável com adaptação** |

### 2.4 Como Retornam Erro Controlado

| Padrão | Exemplo | Classificação |
|--------|---------|---------------|
| String de erro (`return "Erro: ..."`) | `image_generator.py:38, 59–63, 65–70, 94–99` | **Reutilizável diretamente** |
| `ToolResult(error=msg)` | `base.py:173` | **Reutilizável diretamente** |
| JSON de erro com tipo e cleanup | `daytona_sandbox.py:193–232` | **Reutilizável com adaptação** |
| Exceção customizada `DaytonaHTTPError` | `daytona_http.py:7–8` | **Reutilizável com adaptação** |

---

## 3. Padrões de Integrações

### 3.1 `app/integrations/` — Estrutura Geral

| Arquivo | Classificação |
|---------|---------------|
| `app/integrations/__init__.py` (vazio) | **Reutilizável diretamente** |
| `app/integrations/daytona_http.py` | **Reutilizável com adaptação** |

### 3.2 Daytona HTTP — Padrões Relevantes

| Padrão | Linha(s) | Classificação |
|--------|----------|---------------|
| Wrapper HTTP sem SDK oficial | `daytona_http.py:11–490` | **Reutilizável com adaptação** |
| Exceção customizada `DaytonaHTTPError(RuntimeError)` | `daytona_http.py:7–8` | **Reutilizável diretamente** |
| Construtor com fallback para `os.getenv()` | `daytona_http.py:19–32` | **Reutilizável com adaptação** |
| `httpx.Client(timeout=...)` síncrono | `daytona_http.py:55` | **Reutilizável com adaptação** |
| Métodos named-width (create_sandbox, execute_command, etc.) | `daytona_http.py:117–490` | **Reutilizável com adaptação** |
| `_request()` centralizado com tratamento de erro | `daytona_http.py:45–82` | **Reutilizável diretamente** |

### 3.3 Pollinations / Image Generator — Padrões Relevantes

| Padrão | Linha(s) | Classificação |
|--------|----------|---------------|
| Tool que chama API REST externa | `image_generator.py:36–99` | **Reutilizável com adaptação** |
| `httpx.AsyncClient` com timeout 120s | `image_generator.py:53` | **Reutilizável diretamente** |
| Salva resultado local em `output_images/` | `image_generator.py:72–82` | **Reutilizável com adaptação** |
| UUID para nome único de arquivo | `image_generator.py:81` | **Não aplicável** |

### 3.4 Ausências Notáveis

- **Não há** um padrão de integração para banco de dados / storage local.
- **Não há** classe abstrata de integração (`BaseIntegration` ou similar).
- **Não há** lazy loading ou singleton de clientes externos (DaytonaHTTPClient é instanciado sob demanda).

---

## 4. Padrões de Estado Local

### 4.1 Diretórios de Dados Persistentes

| Diretório | Uso | Classificação |
|-----------|-----|---------------|
| `logs/` | Logs rotacionados por data (`logger.py:25`) | **Reutilizável com adaptação** |
| `workspace/` | WORKSPACE_ROOT definido em `config.py:31` | **Reutilizável diretamente** |
| `output_images/` | Imagens geradas localmente (`image_generator.py:72`) | **Reutilizável com adaptação** |
| `data/` | Excluído no `.gitignore` mas sem uso atual | **Ausente** (vazio) |
| `reports/` | Diretório presente, sem padrão definido | **Não aplicável** |

### 4.2 Cache / Storage Persistente

| Padrão | Localização | Classificação |
|--------|-------------|---------------|
| **Nenhum** banco SQLite, JSON persistente ou cache estruturado | Projeto todo | **Ausente** |
| `app/schema.py` contém `Memory` (histórico de mensagens em RAM) | `app/schema.py` | **Não aplicável** (volátil, sem persistência) |
| Nenhum `state.py` ou `storage.py` | **Ausente** | **Ausente** |

### 4.3 Mecanismos de Singleton Existentes

| Singleton | Localização | Classificação |
|-----------|-------------|---------------|
| `Config` (thread-safe, double-checked locking) | `app/config.py:212–397` | **Reutilizável diretamente** |
| `logger` (module-level, loguru) | `app/logger.py:29` | **Reutilizável com adaptação** |

---

## 5. Padrões de Bootstrap

### 5.1 `scripts/` Directory

| Arquivo | Classificação |
|---------|---------------|
| `scripts/create_daytona_sandbox.py` | **Reutilizável com adaptação** (confirmação do usuário antes de criar recurso) |
| Demais 10 scripts Daytona | **Não aplicável** (testes de integração) |

**Padrões observados:**
- Scripts em `scripts/` importam `app.integrations.daytona_http` diretamente.
- Usam `if __name__ == "__main__":` como entrypoint.
- Incluem confirmação (`input("Criar sandbox? (s/N): ")`) antes de ações destrutivas.

### 5.2 Init / Health Check

| Padrão | Classificação |
|--------|---------------|
| Init do `Config` singleton é lazy (primeiro acesso) | **Reutilizável diretamente** |
| Nenhum health check ou validação de bootstrap no startup | **Ausente** |
| Nenhum script `setup_db` ou `init_graph` | **Ausente** |

### 5.3 `main.py` Entrypoint

```python
# main.py:36 — entry point with argparse
```

Clássico e simples. Sem init de infraestrutura.

---

## 6. Padrões de Exclusão do Git

### 6.1 `.gitignore` — Itens Relevantes

| Padrão | Linha(s) | Classificação |
|--------|----------|---------------|
| `logs/` | `.gitignore:3` | **Reutilizável diretamente** |
| `data/` | `.gitignore:6` | **Reutilizável diretamente** (já excluído) |
| `workspace/` | `.gitignore:9` | **Reutilizável diretamente** (já excluído) |
| `config.toml` | `.gitignore:204,212,217` | **Reutilizável diretamente** |
| `output_images/` | `.gitignore:205,209,213` | **Reutilizável com adaptação** |
| `.bak/` | `.gitignore:206,214` | **Não aplicável** |
| `.local_notes/` | **Não está no .gitignore** | **Ausente** (pasta existe no root e é versionada) |

### 6.2 `config/.gitignore`

```
config.toml
```

Já protege o arquivo de config local.

---

## 7. Compatibilidade com Política GraphStore

### 7.1 Requisitos GraphStore vs. Realidade Atual

| Requisito | Situação Atual | Classificação |
|-----------|----------------|---------------|
| **Banco único por instalação/workspace** | Nenhum banco existe. `WORKSPACE_ROOT` é `PROJECT_ROOT / "workspace"` — candidato natural. Banco será `{WORKSPACE_ROOT}/.local_data/graphstore`. | **Ausente** — workspace existe como conceito |
| **GRAPHSTORE_DB_PATH fixo** | Sem definição. Padrão será `{WORKSPACE_ROOT}/.local_data/graphstore`. Painel `config.py` usaria resolução de path similar a `resolve_env()`. | **Ausente** |
| **Init apenas se banco não existir** | Nenhum init idempotente de storage. Padrão `Config.__init__` com `_initialized` é análogo. | **Reutilizável com adaptação** |
| **Estado em `.local_data/manus_graphstore_state.json`** | Nenhum estado JSON persistente. `image_generator.py` salva arquivos, mas sem metadados. | **Ausente** |
| **Nunca criar bancos dinâmicos em uso real** | Sem política de criação de recursos. Padrão Daytona cria sandbox efêmera por chamada. | **Não aplicável** |

### 7.2 Análise de Risco

| Risco | Descrição |
|-------|-----------|
| **R1 — Singleton concorrente** | `Config` é thread-safe, mas se GraphStore for usado em múltiplos agents concorrentes, pode haver race condition no banco. |
| **R2 — Path fixo vs. portabilidade** | `PROJECT_ROOT` é `Path(__file__).resolve().parent.parent`. Em instalação pip, isso pode não ser gravável. |
| **R3 — Migração de schema** | Sem padrão atual de migration. GraphStore exigirá versionamento de schema. |
| **R4 — Limpeza de dados** | Sem script de reset/cleanup. `.local_data/` precisará de entrada no `.gitignore` e política de exclusão. |
| **R5 — Binário ausente ou inválido** | Se `GRAPHSTORE_CLI_PATH` não existir ou não for executável, a tool deve falhar com erro claro. |
| **R6 — Versão incompatível do binário** | O CLI do GraphStore pode evoluir. O adapter precisa validar versão mínima no `health-check`. |
| **R7 — Parsing de stdout JSON** | A comunicação via subprocess depende de JSON bem formatado na stdout. Erros de parsing precisam de tratamento explícito. |

---

## 8. Conclusões e Recomendações

### 8.1 Melhor Local para GraphStore Client

```
app/integrations/graphstore_cli.py
```

**Justificativa:** Segue o padrão `app/integrations/daytona_http.py` — wrapper para execução do binário fechado via subprocess. O sufixo `_cli` deixa explícito que a integração é via CLI, não via HTTP ou biblioteca Python.

### 8.2 Melhor Local para GraphStore Tool

```
app/tool/graphstore_memory.py
```

**Justificativa:** Segue o padrão `DaytonaSandboxTool` — tool que instancia e usa o client da integração. O nome `graphstore_memory` reflete o domínio (memória persistente) e diferencia de futuras tools que possam usar outras capacidades do GraphStore.

### 8.3 Melhor Local para Script de Bootstrap

```
scripts/setup_graphstore_memory.py
```

**Justificativa:** Segue o padrão dos scripts Daytona em `scripts/`. Deve criar o banco apenas se não existir (idempotente). O prefixo `setup` indica bootstrap único, não execução repetida.

### 8.4 Melhor Nome para Config/Env Vars

| Contexto | Sugestão |
|----------|----------|
| Seção TOML | `[graphstore]` |
| Env var (caminho do binário) | `GRAPHSTORE_CLI_PATH` |
| Env var (caminho do banco) | `GRAPHSTORE_DB_PATH` |
| Env var (backend) | `GRAPHSTORE_BACKEND=local_binary` |
| Env var (enabled) | `GRAPHSTORE_ENABLED` |
| Chave TOML | `enabled`, `backend`, `cli_path`, `db_path`, `session_id` |
| Atributo em AppConfig | `graphstore_config: Optional[GraphStoreSettings]` |

### 8.5 Já Existe Padrão para Singleton Persistente?

**Sim, parcialmente.** O `Config` (`app/config.py:212–230`) é o único padrão de singleton thread-safe do projeto:

```python
class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Porém:** Não existe singleton para recurso persisted state (banco, cache, storage). O `Config` é singleton de **configuração**, não de **estado**. Um `GraphStore` singleton precisará de padrão análogo, mas com lifecycle de conexão (open/close).

### 8.6 Riscos Antes da Implementação

| # | Risco | Severidade | Mitigação |
|---|-------|------------|-----------|
| 1 | `PROJECT_ROOT` pode não ser gravável em instalação pip | Alta | Usar `WORKSPACE_ROOT/.local_data/` como base, com fallback para `~/.openmanus/` |
| 2 | Falta de lock para banco em cenários multi-agent | Média | Usar `threading.Lock` (padrão `Config`) + mutex do binário GraphStore |
| 3 | Schema sem migration | Média | Incluir `schema_version` no binário GraphStore desde a primeira versão |
| 4 | Binário GraphStore ausente ou `GRAPHSTORE_CLI_PATH` inválido | Alta | Tool deve validar existência e permissão de execução no bootstrap |
| 5 | Versão do binário incompatível com o adapter | Média | `health-check` deve retornar versão; adapter valida >= versão mínima |
| 6 | Parsing de stdout JSON do subprocess pode falhar | Média | Tratar `json.JSONDecodeError` com mensagem clara; incluir raw stdout no log de debug |
| 7 | `.gitignore` precisa de entrada para `.local_data/` | Baixa | Adicionar `.local_data/` |
| 8 | Nenhum test coverage para persistência | Média | Incluir tests em `tests/` com banco temporário (subprocess + tempfile) |

> **Nota:** Nenhuma dependência Python nova é esperada no MVP. A comunicação é via subprocess + JSON, sem `pip install graphstore` ou SQLite library Python adicional.

---

## Resumo da Classificação

| Categoria | Reutilizável Diretamente | Reutilizável com Adaptação | Não Aplicável | Ausente |
|-----------|--------------------------|----------------------------|---------------|---------|
| Config | Singleton Config, resolve_env, PROJECT_ROOT | Settings Pydantic, fallback de path | TOML sections | `.env.example` |
| Tools | BaseTool, ToolResult, success/fail_response | Chamada de integração externa | to_param() | Tool de storage |
| Integrações | DaytonaHTTPError, _request() centralizado | DaytonaHTTPClient, ImageGenerator | — | BaseIntegration, lazy singleton |
| Estado Local | — | logs/, workspace/, output_images/ | Memory em RAM | state.py, storage.py, banco |
| Bootstrap | Init lazy do Config | Scripts Daytona com confirmação | — | setup_db, health check |
| .gitignore | data/, workspace/, logs/ | output_images/ | .bak/ | *.db, *.sqlite |
| GraphStore Policy | WORKSPACE_ROOT como path base; padrão singleton Config | Init idempotente (padrão Config); CLI via subprocess | Criação dinâmica | DB_PATH fixo, state JSON, schema, binário CLI |

> **Veredito:** O OpenManus tem padrões maduros para **singleton de configuração** e **tools com chamadas externas**, mas **não possui nenhum padrão para estado persistente local**. A implementação do GraphStore (como binário fechado via CLI) precisará criar novos padrões — adapter de subprocess, validação de binário externo, parsing de stdout JSON, bootstrap idempotente com `GRAPHSTORE_CLI_PATH` — inspirados nos existentes (DaytonaHTTPClient, Config singleton), mas não reutilizáveis diretamente sem adaptação significativa.
