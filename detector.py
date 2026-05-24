from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

import javalang
from javalang.parser import JavaSyntaxError
from javalang.tokenizer import LexerError


@dataclass
class FieldInfo:
    signature: str
    line: int


@dataclass
class ClassInfo:
    name: str
    file_name: str
    fields: Dict[str, FieldInfo]
    declaration_line: int


@dataclass
class SmellIssue:
    file_name: str
    line_number: int
    code_smell_type: str
    severity_details: str


def _type_name(type_node) -> str:
    if type_node is None:
        return "Unknown"
    name = getattr(type_node, "name", str(type_node))
    dimensions = "[]" * len(getattr(type_node, "dimensions", []) or [])
    return f"{name}{dimensions}"


def _is_self_qualifier(qualifier: str | None) -> bool:
    return qualifier in (None, "", "this")


def _parse_java_file(file_path: Path) -> tuple[List[ClassInfo], List[SmellIssue]]:
    source = file_path.read_text(encoding="utf-8")
    tree = javalang.parse.parse(source)

    classes: List[ClassInfo] = []
    feature_envy_issues: List[SmellIssue] = []

    for _, class_decl in tree.filter(javalang.tree.ClassDeclaration):
        class_fields: Dict[str, FieldInfo] = {}
        own_field_names: Set[str] = set()

        for field_decl in class_decl.fields:
            field_type = _type_name(field_decl.type)
            for declarator in field_decl.declarators:
                signature = f"{field_type} {declarator.name}"
                line = (
                    declarator.position.line
                    if declarator.position
                    else field_decl.position.line
                    if field_decl.position
                    else class_decl.position.line
                    if class_decl.position
                    else 1
                )
                class_fields[signature] = FieldInfo(signature=signature, line=line)
                own_field_names.add(declarator.name)

        classes.append(
            ClassInfo(
                name=class_decl.name,
                file_name=file_path.name,
                fields=class_fields,
                declaration_line=class_decl.position.line if class_decl.position else 1,
            )
        )

        for method_decl in class_decl.methods:
            own_interactions = 0
            external_interactions = 0
            external_targets: Dict[str, int] = {}

            for _, method_invocation in method_decl.filter(javalang.tree.MethodInvocation):
                qualifier = method_invocation.qualifier
                if _is_self_qualifier(qualifier):
                    own_interactions += 1
                else:
                    external_interactions += 1
                    external_targets[qualifier] = external_targets.get(qualifier, 0) + 1

            for _, member_ref in method_decl.filter(javalang.tree.MemberReference):
                qualifier = member_ref.qualifier
                if _is_self_qualifier(qualifier) and member_ref.member in own_field_names:
                    own_interactions += 1
                elif not _is_self_qualifier(qualifier):
                    external_interactions += 1
                    external_targets[qualifier] = external_targets.get(qualifier, 0) + 1

            if external_interactions >= 3 and external_interactions > own_interactions:
                target = (
                    max(external_targets, key=external_targets.__getitem__)
                    if external_targets
                    else "external object"
                )
                feature_envy_issues.append(
                    SmellIssue(
                        file_name=file_path.name,
                        line_number=method_decl.position.line if method_decl.position else 1,
                        code_smell_type="Feature Envy",
                        severity_details=(
                            f"Method '{method_decl.name}' has {external_interactions} external interactions "
                            f"vs {own_interactions} own interactions (main target: {target})."
                        ),
                    )
                )

    return classes, feature_envy_issues


def _detect_data_clumps(class_infos: List[ClassInfo]) -> List[SmellIssue]:
    issues: List[SmellIssue] = []

    for i, class_a in enumerate(class_infos):
        fields_a = set(class_a.fields.keys())
        for class_b in class_infos[i + 1 :]:
            fields_b = set(class_b.fields.keys())
            common = sorted(fields_a.intersection(fields_b))

            if len(common) >= 3:
                first_line_a = min(class_a.fields[sig].line for sig in common)
                first_line_b = min(class_b.fields[sig].line for sig in common)
                shared_fields = ", ".join(common)

                issues.append(
                    SmellIssue(
                        file_name=class_a.file_name,
                        line_number=first_line_a,
                        code_smell_type="Data Clumps",
                        severity_details=f"Shared with class '{class_b.name}': {shared_fields}.",
                    )
                )
                issues.append(
                    SmellIssue(
                        file_name=class_b.file_name,
                        line_number=first_line_b,
                        code_smell_type="Data Clumps",
                        severity_details=f"Shared with class '{class_a.name}': {shared_fields}.",
                    )
                )

    return issues


def detect_code_smells(directory: Path) -> List[dict]:
    java_files = sorted(directory.rglob("*.java"))

    class_infos: List[ClassInfo] = []
    issues: List[SmellIssue] = []

    for java_file in java_files:
        try:
            file_classes, file_issues = _parse_java_file(java_file)
            class_infos.extend(file_classes)
            issues.extend(file_issues)
        except (JavaSyntaxError, LexerError, TypeError, OSError, UnicodeDecodeError) as exc:  # pragma: no cover
            issues.append(
                SmellIssue(
                    file_name=java_file.name,
                    line_number=1,
                    code_smell_type="Parse Error",
                    severity_details=f"Unable to parse file: {exc}",
                )
            )

    issues.extend(_detect_data_clumps(class_infos))

    return [
        {
            "File Name": issue.file_name,
            "Line Number": issue.line_number,
            "Code Smell Type": issue.code_smell_type,
            "Severity/Details": issue.severity_details,
        }
        for issue in sorted(issues, key=lambda x: (x.file_name, x.line_number, x.code_smell_type))
    ]
