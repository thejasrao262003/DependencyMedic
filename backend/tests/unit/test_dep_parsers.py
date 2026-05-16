"""Unit tests for dependency file parsers."""
from services.vuln_intelligence.utils.parsers import (
    parse_requirements_txt,
    parse_pom_xml,
    parse_package_json,
    parse_manifest,
)


# ─── requirements.txt ────────────────────────────────────────────────────────

def test_requirements_pinned_versions():
    content = "requests==2.27.0\ncryptography==38.0.0\n"
    deps = parse_requirements_txt(content)
    names = {d.name for d in deps}
    assert "requests" in names
    assert "cryptography" in names
    assert all(d.ecosystem == "pypi" for d in deps)


def test_requirements_version_extracted():
    deps = parse_requirements_txt("Flask==2.0.0\n")
    assert deps[0].version == "2.0.0"


def test_requirements_skips_comments_and_blank():
    content = "# this is a comment\n\nrequests==2.27.0\n"
    deps = parse_requirements_txt(content)
    assert len(deps) == 1


def test_requirements_skips_pip_options():
    content = "-r base.txt\n--index-url https://pypi.org\nrequests==2.27.0\n"
    deps = parse_requirements_txt(content)
    assert len(deps) == 1
    assert deps[0].name == "requests"


def test_requirements_extras_notation():
    deps = parse_requirements_txt("uvicorn[standard]==0.20.0\n")
    assert deps[0].name == "uvicorn"
    assert deps[0].version == "0.20.0"


def test_requirements_dash_normalized_to_underscore():
    deps = parse_requirements_txt("some-package==1.0.0\n")
    assert deps[0].name == "some_package"


def test_requirements_bare_package_no_version():
    deps = parse_requirements_txt("requests\n")
    assert deps[0].name == "requests"
    assert deps[0].version == ""


def test_requirements_ge_operator():
    deps = parse_requirements_txt("Django>=3.2.0\n")
    assert deps[0].name == "django"
    assert deps[0].version == "3.2.0"


# ─── pom.xml ─────────────────────────────────────────────────────────────────

_POM_SIMPLE = """\
<project>
  <dependencies>
    <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-core</artifactId>
      <version>2.14.1</version>
    </dependency>
  </dependencies>
</project>
"""

_POM_WITH_NAMESPACE = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <dependencies>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>my-lib</artifactId>
      <version>1.0.0</version>
    </dependency>
  </dependencies>
</project>
"""


def test_pom_extracts_artifact_and_version():
    deps = parse_pom_xml(_POM_SIMPLE)
    assert len(deps) == 1
    assert deps[0].name == "log4j-core"
    assert deps[0].version == "2.14.1"
    assert deps[0].ecosystem == "maven"


def test_pom_handles_namespace():
    deps = parse_pom_xml(_POM_WITH_NAMESPACE)
    assert len(deps) == 1
    assert deps[0].name == "my-lib"


def test_pom_property_placeholder_version_becomes_empty():
    content = """\
<project>
  <dependencies>
    <dependency>
      <artifactId>some-lib</artifactId>
      <version>${some.version}</version>
    </dependency>
  </dependencies>
</project>
"""
    deps = parse_pom_xml(content)
    assert deps[0].version == ""


def test_pom_invalid_xml_returns_empty():
    deps = parse_pom_xml("not xml at all <<<")
    assert deps == []


# ─── package.json ─────────────────────────────────────────────────────────────

_PKG_JSON = """\
{
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "~4.17.11"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
"""


def test_package_json_extracts_dependencies():
    deps = parse_package_json(_PKG_JSON)
    names = {d.name for d in deps}
    assert "express" in names
    assert "lodash" in names
    assert "jest" in names


def test_package_json_strips_semver_prefix():
    deps = parse_package_json(_PKG_JSON)
    by_name = {d.name: d for d in deps}
    assert by_name["express"].version == "4.18.0"
    assert by_name["lodash"].version == "4.17.11"


def test_package_json_ecosystem_is_npm():
    deps = parse_package_json(_PKG_JSON)
    assert all(d.ecosystem == "npm" for d in deps)


def test_package_json_invalid_returns_empty():
    deps = parse_package_json("{ bad json }")
    assert deps == []


# ─── parse_manifest dispatcher ───────────────────────────────────────────────

def test_dispatch_requirements_txt():
    deps = parse_manifest("requirements.txt", "requests==2.27.0\n")
    assert deps[0].name == "requests"


def test_dispatch_pom_xml():
    deps = parse_manifest("pom.xml", _POM_SIMPLE)
    assert deps[0].name == "log4j-core"


def test_dispatch_package_json():
    deps = parse_manifest("package.json", _PKG_JSON)
    assert any(d.name == "express" for d in deps)


def test_dispatch_unknown_file_returns_empty():
    deps = parse_manifest("Gemfile", "gem 'rails'")
    assert deps == []


def test_dispatch_nested_path_uses_basename():
    deps = parse_manifest("services/auth/requirements.txt", "Flask==2.0.0\n")
    assert deps[0].name == "flask"
