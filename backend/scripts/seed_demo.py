"""Seed demo vulnerabilities and repositories into MongoDB."""
import asyncio
from datetime import datetime, timezone

from shared.utils.mongo import init_db, get_database
from shared.constants import (
    COLLECTION_VULNERABILITIES,
    COLLECTION_REPOSITORIES,
)

MONGO_URI = "mongodb://mongodb:27017/dependencymedic"


DEMO_VULNERABILITIES = [
    {
        "_id": "vuln-demo-001",
        "cve_id": "CVE-2021-44228",
        "aliases": ["GHSA-jfh8-c2jp-hdp8"],
        "summary": "Apache Log4j2 Remote Code Execution (Log4Shell)",
        "description": "Apache Log4j2 JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints.",
        "severity": "critical",
        "cvss_score": 10.0,
        "epss_score": 0.97,
        "published_at": "2021-12-10T00:00:00Z",
        "affected_packages": [
            {
                "name": "log4j-core",
                "ecosystem": "maven",
                "affected_versions": "<2.15.0",
                "fixed_versions": ["2.15.0", "2.17.1"],
            }
        ],
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
        "source": "NVD",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "seed_demo",
        "version": 1,
    },
    {
        "_id": "vuln-demo-002",
        "cve_id": "CVE-2021-45046",
        "aliases": [],
        "summary": "Apache Log4j2 DoS and RCE via Thread Context Map",
        "description": "It was found that the fix to address CVE-2021-44228 in Apache Log4j 2.15.0 was incomplete.",
        "severity": "critical",
        "cvss_score": 9.0,
        "epss_score": 0.95,
        "published_at": "2021-12-14T00:00:00Z",
        "affected_packages": [
            {
                "name": "log4j-core",
                "ecosystem": "maven",
                "affected_versions": "<2.16.0",
                "fixed_versions": ["2.16.0"],
            }
        ],
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2021-45046"],
        "source": "NVD",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "seed_demo",
        "version": 1,
    },
]

DEMO_REPOSITORIES = [
    {
        "_id": "repo-demo-001",
        "repo_name": "demo-payment-service",
        "gitlab_project_id": "82069687",
        "default_branch": "main",
        "languages": ["java"],
        "repo_url": "https://gitlab.com/varunkamath05/demo-payment-service",
        "ci_enabled": True,
        "last_scanned_commit": None,
        "status": "active",
        "tags": ["critical-service", "payments"],
        "seed_manifests": {
            "pom.xml": (
                "<project>\n"
                "  <dependencies>\n"
                "    <dependency>\n"
                "      <groupId>org.apache.logging.log4j</groupId>\n"
                "      <artifactId>log4j-core</artifactId>\n"
                "      <version>2.14.1</version>\n"
                "    </dependency>\n"
                "  </dependencies>\n"
                "</project>\n"
            ),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "seed_demo",
        "version": 1,
    },
    {
        "_id": "repo-demo-002",
        "repo_name": "demo-auth-service",
        "gitlab_project_id": "82069719",
        "default_branch": "main",
        "languages": ["python"],
        "repo_url": "https://gitlab.com/varunkamath05/demo-auth-service",
        "ci_enabled": True,
        "last_scanned_commit": None,
        "status": "active",
        "tags": ["auth", "security-critical"],
        "seed_manifests": {
            "requirements.txt": (
                "cryptography==38.0.0\n"
                "requests==2.27.0\n"
                "Flask==2.0.0\n"
                "PyJWT==2.4.0\n"
            ),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "seed_demo",
        "version": 1,
    },
    {
        "_id": "repo-demo-003",
        "repo_name": "demo-inventory-service",
        "gitlab_project_id": "82069731",
        "default_branch": "main",
        "languages": ["python"],
        "repo_url": "https://gitlab.com/varunkamath05/demo-inventory-service",
        "ci_enabled": True,
        "last_scanned_commit": None,
        "status": "active",
        "tags": ["inventory"],
        "seed_manifests": {
            "requirements.txt": (
                "Pillow==9.0.0\n"
                "PyYAML==5.4.1\n"
                "requests==2.26.0\n"
                "Django==3.2.0\n"
            ),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "seed_demo",
        "version": 1,
    },
]


async def seed():
    await init_db(MONGO_URI)
    db = get_database()

    for vuln in DEMO_VULNERABILITIES:
        await db[COLLECTION_VULNERABILITIES].update_one(
            {"_id": vuln["_id"]}, {"$set": vuln}, upsert=True
        )
        print(f"Seeded vulnerability: {vuln['cve_id']}")

    for repo in DEMO_REPOSITORIES:
        await db[COLLECTION_REPOSITORIES].update_one(
            {"_id": repo["_id"]}, {"$set": repo}, upsert=True
        )
        print(f"Seeded repository: {repo['repo_name']}")

    print("Demo seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
