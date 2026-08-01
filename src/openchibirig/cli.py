from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from openchibirig.rigging.errors import RiggingError
from openchibirig.rigging.project_writer import write_project
from openchibirig.runtime.compositor import CompositionError, compose_layers
from openchibirig.validation.input_validator import validate_input


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openchibirig")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="校验分层角色输入目录")
    validate.add_argument("input", type=Path)

    compose = commands.add_parser("compose", help="合成分层角色静态预览")
    compose.add_argument("input", type=Path)
    compose.add_argument("--output", "-o", type=Path, required=True)

    rig = commands.add_parser("rig", help="生成基础绑定项目 JSON")
    rig.add_argument("input", type=Path)
    rig.add_argument("--output", "-o", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        report = validate_input(args.input)
        for item in report.diagnostics:
            location = f" [{item.location}]" if item.location else ""
            print(f"{item.severity.value.upper()} {item.code}{location}: {item.message}")
        if report.is_valid:
            print("输入有效。")
            return 0
        return 1

    if args.command == "rig":
        try:
            project = write_project(args.input, args.output)
        except RiggingError as exc:
            print(f"生成绑定项目失败：{exc}", file=sys.stderr)
            return 1
        for warning in project.warnings:
            print(f"WARNING: {warning}")
        print(f"已生成项目：{args.output}")
        return 0

    try:
        image = compose_layers(args.input)
    except CompositionError as exc:
        print(f"合成失败：{exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG")
    print(f"已生成：{args.output}")
    return 0
