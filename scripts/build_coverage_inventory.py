#!/usr/bin/env python3
"""Build the tracked-file coverage inventory for the pinned SGLang snapshot."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".source" / "sglang"
OUTPUT = ROOT / "docs" / "coverage" / "inventory.csv"
OVERRIDES = ROOT / "docs" / "coverage" / "overrides.csv"
COMMIT = "f464e77d17a3908ad0ea32547b1e8b039bcbd354"
SOURCE_BASE = f"https://github.com/EltonChang1/sglang/blob/{COMMIT}/"
NOTES_BASE = "https://github.com/EltonChang1/SGLang-breakdown/blob/main/"

STATUSES = {"pending", "partial", "covered", "inventory-only"}
BINARY_SUFFIXES = {
    ".bin",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".npy",
    ".npz",
    ".pdf",
    ".pkl",
    ".png",
    ".pt",
    ".pth",
    ".safetensors",
    ".tar",
    ".woff",
    ".woff2",
    ".zip",
}
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cu",
    ".cuh",
    ".go",
    ".h",
    ".hip",
    ".hpp",
    ".inl",
    ".js",
    ".jsx",
    ".metal",
    ".mjs",
    ".mu",
    ".muh",
    ".proto",
    ".py",
    ".rs",
    ".sh",
}
CONFIG_SUFFIXES = {".cfg", ".conf", ".ini", ".json", ".toml", ".yaml", ".yml"}
DOC_SUFFIXES = {".md", ".mdx", ".rst"}
BUILD_NAMES = {
    "build.rs",
    "cargo.lock",
    "cargo.toml",
    "cmakelists.txt",
    "dockerfile",
    "go.mod",
    "go.sum",
    "makefile",
    "manifest.in",
    "package.json",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
}


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(SOURCE), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def tracked_paths() -> list[str]:
    return sorted(path for path in run_git("ls-files").splitlines() if path)


def classify(path_text: str) -> tuple[str, str]:
    path = PurePosixPath(path_text)
    parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    suffix = path.suffix.lower()

    if (
        "generated" in parts
        or name.endswith("_pb2.py")
        or name.endswith(".pb.go")
        or name.endswith("_grpc.pb.go")
        or path_text == "python/sglang/_version.py"
    ):
        return (
            "generated",
            "Machine-generated binding or version output; study its schema or generator instead of duplicating generated code.",
        )

    if "3rdparty" in parts or "third_party" in parts or "vendored" in parts:
        return (
            "vendored",
            "Third-party material; study provenance and SGLang's integration boundary instead of reproducing an upstream line-by-line guide.",
        )

    if suffix in BINARY_SUFFIXES:
        return (
            "binary",
            "Binary artifact; record its role with the containing subsystem rather than attempting line-by-line source notes.",
        )

    is_test_path = bool({"test", "tests", "e2e_test", "benches", "benchmark"} & set(parts))
    is_test_name = name.startswith("test_") or name.endswith("_test.py") or name.endswith("_test.rs")
    if is_test_path or is_test_name:
        detail = "benchmark/evaluation" if "benchmark" in parts or "benches" in parts else "test"
        return "test", f"Awaiting the {detail} coverage pass."

    if "examples" in parts or "example" in parts or "playground" in parts or suffix == ".ipynb":
        return "example", "Awaiting the example and runnable-usage coverage pass."

    if "docs" in parts or suffix in DOC_SUFFIXES or name in {
        "authors",
        "code_of_conduct.md",
        "license",
        "readme",
        "readme.md",
        "thirdpartynotices.txt",
    }:
        return "documentation", "Awaiting the documentation-intent and navigation coverage pass."

    if parts[:2] in {(".github", "actions"), (".github", "workflows")}:
        return "CI", "Awaiting the continuous-integration workflow coverage pass."
    if parts and parts[0] == ".github" and (
        name.endswith(".py") or name in {"ci_permissions.json"}
    ):
        return "CI", "Awaiting the continuous-integration support-tool coverage pass."

    if (
        name in BUILD_NAMES
        or suffix == ".cmake"
        or "docker" in parts
        or "release" in parts
        or "wheel" in parts
    ):
        return "build or packaging", "Awaiting the build, packaging, or containerization coverage pass."

    if (
        parts and parts[0] in {".devcontainer"}
        or (parts and parts[0] == ".github")
        or "config" in parts
        or "configs" in parts
        or suffix in CONFIG_SUFFIXES
        or name.endswith((".sample", ".tmpl"))
        or name.startswith(".")
    ):
        return "configuration", "Awaiting the configuration coverage pass."

    if {"assets", "images", "fonts", "static"} & set(parts) or suffix in {
        ".css",
        ".html",
        ".svg",
    }:
        return (
            "asset",
            "Static presentation or sample asset; the containing subsystem note will explain its role when needed.",
        )

    if suffix in SOURCE_SUFFIXES or name in {"gateway", "router", "fake_worker"}:
        return "source", "Awaiting a source-level subsystem or file reference pass."

    return "other", "Awaiting explicit review and either a detailed note or a justified inventory-only disposition."


def load_overrides() -> dict[str, dict[str, str]]:
    overrides: dict[str, dict[str, str]] = {}
    with OVERRIDES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = row["path"]
            if path in overrides:
                raise ValueError(f"duplicate override: {path}")
            if row["status"] not in STATUSES:
                raise ValueError(f"invalid status for {path}: {row['status']}")
            overrides[path] = row
    return overrides


def render() -> str:
    paths = tracked_paths()
    path_set = set(paths)
    overrides = load_overrides()
    unknown = sorted(set(overrides) - path_set)
    if unknown:
        raise ValueError(f"coverage overrides are not tracked at {COMMIT}: {unknown}")

    buffer = io.StringIO(newline="")
    fieldnames = ["path", "category", "status", "note_path", "note_url", "reason", "source_url"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for path in paths:
        category, default_reason = classify(path)
        override = overrides.get(path)
        status = override["status"] if override else (
            "inventory-only" if category in {"asset", "binary", "generated", "vendored"} else "pending"
        )
        note_path = override["note_path"] if override else ""
        reason = override["reason"] if override and override["reason"] else default_reason
        note_url = f"{NOTES_BASE}{note_path}" if note_path else ""
        writer.writerow(
            {
                "path": path,
                "category": category,
                "status": status,
                "note_path": note_path,
                "note_url": note_url,
                "reason": reason,
                "source_url": f"{SOURCE_BASE}{path}",
            }
        )

    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed inventory is not current",
    )
    args = parser.parse_args()

    actual_commit = run_git("rev-parse", "HEAD").strip()
    if actual_commit != COMMIT:
        print(
            f"source checkout is {actual_commit}, expected {COMMIT}",
            file=sys.stderr,
        )
        return 2

    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(f"{OUTPUT.relative_to(ROOT)} is stale", file=sys.stderr)
            return 1
        print(f"coverage inventory is current ({len(tracked_paths())} paths)")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(tracked_paths())} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
