"""Tests for SDK example fetching and installation helpers."""

import json
from pathlib import Path

import pytest

from lab.tools.import_sdk_example import ImportSdkExampleAction, ImportSdkExampleExecutor
from lab.utils.sdk_examples import (
    CatalogExample,
    GitHubExamplesClient,
    build_human_label,
    install_catalog_example,
    match_catalog_example,
)


class FakeGitHubExamplesClient(GitHubExamplesClient):
    """Test client backed by in-memory directory listings."""

    def __init__(self, listings, files):
        super().__init__()
        self.listings = listings
        self.files = files

    def list_directory(self, path: str):
        return self.listings[path]

    def get_file_text(self, path: str) -> str:
        return self.files[path]


def test_build_human_label():
    assert build_human_label("01_standalone_sdk", "01_hello_world.py") == "Standalone SDK / Hello World"
    assert build_human_label("05_skills_and_plugins", "02_loading_plugins") == "Skills And Plugins / Loading Plugins"


def test_match_catalog_example_exact_and_partial():
    catalog = [
        CatalogExample(
            label="Standalone SDK / Hello World",
            category="Standalone SDK",
            short_name="Hello World",
            relative_path="examples/01_standalone_sdk/01_hello_world.py",
            example_type="file",
            source_url="https://example.com/hello",
        ),
        CatalogExample(
            label="Standalone SDK / Agent Delegation",
            category="Standalone SDK",
            short_name="Agent Delegation",
            relative_path="examples/01_standalone_sdk/25_agent_delegation.py",
            example_type="file",
            source_url="https://example.com/delegation",
        ),
    ]

    matched, candidates = match_catalog_example("hello world", catalog)
    assert matched is not None
    assert matched.short_name == "Hello World"
    assert len(candidates) == 1

    matched, candidates = match_catalog_example("delegation", catalog)
    assert matched is not None
    assert matched.short_name == "Agent Delegation"
    assert len(candidates) == 1


def test_install_catalog_example_file(tmp_path):
    client = FakeGitHubExamplesClient(listings={}, files={"examples/01_standalone_sdk/01_hello_world.py": "print('hello')\n"})
    example = CatalogExample(
        label="Standalone SDK / Hello World",
        category="Standalone SDK",
        short_name="Hello World",
        relative_path="examples/01_standalone_sdk/01_hello_world.py",
        example_type="file",
        source_url="https://example.com/hello",
    )

    installed_paths, manifest_path = install_catalog_example(
        client=client,
        example=example,
        destination_root=tmp_path / "examples/sdk",
    )

    installed_file = tmp_path / "examples/sdk/01_standalone_sdk/01_hello_world.py"
    assert installed_file.read_text() == "print('hello')\n"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text())
    assert payload["imports"][0]["label"] == "Standalone SDK / Hello World"
    assert str(installed_file) in [str(path) for path in installed_paths]


def test_install_catalog_example_directory(tmp_path):
    client = FakeGitHubExamplesClient(
        listings={
            "examples/05_skills_and_plugins/02_loading_plugins": [
                {
                    "name": "README.md",
                    "path": "examples/05_skills_and_plugins/02_loading_plugins/README.md",
                    "type": "file",
                },
                {
                    "name": "app.py",
                    "path": "examples/05_skills_and_plugins/02_loading_plugins/app.py",
                    "type": "file",
                },
            ]
        },
        files={
            "examples/05_skills_and_plugins/02_loading_plugins/README.md": "# demo\n",
            "examples/05_skills_and_plugins/02_loading_plugins/app.py": "print('plugins')\n",
        },
    )
    example = CatalogExample(
        label="Skills And Plugins / Loading Plugins",
        category="Skills And Plugins",
        short_name="Loading Plugins",
        relative_path="examples/05_skills_and_plugins/02_loading_plugins",
        example_type="dir",
        source_url="https://example.com/plugins",
    )

    installed_paths, manifest_path = install_catalog_example(
        client=client,
        example=example,
        destination_root=tmp_path / "examples/sdk",
    )

    installed_dir = tmp_path / "examples/sdk/05_skills_and_plugins/02_loading_plugins"
    assert (installed_dir / "README.md").read_text() == "# demo\n"
    assert (installed_dir / "app.py").read_text() == "print('plugins')\n"
    assert manifest_path.exists()
    assert any(path.name == "app.py" for path in installed_paths)


def test_install_catalog_example_protects_existing_files(tmp_path):
    client = FakeGitHubExamplesClient(listings={}, files={"examples/01_standalone_sdk/01_hello_world.py": "print('hello')\n"})
    example = CatalogExample(
        label="Standalone SDK / Hello World",
        category="Standalone SDK",
        short_name="Hello World",
        relative_path="examples/01_standalone_sdk/01_hello_world.py",
        example_type="file",
        source_url="https://example.com/hello",
    )

    destination = tmp_path / "examples/sdk/01_standalone_sdk/01_hello_world.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("existing\n")

    with pytest.raises(FileExistsError):
        install_catalog_example(
            client=client,
            example=example,
            destination_root=tmp_path / "examples/sdk",
            overwrite=False,
        )


def test_import_sdk_example_executor_lists_catalog(monkeypatch, tmp_path):
    executor = ImportSdkExampleExecutor(working_dir=tmp_path)
    catalog = [
        CatalogExample(
            label="Standalone SDK / Hello World",
            category="Standalone SDK",
            short_name="Hello World",
            relative_path="examples/01_standalone_sdk/01_hello_world.py",
            example_type="file",
            source_url="https://example.com/hello",
        )
    ]
    monkeypatch.setattr(executor, "_build_catalog", lambda action: catalog)

    observation = executor(ImportSdkExampleAction())

    assert observation.error is None
    assert observation.available_examples == ["Standalone SDK / Hello World"]


def test_import_sdk_example_executor_installs_selected_example(monkeypatch, tmp_path):
    executor = ImportSdkExampleExecutor(working_dir=tmp_path)
    catalog = [
        CatalogExample(
            label="Standalone SDK / Hello World",
            category="Standalone SDK",
            short_name="Hello World",
            relative_path="examples/01_standalone_sdk/01_hello_world.py",
            example_type="file",
            source_url="https://example.com/hello",
        )
    ]
    client = FakeGitHubExamplesClient(
        listings={},
        files={"examples/01_standalone_sdk/01_hello_world.py": "print('hello')\n"},
    )
    monkeypatch.setattr(executor, "_build_catalog", lambda action: catalog)
    monkeypatch.setattr(executor, "_client_for", lambda action: client)

    observation = executor(
        ImportSdkExampleAction(example_query="hello world", destination_root="examples/sdk")
    )

    assert observation.error is None
    assert observation.matched_example == "Standalone SDK / Hello World"
    assert (tmp_path / "examples/sdk/01_standalone_sdk/01_hello_world.py").exists()
