# Image Provider Capability Contracts

Esta pasta guarda contratos arquiteturais e instâncias declarativas de capacidades de
providers de imagem. Cada arquivo aqui descreve **o que um provider suporta**, não como
implementá-lo.

## Estrutura

```
contracts/image_provider_capability/
├── schemas/          JSON Schemas — contratos validáveis
│   └── image_provider_capability_map.schema.json
├── configs/          Capability maps reais de providers
│   └── pollinations_api_v0_1.json
└── examples/         Exemplos didáticos
    └── provider_capability_map_example_v0_1.json
```

## O que estes arquivos NÃO são

- Não são código de adapter.
- Não implementam chamadas de API.
- Não geram imagens.
- Não substituem a `ImageGeneratorTool`.

## O que estes arquivos SÃO

- **Contratos arquiteturais** que permitem trocar ou adicionar providers sem alterar a skill.
- **Declarações de capacidade** que a LLM Formatting Layer consulta para saber o que enviar.
- **Fontes de verdade** para o Provider Adapter validar e montar a requisição.
- **Base para o Fidelity Gate / Loss Report** detectar perda de requisito durante a tradução.

## Regra fundamental

> Provider Capability Map descreve o que um provider suporta. Ele não implementa o provider.

## Fluxo arquitetural

```
Skill Result Canonical
    │
    ▼
Normalized Image Request
    │
    ▼
Provider Capability Map   ←── você está aqui
    │
    ▼
Provider Formatting Policy
    │
    ▼
Provider Request Packet
    │
    ▼
Provider Adapter
    │
    ▼
Image API
    │
    ▼
Normalized Image Result
    │
    ▼
Fidelity Gate
```

A skill nunca enxerga a API. A LLM Formatting Layer nunca enxerga classes de adapter.
O Capability Map é a ponte declarativa entre o que a skill pede e o que o provider entrega.

## Como adicionar um novo provider

1. **Pesquisar** a documentação oficial da API alvo.
2. **Criar** o capability map em `configs/` seguindo o schema.
3. **Validar** o JSON contra o schema (`Draft202012Validator`).
4. **Criar** a formatting policy associada (em documento ou código separado).
5. **Implementar** o adapter específico implementando o contrato de adapter.
6. **Testar offline** com payloads simulados.
7. **Testar runtime controlado** com chamada real (ambiente de teste).
