"""Dependency file parsers for requirements.txt, pom.xml, and package.json."""
import json
import re
import xml.etree.ElementTree as ET
from typing import NamedTuple


class Dependency(NamedTuple):
    name: str
    version: str
    ecosystem: str


def parse_requirements_txt(content: str) -> list[Dependency]:
    """Parse Python requirements.txt into a list of Dependency objects."""
    deps = []
    for line in content.splitlines():
        line = line.strip()
        # Skip blank lines, comments, and pip options (-r, -i, --index-url, etc.)
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip inline comments
        line = line.split("#")[0].strip()
        # Match: pkg==1.0, pkg>=1.0, pkg~=1.0, pkg[extra]==1.0, pkg; marker
        match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[.*?\])?\s*[=~!<>]+\s*([^\s;,]+)", line)
        if match:
            name = match.group(1).lower().replace("-", "_")
            version = match.group(2).strip()
            deps.append(Dependency(name=name, version=version, ecosystem="pypi"))
        else:
            bare = re.match(r"^([A-Za-z0-9_.-]+)", line)
            if bare:
                name = bare.group(1).lower().replace("-", "_")
                deps.append(Dependency(name=name, version="", ecosystem="pypi"))
    return deps


def parse_pom_xml(content: str) -> list[Dependency]:
    """Parse Maven pom.xml into a list of Dependency objects."""
    deps = []
    try:
        root = ET.fromstring(content)
        # Handle optional XML namespace (e.g. xmlns="http://maven.apache.org/POM/4.0.0")
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for dep in root.iter(f"{ns}dependency"):
            artifact = dep.find(f"{ns}artifactId")
            version_el = dep.find(f"{ns}version")
            if artifact is not None and artifact.text:
                name = artifact.text.strip().lower()
                version = (
                    version_el.text.strip()
                    if version_el is not None and version_el.text
                    else ""
                )
                # Skip property placeholders like ${log4j.version}
                if version.startswith("${"):
                    version = ""
                deps.append(Dependency(name=name, version=version, ecosystem="maven"))
    except ET.ParseError:
        pass
    return deps


def parse_package_json(content: str) -> list[Dependency]:
    """Parse Node.js package.json into a list of Dependency objects."""
    deps = []
    try:
        data = json.loads(content)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for name, version_spec in data.get(section, {}).items():
                # Strip semver range prefixes: ^, ~, >=, <=, >, <, =
                version = re.sub(r"^[^0-9]*", "", str(version_spec)).strip()
                deps.append(
                    Dependency(
                        name=name.lower(),
                        version=version,
                        ecosystem="npm",
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        pass
    return deps


# Dispatch table keyed by filename (basename only)
_PARSERS = {
    "requirements.txt": parse_requirements_txt,
    "pom.xml": parse_pom_xml,
    "package.json": parse_package_json,
}


def parse_manifest(filename: str, content: str) -> list[Dependency]:
    """Parse a dependency manifest file. Returns [] for unknown file types."""
    basename = filename.split("/")[-1]
    parser = _PARSERS.get(basename)
    if parser is None:
        return []
    return parser(content)
