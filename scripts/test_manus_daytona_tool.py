import asyncio

from app.agent.manus import Manus


PROMPT = """
Você deve usar obrigatoriamente a tool daytona_sandbox.

Tarefa:
Execute código Python em uma sandbox Daytona remota para calcular a soma dos números de 1 até 20.

O código Python deve:
1. imprimir MANUS_DAYTONA_TOOL_OK
2. imprimir o resultado da soma de 1 até 20
3. criar um arquivo result.txt com o texto:
MANUS_DAYTONA_RESULT_OK
sum_1_to_20=210

Depois da execução, responda de forma curta informando:
- se a tool daytona_sandbox foi usada
- o stdout retornado
- o conteúdo do result.txt
"""


async def main() -> None:
    agent = Manus()
    result = await agent.run(PROMPT)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())