# DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1

## 1. Objetivo

A `DaytonaSandboxTool` fornece ao Manus uma ferramenta segura para executar código Python em uma sandbox remota efêmera da Daytona usando HTTP API direta.

A tool não usa o SDK Daytona, não depende da sandbox original do OpenManus e não importa módulos de `app.daytona`, `app.sandbox` ou `app.tool.sandbox`.

Fluxo validado:

```text
Manus
→ daytona_sandbox
→ app.integrations.daytona_http.DaytonaHTTPClient
→ Daytona HTTP API
→ sandbox remota efêmera
→ execução Python
→ retorno de stdout/result.txt
→ cleanup
→ solicitação de deleção da sandbox
```

## 2. Arquivo principal

```text
app/tool/daytona_sandbox.py
```

Dependência interna obrigatória:

```text
app/integrations/daytona_http.py
```

## 3. Nome da tool

```text
daytona_sandbox
```

## 4. Ação suportada na v0.2.1

```text
run_python_code
```

A v0.2.1 não deve executar comandos shell arbitrários. Execução shell direta será uma ação futura separada, se aprovada.

## 5. Parâmetros

```json
{
  "action": "run_python_code",
  "code": "código Python completo",
  "timeout": 30,
  "result_filename": "result.txt",
  "debug": false
}
```

### 5.1 action

Obrigatório.

Valor aceito na v0.2.1:

```text
run_python_code
```

### 5.2 code

Obrigatório.

Código Python completo enviado como `task.py` para a sandbox.

Limite atual:

```text
MAX_CODE_CHARS = 20000
```

### 5.3 timeout

Opcional.

Tempo máximo de execução em segundos.

Valores atuais:

```text
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120
```

Se o timeout for menor que 1, a tool usa `DEFAULT_TIMEOUT`.

Se o timeout for maior que `MAX_TIMEOUT`, a tool limita para `MAX_TIMEOUT`.

### 5.4 result_filename

Opcional.

Nome do arquivo de resultado que a tool tentará baixar após a execução.

Valor padrão:

```text
result.txt
```

### 5.5 debug

Opcional.

Valor padrão:

```text
false
```

Quando `debug=false`, a resposta não deve expor detalhes internos da sandbox.

Quando `debug=true`, a resposta pode incluir:

```json
{
  "debug": {
    "sandbox_id": "...",
    "sandbox_name": "...",
    "remote_script": "...",
    "remote_result": "..."
  }
}
```

`debug=true` deve ser usado apenas para diagnóstico.

## 6. Resposta esperada em sucesso

Formato limpo esperado:

```json
{
  "ok": true,
  "exitCode": 0,
  "stdout": "texto impresso pelo script",
  "stdout_truncated": false,
  "result_file_found": true,
  "cleanup": {
    "remote_dir_deleted": true,
    "sandbox_delete_requested": true
  },
  "result_file_content": "conteúdo do result.txt",
  "result_file_truncated": false
}
```

Se `result.txt` não existir:

```json
{
  "ok": true,
  "exitCode": 0,
  "stdout": "texto impresso pelo script",
  "stdout_truncated": false,
  "result_file_found": false,
  "cleanup": {
    "remote_dir_deleted": true,
    "sandbox_delete_requested": true
  }
}
```

## 7. Limites de retorno

A tool deve limitar saídas grandes para evitar excesso de tokens.

Valores atuais:

```text
MAX_STDOUT_CHARS = 12000
MAX_RESULT_FILE_CHARS = 12000
```

Se `stdout` for truncado:

```json
"stdout_truncated": true
```

Se `result_file_content` for truncado:

```json
"result_file_truncated": true
```

## 8. Cleanup obrigatório

A tool deve sempre tentar:

```text
1. Remover a pasta remota criada para a tarefa.
2. Solicitar deleção da sandbox.
```

A resposta deve registrar:

```json
"cleanup": {
  "remote_dir_deleted": true,
  "sandbox_delete_requested": true
}
```

Mesmo em erro, a tool deve tentar deletar a sandbox antes de retornar.

## 9. Contrato de isolamento

A sandbox criada pela tool é efêmera.

A tool não deve reutilizar sandbox entre chamadas na v0.2.1.

Cada execução deve criar um nome temporário:

```text
openmanus-tool-xxxxxxxx
```

Cada execução deve usar diretório remoto próprio:

```text
/home/daytona/openmanus-tool-xxxxxxxx
```

## 10. Importações proibidas

A tool não deve importar:

```python
from daytona import ...
from app.daytona import ...
from app.sandbox import ...
from app.tool.sandbox import ...
```

A tool deve usar apenas a integração HTTP já validada:

```python
from app.integrations.daytona_http import DaytonaHTTPClient, DaytonaHTTPError
```

## 11. Testes validados

### 11.1 Teste isolado

Arquivo:

```text
scripts/test_daytona_sandbox_tool.py
```

Casos aprovados:

```text
TESTE 1 — stdout simples
TESTE 2 — arquivo result.txt
TESTE 3 — debug true
```

Critérios de aprovação:

```text
ok = true
exitCode = 0
stdout retornado
result.txt baixado quando criado
remote_dir_deleted = true
sandbox_delete_requested = true
debug só aparece quando debug=true
```

### 11.2 Teste via Manus

Arquivo:

```text
scripts/test_manus_daytona_tool.py
```

Critérios de aprovação:

```text
Manus seleciona daytona_sandbox
Tool executa código Python remoto
stdout contém MANUS_DAYTONA_TOOL_OK
stdout contém 210
result_file_content contém MANUS_DAYTONA_RESULT_OK
result_file_content contém sum_1_to_20=210
remote_dir_deleted = true
sandbox_delete_requested = true
Manus finaliza com terminate success
```

## 12. Estado aprovado

A versão `DaytonaSandboxTool v0.2.1` está aprovada quando:

```text
python scripts\test_daytona_sandbox_tool.py
python scripts\test_manus_daytona_tool.py
```

passam com sucesso.

## 13. Próximas ações possíveis

Ações futuras só devem ser adicionadas depois de preservar o contrato da v0.2.1.

Candidatas futuras:

```text
run_shell_command
upload_and_run_project
download_artifact
persistent_session
front-end API route
```

Nenhuma ação futura deve quebrar `run_python_code`.

## 14. Regra de estabilidade

Antes de qualquer alteração futura:

```text
1. Rodar teste isolado.
2. Rodar teste via Manus.
3. Confirmar pip check.
4. Confirmar git status limpo.
5. Só então commitar.
```
