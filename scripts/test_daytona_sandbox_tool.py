import asyncio

from app.tool.daytona_sandbox import DaytonaSandboxTool


async def main() -> None:
    tool = DaytonaSandboxTool()

    print("TESTE 1 — stdout simples")
    result_1 = await tool.execute(
        action="run_python_code",
        code="""
print("DAYTONA_TOOL_OK")
print(2 + 2)
""",
    )
    print(result_1)

    print("\n" + "-" * 80 + "\n")

    print("TESTE 2 — arquivo result.txt")
    result_2 = await tool.execute(
        action="run_python_code",
        code="""
from pathlib import Path

Path("result.txt").write_text("RESULT_OK", encoding="utf-8")
print("done")
""",
        result_filename="result.txt",
    )
    print(result_2)


if __name__ == "__main__":
    asyncio.run(main())