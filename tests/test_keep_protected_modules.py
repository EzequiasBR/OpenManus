import importlib
from pathlib import Path


def test_keep_protected_modules_import():
    modules = [
        "app.tool.create_chat_completion",
        "app.tool.python_execute",
        "app.tool.str_replace_editor",
        "app.tool.file_operators",
    ]

    imported = [importlib.import_module(module_name) for module_name in modules]

    assert len(imported) == len(modules)


def test_create_chat_completion_class_available():
    module = importlib.import_module("app.tool.create_chat_completion")

    assert hasattr(module, "CreateChatCompletion")


def test_python_execute_class_available():
    module = importlib.import_module("app.tool.python_execute")

    assert hasattr(module, "PythonExecute")


def test_str_replace_editor_class_available():
    module = importlib.import_module("app.tool.str_replace_editor")

    assert hasattr(module, "StrReplaceEditor")


def test_file_operator_classes_available():
    module = importlib.import_module("app.tool.file_operators")

    assert hasattr(module, "LocalFileOperator")
    assert hasattr(module, "SandboxFileOperator")
    assert hasattr(module, "FileOperator")

    local_operator = module.LocalFileOperator()

    assert isinstance(local_operator, module.LocalFileOperator)


def test_validation_script_exists():
    validation_script = Path("scripts/validation/validate_modules.py")

    assert validation_script.exists()
    assert validation_script.is_file()


def test_validation_script_has_main_guard():
    validation_script = Path("scripts/validation/validate_modules.py")
    content = validation_script.read_text(encoding="utf-8", errors="replace")

    assert 'if __name__ == "__main__"' in content
