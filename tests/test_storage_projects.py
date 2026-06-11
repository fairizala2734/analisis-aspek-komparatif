from pathlib import Path

from storage.projects import get_project_dir


def test_project_dir_includes_slugified_title(tmp_path: Path) -> None:
    project_dir = get_project_dir(tmp_path, "abc123", "Judul Analisis Keren")
    assert project_dir.name == "judul-analisis-keren__abc123"
