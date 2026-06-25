# GraphStore Closed Binary Integration Decision — v0.1

> **Objetivo:** Registrar a decisão técnica de integrar o GraphStore à Manus como dependência externa fechada, usando binário compilado local, sem incluir o código-fonte do GraphStore no repositório OpenManus.
>
> **Status:** Aprovado (rascunho v0.1)
>
> **Data:** 25/06/2026

---

## 1. Decisão Central

- GraphStore será integrado como **binário local fechado**.
- OpenManus **não incorporará o código-fonte** do GraphStore.
- OpenManus conterá **apenas**:
  - Adapter (`app/integrations/graphstore_cli.py`)
  - Tool (`app/tool/graphstore_memory.py`)
  - Config (seção `[graphstore]` em `config.toml`)
  - Setup (`scripts/setup_graphstore_memory.py`)
  - Documentação (`docs/`)

**Justificativa:** GraphStore é um projeto separado e privado do mantenedor. OpenManus é apenas consumidor. A integração inicial não usará Docker, Daytona cloud, submodule nem cópia do código-fonte.

---

## 2. Modelo de Distribuição

```
[GraphStore repo privado]  ──build/publish──>  graphstore-cli(.exe)
                                                      │
                                                      ▼
[Usuário]  ──download/instala──>  graphstore-cli em $PATH ou GRAPHSTORE_CLI_PATH
                                                      │
                                                      ▼
[Manus tool]  ──subprocess──>  graphstore-cli  ──>  banco SQLite local
```

| Componente | Descrição |
|------------|-----------|
| Repositório GraphStore | Privado do mantenedor. Gera release/binário. |
| Binário | `graphstore-cli` (Windows `.exe`, Linux/macOS executável). |
| Descoberta | Var `GRAPHSTORE_CLI_PATH` ou `$PATH`. |
| Comunicação | CLI via subprocess (stdin/stdout JSON). |
| Banco | Criado localmente no PC do usuário. |

**Não faz parte deste modelo:**
- Docker
- Daytona cloud
- Submodule Git
- GraphStore como serviço HTTP
- GraphStore embutido no OpenManus
- Abertura do código-fonte
- Sincronização remota
- Múltiplos bancos por conversa

---

## 3. Política de Banco Único

**Regra fundamental:** 1 instalação/workspace da Manus = 1 banco GraphStore.

| Item | Caminho / Regra |
|------|-----------------|
| Banco real | `{WORKSPACE_ROOT}/.local_data/graphstore` (arquivo SQLite) |
| Estado local | `{WORKSPACE_ROOT}/.local_data/manus_graphstore_state.json` |
| Init | Só pode rodar **se o banco ainda não existir** |
| Guard `CURRENT` | Se `manus_graphstore_state.json` contiver `"session_rel_id"`, o banco é considerado inicializado |
| Criação dinâmica | **Proibida** em uso real |
| Bancos temporários | Permitidos **apenas** em testes explícitos (`tests/` com tempfile ou `:memory:`) |

**Fluxo de init idempotente:**

```
1. Verificar se GRAPHSTORE_CLI_PATH é executável
2. Verificar se banco existe em GRAPHSTORE_DB_PATH
3. Se banco NÃO existe → executar `graphstore-cli init --db-path <path>`
4. Se estado local NÃO existe → executar `graphstore-cli memory-session-start`
5. Persistir session_rel_id em manus_graphstore_state.json
6. Se banco já existe → reutilizar (pular init)
```

---

## 4. Variáveis / Configuração Previstas

### 4.1 Seção TOML (`config.toml`)

```toml
[graphstore]
enabled = false
backend = "local_binary"
cli_path = "env:GRAPHSTORE_CLI_PATH"
db_path = "env:GRAPHSTORE_DB_PATH"
session_id = "manus-default"
```

### 4.2 Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `GRAPHSTORE_ENABLED` | Não | `false` | Liga/desliga o GraphStore |
| `GRAPHSTORE_BACKEND` | Não | `local_binary` | Backend (reservado para futuro) |
| `GRAPHSTORE_CLI_PATH` | Sim (se enabled) | — | Caminho completo para o binário |
| `GRAPHSTORE_DB_PATH` | Não | `{WORKSPACE_ROOT}/.local_data/graphstore` | Onde o banco SQLite será criado |
| `GRAPHSTORE_SESSION_ID` | Não | `manus-default` | Nome da sessão padrão |

### 4.3 Settings Pydantic (em `app/config.py`)

Segue o padrão existente de `DaytonaSettings`:
```python
class GraphStoreSettings(BaseModel):
    enabled: bool = Field(False, description="Enable GraphStore integration")
    backend: str = Field("local_binary", description="Backend type")
    cli_path: Optional[str] = Field(None, description="Path to graphstore-cli binary")
    db_path: Optional[str] = Field(None, description="Path to the GraphStore database")
    session_id: str = Field("manus-default", description="Default session identifier")
```

---

## 5. Fluxo de Bootstrap Idempotente

```
┌─────────────────────────────────────────────┐
│ scripts/setup_graphstore_memory.py          │
├─────────────────────────────────────────────┤
│ 1. Carregar config (AppConfig.graphstore)   │
│ 2. Se não enabled → sair (sem erro)         │
│ 3. Validar que GRAPHSTORE_CLI_PATH existe   │
│    e é executável                            │
│ 4. Resolver GRAPHSTORE_DB_PATH              │
│ 5. Se banco NÃO existe:                     │
│    └─ subprocess(graphstore-cli init ...)   │
│ 6. Se manus_graphstore_state.json           │
│    NÃO existe:                              │
│    └─ subprocess(graphstore-cli             │
│         memory-session-start ...)           │
│    └─ salvar session_rel_id no JSON         │
│ 7. Se ambos existem: nada a fazer (OK)      │
│ 8. Reportar status (ok/erro)                │
└─────────────────────────────────────────────┘
```

**Propriedades:**
- Idempotente: executar N vezes produz o mesmo estado.
- Seguro: só cria banco se ausente.
- Silencioso se já configurado.

---

## 6. Fora do Escopo (v0.1)

| Item | Motivo |
|------|--------|
| Docker | Integração é local/binário. Docker adiciona complexidade sem necessidade imediata. |
| Daytona cloud | Sandbox remota não tem o binário GraphStore. |
| Submodule | GraphStore é fechado. Submodule exigiria acesso ao repo privado. |
| GraphStore como serviço HTTP | Aumenta superfície de ataque e latência. CLI é suficiente. |
| GraphStore embutido no OpenManus | Separação de responsabilidades. |
| Abertura do código-fonte | Decisão do mantenedor, fora do escopo técnico. |
| Sincronização remota | Sem nuvem no momento. |
| Múltiplos bancos por conversa | Viola política de banco único. |
| Interface gráfica | Sem necessidade. CLI + JSON bastam. |

---

## 7. Segurança e Privacidade

| Requisito | Implementação |
|-----------|---------------|
| `.local_data/` não versionado | Adicionar `**/.local_data/` ao `.gitignore` |
| Banco real não sobe para Git | `.local_data/` cobre todos os bancos |
| Sem secrets no banco | Não salvar chaves API, tokens ou segredos no GraphStore |
| Reset apenas com confirmação | `scripts/setup_graphstore_memory.py` deve exigir confirmação (`input("Tem certeza? (s/N): ")`) antes de apagar banco |
| Permissão de arquivo | Banco criado com permissões padrão do sistema (usuário dono) |
| Path injection | Validar que `cli_path` e `db_path` são caminhos seguros (sem caracteres especiais) |

---

## 8. Próximos Passos

### 8.1 Imediatos (pré-código)

- [ ] Validar build/publish do binário GraphStore (`graphstore-cli --version`)
- [ ] Validar comandos CLI planejados: `health-check`, `init`, `memory-session-start`, `memory-add`, `memory-get`, `memory-list-session`
- [ ] Validar formato de retorno JSON do binário
- [ ] Validar comportamento quando banco já existe (deve retornar erro controlado, não corromper)

### 8.2 Implementação (próxima sprint)

- [ ] Criar adapter: `app/integrations/graphstore_cli.py`
  - Classe `GraphStoreCLI` que executa subprocess com JSON stdin/stdout
  - Métodos: `health_check()`, `init(db_path)`, `memory_session_start()`, `memory_add()`, `memory_get()`, `memory_list_session()`
  - Exceção customizada `GraphStoreError`
  - Segue padrão de `DaytonaHTTPClient` / `DaytonaHTTPError`
- [ ] Criar tool: `app/tool/graphstore_memory.py`
  - `GraphStoreMemoryTool(BaseTool)` com `name="graphstore_memory"`
  - Ações: `add`, `get`, `list_sessions`, `health`
  - Segue padrão de `DaytonaSandboxTool`
  - Exportar em `app/tool/__init__.py`
- [ ] Criar script: `scripts/setup_graphstore_memory.py`
  - Bootstrap idempotente conforme seção 5
  - Segue padrão dos scripts Daytona em `scripts/`
- [ ] Atualizar `app/config.py`:
  - Adicionar `GraphStoreSettings`
  - Adicionar `graphstore_config` em `AppConfig`
  - Carregar seção `[graphstore]` do TOML
- [ ] Atualizar `config/config.example.toml`:
  - Adicionar seção `[graphstore]` comentada
- [ ] Atualizar `.gitignore`:
  - Adicionar `.local_data/`

### 8.3 Testes (validação)

- [ ] Script de teste local manual (bash/PowerShell): chamar `graphstore-cli health-check`
- [ ] Testar init com banco ausente → cria banco
- [ ] Testar init com banco existente → não recria
- [ ] Testar `memory-add` e `memory-get` no banco criado
- [ ] Testar `memory-list-session` após `memory-session-start`
- [ ] Testar erro quando binário não encontrado
- [ ] Testar erro quando `GRAPHSTORE_CLI_PATH` não é executável

---

## Apêndice A — Exemplo de Contrato CLI (JSON)

### health-check

```
> graphstore-cli health-check
← {"status":"ok","version":"0.1.0","db_available":false}
```

### init

```
> graphstore-cli init --db-path /path/to/graphstore
← {"status":"created","db_path":"/path/to/graphstore"}
```

### init (banco já existe)

```
> graphstore-cli init --db-path /path/to/graphstore
← {"status":"error","code":"DB_ALREADY_EXISTS","message":"...", "db_path":"..."}
```

### memory-session-start

```
> graphstore-cli memory-session-start --session-id manus-default --db-path ...
← {"status":"ok","session_rel_id":"abc123"}
```

### memory-add

```
> graphstore-cli memory-add --session-rel-id abc123 --content "..." --db-path ...
← {"status":"ok","memory_id":"mem_001"}
```

### memory-get

```
> graphstore-cli memory-get --memory-id mem_001 --db-path ...
← {"status":"ok","memory":{"id":"mem_001","content":"...","session":"abc123","created_at":"..."}}
```

### memory-list-session

```
> graphstore-cli memory-list-session --session-rel-id abc123 --db-path ...
← {"status":"ok","memories":[{"id":"mem_001","content":"...",...}]}
```

> **Nota:** O contrato JSON acima é **proposto** e deve ser validado contra o binário real do GraphStore antes da implementação.

---

## Apêndice B — Mapa de Padrões Reutilizáveis (ref. `docs/GRAPHSTORE_EXISTING_PATTERN_AUDIT.md`)

| O quê | Padrão Existente | Como Reutilizar |
|-------|------------------|-----------------|
| Singleton de config | `Config` em `app/config.py:212–230` | Usar `GraphStoreSettings` como Pydantic model |
| Tool base | `BaseTool` em `app/tool/base.py:78–173` | `GraphStoreMemoryTool(BaseTool)` |
| Integração externa | `DaytonaHTTPClient` em `app/integrations/daytona_http.py` | `GraphStoreCLI` em `app/integrations/graphstore_cli.py` |
| Erro controlado | `DaytonaHTTPError(RuntimeError)` | `GraphStoreError(RuntimeError)` |
| Bootstrap script | `scripts/create_daytona_sandbox.py` | `scripts/setup_graphstore_memory.py` |
| Path de dados | `WORKSPACE_ROOT` em `app/config.py:31` | `{WORKSPACE_ROOT}/.local_data/` |
| Git ignore | `data/`, `logs/`, `workspace/` em `.gitignore` | Adicionar `.local_data/` |
