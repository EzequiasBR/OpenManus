"""
Utilitário de validação modular do OpenManus.

Objetivo: verificar import, instanciação e registro de módulos
sem alterar código de produção e sem chamar APIs externas.
"""
import importlib
import sys
import traceback
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP_EXT_DEP"
CONFIG_DEP = "CONFIG_DEPENDENT"
NOT_IMPORTABLE = "NOT_IMPORTABLE"

results: list[dict] = []


def try_import(mod_path: str) -> tuple[str, str | None]:
    """Tenta importar um módulo. Retorna (status, erro_ou_None)."""
    try:
        importlib.import_module(mod_path)
        return PASS, None
    except Exception as e:
        return FAIL, _short_tb(e)


def try_instantiate(module_path: str, class_name: str, **kwargs) -> tuple[str, str | None]:
    """Tenta instanciar uma classe, passando kwargs opcionais."""
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name, None)
        if cls is None:
            return FAIL, f"Class {class_name} not found in {module_path}"
        _ = cls(**kwargs)
        return PASS, None
    except Exception as e:
        return FAIL, _short_tb(e)


def _short_tb(e: Exception) -> str:
    return f"{type(e).__name__}: {e}".split("\n")[0][:200]


def log(area: str, path: str, imp: str, inst: str, runtime: str, ext_dep: str, evidence: str, classification: str, action: str):
    results.append(dict(
        area=area, path=path, imp=imp, inst=inst, runtime=runtime,
        ext_dep=ext_dep, evidence=evidence, classification=classification,
        action=action,
    ))


def heading(title: str):
    sep = "=" * 60
    print(f"\n{sep}\n{title}\n{sep}")


# ── Config bootstrap (precisa de TOML) ───────────────────────────────

def check_config():
    heading("0. CONFIG BOOTSTRAP")
    from app.config import Config, config
    cfg = Config()
    llm_keys = list(cfg.llm.keys()) if cfg.llm else []
    print(f"  Config singleton: OK, llm keys={llm_keys}")
    log("config", "app.config", PASS, PASS, PASS, "none",
        f"Singleton Config OK, chaves LLM: {llm_keys}",
        "KEEP_CORE", "manter")


# ── Core do agente ───────────────────────────────────────────────────

def check_agent_core():
    heading("1. CORE DO AGENTE")

    modules = [
        "app.schema",
        "app.config",
        "app.exceptions",
        "app.logger",
        "app.tool.base",
        "app.agent.base",
        "app.agent.toolcall",
        "app.agent.manus",
        "app.flow",
        "app.flow.base",
        "app.flow.flow_factory",
        "app.flow.planning",
        "app.prompt",
        "app.llm",
        "app.prompt.manus",
        "app.prompt.toolcall",
        "app.prompt.planning",
    ]

    for mod in modules:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")
        area = "agent_core" if "agent" in mod else "flow" if "flow" in mod else "prompt" if "prompt" in mod else "schema"

        # app.llm importa bedrock e openai — só testamos import
        if mod == "app.llm":
            s_llm, _ = try_import("app.llm")
            log(area, mod, s_llm, SKIP, SKIP, "openai/aws/bedrock",
                f"LLM requer API key e conexão externa",
                "KEEP_CORE", "manter, não testar runtime sem API key")
            continue

        if mod == "app.agent.manus":
            # Manus depende de MCP, BrowserUseTool (browser_use lib), Daytona
            log(area, mod, s, SKIP, SKIP, "browser_use, mcp, daytona",
                "Manus depende de MCP servers, browser_use, DaytonaSandboxTool",
                "KEEP_CORE", "manter, testar apenas com integração completa")
            continue

        inst_status, inst_err = SKIP, "abstract/async class"

        if s == PASS:
            if "schema" in mod or mod == "app.exceptions":
                inst_status = PASS
                inst_err = None
            elif mod == "app.config":
                inst_status = PASS
                inst_err = None

        log(area, mod, s, inst_status, SKIP, "none",
            f"import: {s}" + (f" | err: {err}" if err else ""),
            "KEEP_CORE", "manter")


# ── Tools principais ─────────────────────────────────────────────────

def check_main_tools():
    heading("2. TOOLS PRINCIPAIS")

    tool_modules = [
        ("app.tool.base", ["BaseTool", "ToolResult", "CLIResult", "ToolFailure"]),
        ("app.tool.tool_collection", ["ToolCollection"]),
        ("app.tool.terminate", ["Terminate"]),
        ("app.tool.ask_human", ["AskHuman"]),
        ("app.tool.create_chat_completion", ["CreateChatCompletion"]),
        ("app.tool.planning", ["PlanningTool"]),
    ]

    for mod, classes in tool_modules:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")

        if s == FAIL:
            log("main_tools", mod, s, FAIL, FAIL, "none",
                f"Falha ao importar: {err}",
                "QUARANTINE_FOR_FIX", "revisar dependências")
            continue

        inst_ok = PASS
        inst_errors = []
        for cls_name in classes:
            if cls_name in ("BaseTool", "ToolCollection"):
                continue  # abstract or requires args
            i_s, i_e = try_instantiate(mod, cls_name)
            if i_s == FAIL:
                inst_ok = FAIL
                inst_errors.append(f"{cls_name}: {i_e}")

        log("main_tools", mod, s, inst_ok, PASS, "none",
            f"Classes: {classes}" + (f" | inst err: {inst_errors}" if inst_errors else ""),
            "KEEP_CORE", "manter")


# ── Tools validadas ──────────────────────────────────────────────────

def check_validated_tools():
    heading("3. TOOLS VALIDADAS")

    checks = [
        ("app.integrations.daytona_http", ["DaytonaHTTPClient", "DaytonaHTTPError"],
         "httpx", "KEEP_VALIDATED_TOOL"),
        ("app.tool.daytona_sandbox", ["DaytonaSandboxTool"],
         "daytona_http, httpx", "KEEP_VALIDATED_TOOL"),
        ("app.tool.image_generator", ["ImageGeneratorTool"],
         "httpx (Pollinations API externa)", "KEEP_VALIDATED_TOOL"),
    ]

    for mod, classes, ext_dep, classification in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")

        inst_ok = SKIP
        if s == PASS:
            for cls_name in classes:
                if cls_name == "DaytonaHTTPClient":
                    # precisa de DAYTONA_API_KEY
                    inst_ok = CONFIG_DEP
                elif cls_name == "DaytonaSandboxTool":
                    inst_ok = CONFIG_DEP
                elif cls_name == "ImageGeneratorTool":
                    i_s, _ = try_instantiate(mod, cls_name)
                    inst_ok = i_s

        log("validated_tools", mod, s, inst_ok, SKIP, ext_dep,
            f"Importa OK, runtime requer {ext_dep}" if s == PASS else f"Falha: {err}",
            classification, "manter")


# ── File operators ──────────────────────────────────────────────────

def check_file_tools():
    heading("4. FILES / EDIÇÃO")

    checks = [
        ("app.tool.file_operators", ["LocalFileOperator", "SandboxFileOperator"]),
        ("app.tool.str_replace_editor", ["StrReplaceEditor"]),
    ]

    for mod, classes in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")

        inst_ok = PASS
        inst_errs = []
        if s == PASS:
            for cls_name in classes:
                if cls_name == "SandboxFileOperator":
                    inst_ok = CONFIG_DEP
                    continue
                i_s, i_e = try_instantiate(mod, cls_name)
                if i_s == FAIL:
                    inst_ok = FAIL
                    inst_errs.append(f"{cls_name}: {i_e}")

        evidence = "Depende de app.sandbox.client (SANDBOX_CLIENT)" if "Sandbox" in str(classes) else ""
        log("file_tools", mod, s, inst_ok, SKIP, "sandbox (Docker)",
            f"Import: {s}" + (f" | inst err: {inst_errs}" if inst_errs else "") + (f" | {evidence}" if evidence else ""),
            "KEEP_CORE", "manter (acoplado ao sandbox local)")


# ── Sandbox Docker ──────────────────────────────────────────────────

def check_sandbox():
    heading("5. SANDBOX DOCKER LOCAL")

    sandbox_modules = [
        "app.sandbox",
        "app.sandbox.client",
        "app.sandbox.core.exceptions",
        "app.sandbox.core.sandbox",
        "app.sandbox.core.terminal",
        "app.sandbox.core.manager",
    ]

    for mod in sandbox_modules:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")
        inst_ok = SKIP
        evidence = f"import: {s}"
        if err:
            evidence += f" | err: {err}"

        log("sandbox_docker", mod, s, inst_ok, "FAIL (socket Win)", "docker SDK",
            evidence,
            "QUARANTINE_FOR_FIX", "não remover; falha de socket no Windows")


# ── Daytona legado ──────────────────────────────────────────────────

def check_legacy_daytona():
    heading("6. DAYTONA LEGADO / SDK")

    checks = [
        ("app.daytona.sandbox", "daytona SDK (daytona pip pkg)"),
        ("app.daytona.tool_base", "daytona SDK"),
        ("app.tool.computer_use_tool", "daytona SDK, aiohttp"),
        ("app.agent.sandbox_agent", "daytona SDK, sandbox tools"),
    ]

    for mod, ext_dep in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")

        inst_ok = SKIP
        evidence = f"import: {s}"
        if err:
            evidence += f" | err: {err}"

        log("legacy_daytona", mod, s, inst_ok, SKIP, ext_dep,
            evidence,
            "LEGACY_DEPENDENCY" if s == FAIL else "INVESTIGATE",
            "investigar dependências ainda ativas")


# ── MCP ─────────────────────────────────────────────────────────────

def check_mcp():
    heading("7. MCP")

    checks = [
        ("app.mcp.server", "FastMCP, browser_use, bash"),
        ("app.tool.mcp", "mcp SDK (ClientSession)"),
        ("app.agent.mcp", "MCPClients"),
    ]

    for mod, ext_dep in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")

        inst_ok = SKIP
        evidence = f"import: {s}"
        if err:
            evidence += f" | err: {err}"

        log("mcp", mod, s, inst_ok, SKIP, ext_dep,
            evidence,
            "KEEP_OPTIONAL", "manter (MCP é arquitetura futura)")


# ── Browser / Search / Crawl ────────────────────────────────────────

def check_browser_search():
    heading("8. BROWSER / SEARCH / CRAWL")

    checks = [
        ("app.tool.browser_use_tool", ["BrowserUseTool"], "browser_use"),
        ("app.agent.browser", ["BrowserAgent", "BrowserContextHelper"], "browser_use"),
        ("app.tool.web_search", ["WebSearch"], "requests, bs4, search engines"),
        ("app.tool.search.base", ["WebSearchEngine", "SearchItem"], "none"),
        ("app.tool.search", None, "none"),
        ("app.tool.crawl4ai", ["Crawl4aiTool"], "crawl4ai"),
        ("app.tool.bash", ["Bash"], "none (subprocess local)"),
        ("app.tool.python_execute", ["PythonExecute"], "none (subprocess local)"),
    ]

    for mod, classes, ext_dep in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")
        inst_ok = SKIP
        evidence = f"import: {s}"
        if err:
            evidence += f" | err: {err}"

        if s == PASS and classes:
            for cls_name in classes:
                if cls_name in ("Bash", "PythonExecute", "SearchItem"):
                    i_s, i_e = try_instantiate(mod, cls_name)
                    if i_s == PASS:
                        inst_ok = PASS
                    else:
                        inst_ok = FAIL
                        evidence += f" | {cls_name}: {i_e}"

        log("browser_search", mod, s, inst_ok, SKIP, ext_dep,
            evidence,
            "KEEP_CORE" if ext_dep == "none" else "KEEP_OPTIONAL",
            "manter")


# ── Ferramentas de sandbox legado ───────────────────────────────────

def check_sandbox_tools():
    heading("9. SANDBOX TOOLS (Daytona SDK)")

    sandbox_tool_modules = [
        "app.tool.sandbox.sb_shell_tool",
        "app.tool.sandbox.sb_files_tool",
        "app.tool.sandbox.sb_browser_tool",
        "app.tool.sandbox.sb_vision_tool",
    ]

    for mod in sandbox_tool_modules:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")
        log("sandbox_tools", mod, s, SKIP, SKIP, "daytona SDK",
            f"import: {s}" + (f" | err: {err}" if err else ""),
            "LEGACY_DEPENDENCY", "depende de daytona SDK; manter até migração")


# ── Data Analysis / Charts ──────────────────────────────────────────

def check_charts():
    heading("10. DATA ANALYSIS / CHARTS")

    checks = [
        ("app.tool.chart_visualization.chart_prepare", ["VisualizationPrepare"]),
        ("app.tool.chart_visualization.data_visualization", ["DataVisualization"]),
        ("app.tool.chart_visualization.python_execute", ["NormalPythonExecute"]),
        ("app.agent.data_analysis", ["DataAnalysis"]),
    ]

    for mod, classes in checks:
        s, err = try_import(mod)
        print(f"  {s:20s} {mod}")
        inst_ok = SKIP
        evidence = f"import: {s}"
        if err:
            evidence += f" | err: {err}"

        log("data_analysis", mod, s, inst_ok, SKIP, "pyecharts, pandas",
            evidence,
            "KEEP_OPTIONAL", "manter (DataAnalysis agent)")


# ── Bedrock ─────────────────────────────────────────────────────────

def check_bedrock():
    heading("11. BEDROCK (AWS)")

    s, err = try_import("app.bedrock")
    print(f"  {s:20s} app.bedrock")
    log("bedrock", "app.bedrock", s, SKIP, SKIP, "boto3 (AWS)",
        f"import: {s}" + (f" | err: {err}" if err else ""),
        "KEEP_OPTIONAL", "manter (alternativa de LLM)")


# ── Tool __init__ registry ──────────────────────────────────────────

def check_tool_registry():
    heading("12. TOOL __init__ REGISTRY")
    s, err = try_import("app.tool")
    if s == PASS:
        from app.tool import __all__ as tool_all
        print(f"  Tools registradas em app.tool.__all__: {tool_all}")
        log("registry", "app.tool.__init__", PASS, PASS, PASS, "none",
            f"Tools registradas: {tool_all}",
            "KEEP_CORE", "manter")
    else:
        print(f"  FAIL: {err}")
        log("registry", "app.tool.__init__", FAIL, FAIL, FAIL, "none",
            f"Falha: {err}",
            "QUARANTINE_FOR_FIX", "revisar")


# ── Manus tool list ─────────────────────────────────────────────────

def check_manus_tool_list():
    heading("13. MANUS TOOL LIST")
    try:
        from app.agent.manus import Manus
        tools_in_manus = [t.name for t in Manus().available_tools.tools]
        print(f"  Tools no Manus default: {tools_in_manus}")
        log("registry", "app.agent.manus (available_tools)", PASS, PASS, PASS, "none",
            f"Tools no Manus: {tools_in_manus}",
            "KEEP_CORE", "manter")
    except Exception as e:
        print(f"  FAIL: {e}")
        log("registry", "app.agent.manus (available_tools)", FAIL, FAIL, FAIL, "none",
            f"Falha: {e}",
            "QUARANTINE_FOR_FIX", "revisar")


# ── Report ──────────────────────────────────────────────────────────

def print_report():
    heading("REPORT FINAL")

    stats = {}
    for r in results:
        stats.setdefault(r["classification"], {"total": 0, "imp_fail": 0, "inst_fail": 0})
        stats[r["classification"]]["total"] += 1
        if r["imp"] == FAIL:
            stats[r["classification"]]["imp_fail"] += 1
        if r["inst"] == FAIL:
            stats[r["classification"]]["inst_fail"] += 1

    print(f"\n{'Classificação':40s} {'Total':>6s} {'ImpFail':>8s} {'InstFail':>9s}")
    print("-" * 65)
    for cls, v in sorted(stats.items()):
        print(f"{cls:40s} {v['total']:6d} {v['imp_fail']:8d} {v['inst_fail']:9d}")

    print(f"\nTotal de módulos validados: {len(results)}")

    fails = [r for r in results if r["imp"] == FAIL]
    if fails:
        print(f"\nFalhas de import ({len(fails)}):")
        for r in fails:
            print(f"  - {r['path']}: {r['evidence'][:100]}")

    print("\nFim da validação modular.")


if __name__ == "__main__":
    print(f"Python {sys.version}")
    print(f"Path: {sys.executable}")
    print(f"CWD: {Path.cwd()}")

    check_config()
    check_agent_core()
    check_main_tools()
    check_validated_tools()
    check_file_tools()
    check_sandbox()
    check_legacy_daytona()
    check_mcp()
    check_browser_search()
    check_sandbox_tools()
    check_charts()
    check_bedrock()
    check_tool_registry()
    check_manus_tool_list()
    print_report()
