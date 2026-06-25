# PROJECT_STATUS

## 1. Estado atual do projeto

Este projeto é uma adaptação local do OpenManus com integrações externas controladas para:

* uso de LLM via Groq;
* geração de imagens via Pollinations;
* execução remota isolada via Daytona HTTP API;
* uso de tools registradas diretamente no Manus.

O foco atual é manter o OpenManus funcional em ambiente local, evitando dependências pesadas ou instáveis, especialmente o SDK Daytona.

---

## 2. Ambiente validado

* Sistema: Windows / PowerShell
* Ambiente Python: `venv` local do projeto
* Provedor LLM: Groq
* Gerador de imagem: Pollinations
* Sandbox remota: Daytona via HTTP API direta
* SDK Daytona: não utilizado
* Estratégia de chaves: variáveis de ambiente

Variáveis de ambiente usadas:

```text
GROQ_API_KEY
POLLINATIONS_API_KEY
DAYTONA_API_KEY
```

---

## 3. Integrações funcionais

### 3.1 Groq

Status: funcional.

Configuração esperada em `config/config.toml`:

```toml
[llm]
model = "llama-3.3-70b-versatile"
base_url = "https://api.groq.com/openai/v1"
api_key = "env:GROQ_API_KEY"
max_tokens = 4096
temperature = 0.1

[llm.vision]
model = "llama-3.3-70b-versatile"
base_url = "https://api.groq.com/openai/v1"
api_key = "env:GROQ_API_KEY"
max_tokens = 4096
temperature = 0.1
```

Observações:

* `config.toml` não deve ser commitado.
* A chave deve ser lida por `env:GROQ_API_KEY`.
* A configuração local validada usa `config/config.toml`.

---

### 3.2 Pollinations

Status: funcional.

Tool registrada:

```text
generate_image
```

Arquivo principal:

```text
app/tool/image_generator.py
```

Função validada:

* gerar imagem via Pollinations;
* salvar resultado em `output_images/`;
* disponibilizar a tool no `ToolCollection` do Manus.

Variável de ambiente usada:

```text
POLLINATIONS_API_KEY
```

---

### 3.3 Daytona HTTP API

Status: funcional.

Camada principal:

```text
app/integrations/daytona_http.py
```

Variável de ambiente usada:

```text
DAYTONA_API_KEY
```

O SDK Daytona foi descartado para evitar conflitos de dependência e problemas de build no ambiente local.

Fluxos Daytona já validados:

* validação da API key;
* listagem de sandboxes;
* criação de sandbox;
* deleção de sandbox;
* execução de comando remoto;
* criação de pasta remota;
* upload de arquivo;
* download de arquivo;
* leitura de metadados de arquivo;
* remoção de pasta remota;
* execução de script Python remoto;
* retorno de stdout;
* retorno de arquivo `result.txt`;
* uso da Daytona via tool do Manus.

---

## 4. Tools registradas no Manus

Tools esperadas no `ToolCollection`:

```text
python_execute
browser_use
str_replace_editor
ask_human
generate_image
terminate
daytona_sandbox
```

Teste usado para conferir:

```powershell
python -c "from app.agent.manus import Manus; agent = Manus(); print([t.name for t in agent.available_tools.tools])"
```

---

## 5. DaytonaSandboxTool

Status: aprovada na versão v0.2.1.

Arquivo principal:

```text
app/tool/daytona_sandbox.py
```

Nome da tool:

```text
daytona_sandbox
```

Ação aprovada:

```text
run_python_code
```

Fluxo da tool:

```text
Manus
→ daytona_sandbox
→ DaytonaHTTPClient
→ cria sandbox temporária
→ cria diretório remoto
→ envia task.py
→ executa python3 task.py
→ captura stdout
→ tenta baixar result.txt
→ remove diretório remoto
→ solicita deleção da sandbox
```

Resposta limpa esperada:

```json
{
  "ok": true,
  "exitCode": 0,
  "stdout": "texto retornado",
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

---

## 6. Testes aprovados

### 6.1 Daytona HTTP básico

```text
scripts/test_daytona_http.py
```

Valida:

* API key;
* conexão com Daytona;
* listagem de sandboxes.

---

### 6.2 Daytona command execution

```text
scripts/test_daytona_toolbox_execute.py
```

Valida:

* execução de comandos remotos;
* `whoami`;
* `pwd`;
* versão do Python remoto;
* uso de `SHELL=/bin/bash`.

---

### 6.3 Daytona File API

```text
scripts/test_daytona_file_api.py
```

Valida:

* criação de pasta;
* upload multipart;
* metadados de arquivo;
* download;
* validação via comando remoto;
* remoção de pasta;
* deleção da sandbox.

---

### 6.4 Daytona code execution flow

```text
scripts/test_daytona_code_execution_flow.py
```

Valida:

* criação de sandbox;
* envio de script Python;
* execução remota;
* geração de `result.txt`;
* download de resultado;
* cleanup;
* deleção da sandbox.

---

### 6.5 DaytonaSandboxTool isolada

```text
scripts/test_daytona_sandbox_tool.py
```

Valida:

* execução simples com stdout;
* execução com `result.txt`;
* modo `debug=true`;
* cleanup remoto;
* solicitação de deleção da sandbox.

---

### 6.6 DaytonaSandboxTool via Manus

```text
scripts/test_manus_daytona_tool.py
```

Valida:

* Manus seleciona `daytona_sandbox`;
* Manus executa código Python remoto;
* stdout contém resultado esperado;
* `result.txt` é baixado;
* cleanup é registrado;
* Manus finaliza com `terminate`.

---

## 7. Regras de estabilidade

Antes de alterar qualquer integração funcional:

1. Rodar teste isolado.
2. Rodar teste via Manus, quando aplicável.
3. Rodar:

```powershell
python -m pip check
```

4. Conferir:

```powershell
git status
```

5. Fazer commit pequeno e claro.
6. Só depois avançar para o próximo marco.

---

## 8. O que não deve ser feito agora

* Não reinstalar o SDK Daytona no `venv` principal.
* Não misturar a integração HTTP validada com a sandbox original do OpenManus.
* Não expor chaves no código.
* Não commitar `config.toml`.
* Não commitar imagens geradas em `output_images/`, salvo decisão explícita.
* Não apagar scripts de diagnóstico antes da etapa planejada de limpeza.
* Não alterar a sandbox original do OpenManus sem uma etapa separada de análise.

---

## 9. Próximos marcos possíveis

Próximos passos candidatos:

```text
1. Criar DAYTONA_SANDBOX_TOOL_CONTRACT_v0_2_1.md
2. Adicionar run_shell_command como ação separada
3. Criar API local para futuro front-end
4. Criar limpeza controlada de scripts experimentais
5. Documentar fluxo Groq/Pollinations/Daytona em README próprio
```

A prioridade imediata é documentar o contrato da `DaytonaSandboxTool` antes de adicionar novas ações.
