import importlib
from pathlib import Path

from app.agent.manus import Manus
from app.tool.daytona_sandbox import DaytonaSandboxTool
from app.tool.image_generator import ImageGeneratorTool


def test_core_modules_import():
    modules = [
        "app.config",
        "app.schema",
        "app.llm",
        "app.agent.base",
        "app.agent.toolcall",
        "app.agent.manus",
        "app.flow",
        "app.prompt",
        "app.tool.base",
        "app.tool.tool_collection",
    ]

    imported = [importlib.import_module(module_name) for module_name in modules]

    assert len(imported) == len(modules)


def test_validated_tools_import():
    modules = [
        "app.integrations.daytona_http",
        "app.tool.daytona_sandbox",
        "app.tool.image_generator",
    ]

    imported = [importlib.import_module(module_name) for module_name in modules]

    assert len(imported) == len(modules)


def test_image_generator_instantiates_without_network():
    tool = ImageGeneratorTool()

    assert tool.name == "generate_image"
    assert "prompt" in tool.parameters["properties"]


def test_daytona_sandbox_tool_instantiates_without_remote_call():
    tool = DaytonaSandboxTool()

    assert tool.name == "daytona_sandbox"
    assert "action" in tool.parameters["properties"]
    assert "code" in tool.parameters["properties"]


def test_manus_default_tools_registry():
    manus = Manus()
    tool_names = [tool.name for tool in manus.available_tools.tools]

    expected_names = {
        "python_execute",
        "str_replace_editor",
        "ask_human",
        "generate_image",
        "terminate",
        "daytona_sandbox",
    }

    assert expected_names.issubset(set(tool_names))


def test_sandbox_docker_not_required_for_boot_registry(monkeypatch):
    import docker

    def fail_if_docker_client_is_created(*args, **kwargs):
        raise AssertionError("Boot/registry should not create a Docker client")

    monkeypatch.setattr(docker, "from_env", fail_if_docker_client_is_created)

    manus = Manus()
    tool_names = [tool.name for tool in manus.available_tools.tools]

    assert "daytona_sandbox" in tool_names


def test_validation_script_importable_or_exists():
    validation_script = Path("scripts/validation/validate_modules.py")

    assert validation_script.exists()
    assert validation_script.is_file()
