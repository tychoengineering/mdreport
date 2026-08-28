#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["click==8.4.2"]
# ///
"""Management CLI

Every command runs through `uv`, so there is no virtual environment to activate first.
The Sphinx tool-chain lives in the `docs` dependency group, which the `dev` group
includes, so `uv run` syncs it automatically and the docs commands need no extra
provisioning. Sphinx autodoc imports `mdreport`, so the docs must be built inside that
environment — this is why the commands go through `uv run` rather than `make html`.

`publish` uploads to the real PyPI by default and will refuse to overwrite an
existing release; test the flow against TestPyPI first.

Usage:
    uv run manage.py docs                          # serve docs at http://127.0.0.1:8000 with livereload
    uv run manage.py docs --port 9000
    uv run manage.py docs --build                  # render to docs/build/html instead of serving
    uv run manage.py docs --build --strict         # treat Sphinx warnings as errors
    uv run manage.py docs-publish                  # push the built docs to the gh-pages branch
    uv run manage.py docs-publish --force          # force-push, discarding gh-pages history
    uv run manage.py publish                       # build sdist+wheel, upload to PyPI
    uv run manage.py publish --repository testpypi
    uv run manage.py publish --skip-build          # upload whatever is already in dist/
    uv run manage.py build                         # build sdist+wheel into dist/
    uv run manage.py test                          # run the pytest suite
    uv run manage.py clean                         # remove build, cache, and docs artifacts
"""

from __future__ import annotations

import enum
import shutil
import subprocess
import tempfile
from pathlib import Path

import click

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
DOCS_SOURCE = DOCS / "source"
DOCS_BUILD = DOCS / "build"
DOCS_HTML = DOCS_BUILD / "html"

# Directories and glob patterns `clean` removes, relative to ROOT.
BUILD_ARTIFACTS = ["build", "dist", "docs/build", ".eggs", ".pytest_cache", ".ruff_cache", ".mypy_cache"]
ARTIFACT_GLOBS = ["**/*.egg-info", "**/*.egg", "**/__pycache__", "**/*.pyc", "**/*.pyo"]


class Repository(enum.StrEnum):
    """A package index `publish` can upload to."""

    PYPI = "pypi"
    TESTPYPI = "testpypi"


PUBLISH_URLS = {
    Repository.PYPI: "https://upload.pypi.org/legacy/",
    Repository.TESTPYPI: "https://test.pypi.org/legacy/",
}


def run(command: list[str]) -> None:
    """Run command in ROOT, echoing it first.

    Raises:
        click.ClickException: if the command exits non-zero or is not installed.
    """
    click.echo(click.style(f"$ {' '.join(command)}", fg="cyan"))
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError as e:
        raise click.ClickException(f"{command[0]} is not installed or not on PATH") from e
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"{command[0]} exited with status {e.returncode}") from e


def sphinx(command: str, arguments: list[str]) -> None:
    """Run a Sphinx tool from the project's docs dependency group.

    Raises:
        click.ClickException: if docs/source/conf.py is missing or the tool exits non-zero.
    """
    if not (DOCS_SOURCE / "conf.py").exists():
        raise click.ClickException(f"{DOCS_SOURCE / 'conf.py'} not found; the docs site has not been configured yet")
    run(["uv", "run", "--group", "docs", command, *arguments])


def build_docs(strict: bool) -> None:
    """Render the documentation into docs/build/html.

    Raises:
        click.ClickException: if sphinx-build fails.
    """
    sphinx("sphinx-build", ["-b", "html", *(["-W"] if strict else []), str(DOCS_SOURCE), str(DOCS_HTML)])


@click.group(help="Development, documentation, and release tasks for mdreport.")
def main() -> None:
    pass


@main.command(help="Serve the documentation with livereload, or render it to docs/build/html.")
@click.option("--build", "is_build", is_flag=True, help="Render to docs/build/html instead of serving.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Address to serve on.")
@click.option(
    "--port", type=click.IntRange(min=1, max=65535), default=8000, show_default=True, help="Port to serve on."
)
@click.option("--strict", is_flag=True, help="Treat Sphinx warnings (broken refs, orphan pages) as errors.")
@click.option("--clean", "is_clean", is_flag=True, help="Discard docs/build first, forcing a full rebuild.")
def docs(is_build: bool, host: str, port: int, strict: bool, is_clean: bool) -> None:
    if is_clean and DOCS_BUILD.exists():
        shutil.rmtree(DOCS_BUILD)
    if is_build:
        build_docs(strict)
        click.echo(click.style(f"Built documentation into {DOCS_HTML}", fg="green"))
        return
    # Autodoc reads the installed package, so a docstring edit under src/ has to
    # retrigger the build as well as a change under docs/source.
    sphinx(
        "sphinx-autobuild",
        [
            "--host",
            host,
            "--port",
            str(port),
            "--watch",
            str(ROOT / "src"),
            *(["-W"] if strict else []),
            str(DOCS_SOURCE),
            str(DOCS_HTML),
        ],
    )


@main.command("docs-publish", help="Build the documentation and deploy it to the gh-pages branch.")
@click.option("--branch", default="gh-pages", show_default=True, help="Branch to deploy the built site to.")
@click.option("--remote-name", default="origin", show_default=True, help="Git remote to push the branch to.")
@click.option("--message", default="Deploy documentation", show_default=True, help="Commit message for the deploy.")
@click.option("--force", is_flag=True, help="Force-push the branch, discarding its remote history.")
@click.option("--allow-warnings", is_flag=True, help="Deploy even if Sphinx reports broken refs or missing pages.")
def docs_publish(branch: str, remote_name: str, message: str, force: bool, allow_warnings: bool) -> None:
    if DOCS_BUILD.exists():
        shutil.rmtree(DOCS_BUILD)
    build_docs(strict=not allow_warnings)
    if not (DOCS_HTML / "index.html").exists():
        raise click.ClickException(f"{DOCS_HTML / 'index.html'} is missing; the documentation build produced no site")

    # Deploy from a detached worktree rather than checking the branch out in place, so
    # an interrupted publish can never leave the working tree on gh-pages.
    with tempfile.TemporaryDirectory() as directory:
        worktree = Path(directory) / "gh-pages"
        run(["git", "worktree", "add", "--detach", str(worktree)])
        try:
            for entry in worktree.iterdir():
                if entry.name == ".git":
                    continue
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            # Without .nojekyll, GitHub Pages drops Sphinx's _static and _sources trees.
            shutil.copytree(DOCS_HTML, worktree, dirs_exist_ok=True, symlinks=False)
            (worktree / ".nojekyll").touch()
            run(["git", "-C", str(worktree), "add", "--all"])
            run(["git", "-C", str(worktree), "commit", "--allow-empty", "--message", message])
            push = ["git", "-C", str(worktree), "push", *(["--force"] if force else []), remote_name]
            run([*push, f"HEAD:refs/heads/{branch}"])
        finally:
            run(["git", "worktree", "remove", "--force", str(worktree)])
    click.echo(click.style(f"Published documentation to {remote_name}/{branch}", fg="green"))


@main.command(help="Build the sdist and wheel into dist/.")
@click.option("--keep-dist", is_flag=True, help="Keep existing artifacts in dist/ instead of clearing it first.")
def build(keep_dist: bool) -> None:
    if not keep_dist and DIST.exists():
        shutil.rmtree(DIST)
    run(["uv", "build", "--out-dir", str(DIST)])
    for artifact in sorted(DIST.iterdir()):
        click.echo(f"  {artifact.name}")


@main.command(help="Build the distribution and upload it to a package index.")
@click.option(
    "--repository",
    type=click.Choice([r.value for r in Repository]),
    default=Repository.PYPI.value,
    show_default=True,
    help="Index to upload to.",
)
@click.option("--skip-build", is_flag=True, help="Upload the existing contents of dist/ without rebuilding.")
@click.option("--token", default=None, help="Index API token. Falls back to UV_PUBLISH_TOKEN or ~/.pypirc.")
def publish(repository: str, skip_build: bool, token: str | None) -> None:
    target = Repository(repository)
    if not skip_build:
        if DIST.exists():
            shutil.rmtree(DIST)
        run(["uv", "build", "--out-dir", str(DIST)])
    artifacts = sorted(DIST.glob("*")) if DIST.exists() else []
    if not artifacts:
        raise click.ClickException("dist/ is empty; drop --skip-build or run `uv run manage.py build` first")

    click.echo(f"Uploading to {target.value}:")
    for artifact in artifacts:
        click.echo(f"  {artifact.name}")
    click.confirm(f"Publish these {len(artifacts)} artifacts to {target.value}?", abort=True)

    command = ["uv", "publish", "--publish-url", PUBLISH_URLS[target]]
    if token is not None:
        command += ["--token", token]
    run([*command, *(str(a) for a in artifacts)])
    click.echo(click.style(f"Published to {target.value}", fg="green"))


@main.command(help="Run the test suite.")
@click.option("--coverage", is_flag=True, help="Also report line coverage for the package.")
@click.option("--path", type=click.Path(path_type=Path), default=Path("tests"), show_default=True, help="Tests to run.")
def test(coverage: bool, path: Path) -> None:
    if coverage:
        run(["uv", "run", "--group", "dev", "pytest", str(path), "--cov=mdreport", "--cov-report=term-missing"])
        return
    run(["uv", "run", "--group", "dev", "pytest", str(path), "-v", "--tb=short"])


@main.command(help="Remove build, cache, and documentation artifacts.")
def clean() -> None:
    removed = 0
    for name in BUILD_ARTIFACTS:
        target = ROOT / name
        if target.is_dir():
            shutil.rmtree(target)
            removed += 1
            click.echo(f"  removed {name}/")
    for pattern in ARTIFACT_GLOBS:
        for target in ROOT.glob(pattern):
            if ".venv" in target.parts or ".git" in target.parts:
                continue
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed += 1
    click.echo(click.style(f"Cleaned {removed} artifacts", fg="green"))


if __name__ == "__main__":
    main()
