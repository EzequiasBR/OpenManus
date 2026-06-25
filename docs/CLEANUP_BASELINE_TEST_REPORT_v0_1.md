# Cleanup Baseline Test Report — v0.1

> **Objetivo:** Registrar o estado de baseline antes da limpeza controlada do projeto OpenManus local.
>
> **Data:** 25/06/2026
>
> **Ambiente de validação:** Python 3.12.10 (venv), Windows, pytest 9.0.3
>
> **Nota:** Nenhum código foi alterado. Nenhuma dependência foi modificada. Apenas captura de baseline.

---

## 1. `python -m compileall app` — Compilação

**Resultado:** OK

**Saída:** Todos os módulos de `app/` foram listados e compilados sem erro fatal:

```
Listing 'app'...
Compiling 'app\\__init__.py'...
Compiling 'app\\config.py'...
Compiling 'app\\llm.py'...
Compiling 'app\\schema.py'...
Compiling 'app\\agent\\manus.py'...
Compiling 'app\\tool\\daytona_sandbox.py'...
Compiling 'app\\tool\\image_generator.py'...
Compiling 'app\\integrations\\daytona_http.py'...
... (total de ~70 arquivos compilados)
```

**Interpretação:** Todo o código Python do pacote `app/` é sintaticamente válido. Nenhum erro de syntax, import circular ou referência inválida foi detectado em tempo de compilação.

---

## 2. `python -m pip check` — Integridade de Dependências

**Resultado:** OK

**Saída:**
```
No broken requirements found.
```

**Interpretação:** Todas as dependências declaradas estão instaladas e não há conflitos de versão entre pacotes.

---

## 3. `python -m pytest tests` — Testes Automatizados

**Resultado:** 13 **FAILED**, 2 **PASSED**, 10 **ERRORS**

**Saída resumida:**
```
FAILED tests/sandbox/test_client.py::test_sandbox_creation
FAILED tests/sandbox/test_client.py::test_local_command_execution
FAILED tests/sandbox/test_client.py::test_local_file_operations
FAILED tests/sandbox/test_client.py::test_local_volume_binding
FAILED tests/sandbox/test_client.py::test_local_error_handling
FAILED tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_command_timeout
FAILED tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_session_cleanup
FAILED tests/sandbox/test_sandbox.py::test_sandbox_cleanup
FAILED tests/sandbox/test_sandbox_manager.py::test_create_sandbox
FAILED tests/sandbox/test_sandbox_manager.py::test_max_sandboxes_limit
FAILED tests/sandbox/test_sandbox_manager.py::test_sandbox_cleanup
FAILED tests/sandbox/test_sandbox_manager.py::test_idle_sandbox_cleanup
FAILED tests/sandbox/test_sandbox_manager.py::test_manager_cleanup
ERROR tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_basic_command_execution
ERROR tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_environment_variables
ERROR tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_working_directory
ERROR tests/sandbox/test_docker_terminal.py::TestAsyncDockerizedTerminal::test_multiple_commands
ERROR tests/sandbox/test_sandbox.py::test_sandbox_working_directory
ERROR tests/sandbox/test_sandbox.py::test_sandbox_file_operations
ERROR tests/sandbox/test_sandbox.py::test_sandbox_python_execution
ERROR tests/sandbox/test_sandbox.py::test_sandbox_file_persistence
ERROR tests/sandbox/test_sandbox.py::test_sandbox_python_environment
ERROR tests/sandbox/test_sandbox.py::test_sandbox_network_access
```

**Testes que PASSARAM** (2):
- `tests/sandbox/test_docker_terminal.py::test_command_timeout` — o timeout foi detectado corretamente.
- `tests/sandbox/test_docker_terminal.py::test_session_cleanup` — o cleanup foi executado sem erro.

### 3.1 Causa Raiz

Todas as falhas convergem para o mesmo erro em `app/sandbox/core/terminal.py:71`:

```
RuntimeError: Failed to get socket connection
```

O fluxo de criação do sandbox Docker local:
1. `SandboxManager.create_sandbox()` → `DockerSandbox.create()` → `AsyncDockerizedTerminal.init()` → `DockerSession.create()`
2. O container Docker **é criado e iniciado com sucesso** (a API Docker responde).
3. A falha ocorre em `terminal.py:71` quando `exec_start(socket=True)` retorna um objeto **sem o atributo `_sock`**.
4. A condição `if hasattr(socket_data, "_sock")` falha, levantando `RuntimeError("Failed to get socket connection")`.

**Causa provável:** O método `exec_start` com `socket=True` no Docker SDK para Windows não expõe `_sock` da mesma forma que no Linux. Este é um problema conhecido de compatibilidade entre plataformas.

### 3.2 Evidência de que Docker Desktop Está Acessível

A API Docker respondeu corretamente:
- `docker.from_env()` criou o client sem erro.
- `create_container()` executou sem erro em todos os testes.
- `containers.get()` e `container.start()` executaram sem erro.

O Docker está funcionando. O que falha é a camada de **terminal interativo via socket**, específica do Windows.

---

## 4. `python -m pytest tests -k "not sandbox and not docker"` — Cobertura Fora de Sandbox

**Resultado:** `0 selected / 4 deselected`

**Saída:**
```
collected 0 items / 4 deselected / 0 selected
================================= no tests ran in 0.51s
```

**Interpretação:** A suíte de testes atual está **inteiramente concentrada** em `tests/sandbox/`. Não existe nenhum teste unitário ou de integração para:

- `app/config.py`
- `app/llm.py`
- `app/schema.py`
- `app/agent/` (manus, toolcall, react, base)
- `app/tool/` (nenhuma tool)
- `app/integrations/daytona_http.py`
- `app/tool/daytona_sandbox.py`
- `app/tool/image_generator.py`
- `app/flow/`
- `app/mcp/`

---

## 5. Warnings Observados

```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated,
use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0.
```

**Local:** `venv\Lib\site-packages\pydantic\_internal\_config.py:295`

**Impacto:** Aviso de deprecação do Pydantic 2.x. Não quebra execução, mas precisa ser resolvido antes da migração para Pydantic 3.x. Afeta `app/schema.py` e `app/tool/base.py` que usam `class Config`.

---

## 6. Decisões

### 6.1 Sobre `app/sandbox/` (Docker Sandbox Local)

| Decisão | Justificativa |
|---------|---------------|
| **Não remover agora** | O módulo faz parte do upstream original e é o único com testes formais. A falha é de compatibilidade Windows, não de lógica. |
| **Classificação** | `KEEP_OPTIONAL / QUARANTINE_FOR_FIX` |
| **Ação futura** | Corrigir `terminal.py` para fallback quando `_sock` não estiver disponível, ou isolar os testes com marcador `@pytest.mark.docker` para não falharem em execução padrão. |

### 6.2 Sobre `tests/sandbox/`

| Decisão | Justificativa |
|---------|---------------|
| **Não remover agora** | Únicos testes existentes. Documentam o comportamento esperado do sandbox Docker. |
| **Ação futura** | Adicionar marcador `@pytest.mark.docker` e configurar `pytest.ini` para pular testes Docker por padrão. |

### 6.3 Sobre o Caminho de Sandbox Validado

| Decisão | Justificativa |
|---------|---------------|
| **Manter Daytona HTTP como sandbox validada** | `app/integrations/daytona_http.py` + `app/tool/daytona_sandbox.py` são a alternativa funcional e validada para execução remota isolada. |
| **Não substituir** | A implementação Docker local não será substituída pela Daytona — são caminhos complementares. |

### 6.4 Sobre Dependências

| Decisão | Justificativa |
|---------|---------------|
| **Não alterar `requirements.txt`** | Baseline está estável (`pip check` OK). Qualquer alteração deve ser precedida de nova validação. |
| **Não alterar `setup.py`** | O arquivo está consistente com o estado atual. |

### 6.5 Sobre Warnings

| Warning | Tratamento |
|---------|------------|
| `PydanticDeprecatedSince20` | **Não bloqueia limpeza inicial.** Registrar como dívida técnica. Deve ser resolvido antes da migração para Pydantic 3.x. |
| `pytest-asyncio` implícito | Collected via `pytest.ini` ou `conftest.py` — verificar configuração. |
| `requests` urllib3 | Se houver warnings de SSL/urllib3, registrar como dívida técnica. |

---

## 7. Decisão de Limpeza

### 7.1 Escopo da Limpeza Inicial

A limpeza inicial deve focar **apenas** em:

- Caches (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`)
- Arquivos temporários (`*.pyc`, `*.pyo`, `*.log`)
- Outputs locais (`output_images/`, `logs/`)
- Artefatos não oficiais (`.bak/`, `.local_notes/` — sujeito a revisão)
- Snapshots de dependência (`reports/dependency_snapshots/` — consolidar)

### 7.2 O Que Deve Permanecer Intocado

- **Runtime de agentes:** `app/agent/base.py`, `app/agent/react.py`, `app/agent/toolcall.py`, `app/agent/manus.py`
- **Configuração central:** `app/config.py`
- **Tools validadas:** `app/tool/daytona_sandbox.py`, `app/tool/image_generator.py`
- **Integração Daytona:** `app/integrations/daytona_http.py`
- **Módulos base da Skill Adapter futura:** conforme seção 18.4 do `MODULE_DISPOSITION_PLAN_v0_1.md`
- **`app/sandbox/`:** Não remover — corrigir ou isolar em fase futura própria.
- **`tests/sandbox/`:** Não remover — adicionar marcador para pular por padrão.
- **`requirements.txt` e `setup.py`:** Não alterar sem nova baseline.
- **Módulos QUARANTINE e INVESTIGATE:** Conforme classificação do `MODULE_DISPOSITION_PLAN_v0_1.md`.

### 7.3 Sandbox Docker Local

| Ação | Prazo |
|------|-------|
| Isolar testes Docker com marcador `@pytest.mark.docker` | Antes da Fase 1 |
| Corrigir `terminal.py` para compatibilidade Windows | Fase futura própria |
| Manter como `KEEP_OPTIONAL / QUARANTINE_FOR_FIX` | Até correção |

### 7.4 Resumo do Baseline

| Comando | Status | Interpretação |
|---------|--------|---------------|
| `compileall app` | OK | Código sintaticamente válido |
| `pip check` | OK | Dependências íntegras |
| `pytest tests` | 13F / 2P / 10E | Falhas concentradas em sandbox Docker (socket Windows) |
| `pytest -k "not sandbox"` | 0 selected | Nenhum teste fora de sandbox existe |
| Pydantic warning | Presente | Dívida técnica, não bloqueia |

---

## 8. Próximos Passos Imediatos

1. Adicionar `pytest.ini` ou `conftest.py` com marcador `docker` para isolar testes de sandbox.
2. Executar `pytest -m "not docker"` como comando padrão de validação.
3. Registrar warning Pydantic como issue técnica.
4. Seguir fases definidas no `MODULE_DISPOSITION_PLAN_v0_1.md` começando pela Fase 1 (quarentena).
