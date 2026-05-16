"""
Trigger the demo flow end-to-end using the seeded CVE-2023-32681 (requests SSRF).

This script:
1. Checks api_gateway health
2. Publishes vuln.discovered + vuln.matched by calling the ingest endpoint
   with the specific packages from the seed repos
3. Prints the chain of events to watch for

Usage (from docker-compose run):
  docker-compose run --rm api_gateway python /app/scripts/trigger_demo.py
"""
import asyncio
import json
import sys

import httpx

API_BASE = "http://api_gateway:8000/api/v1"


async def main():
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        # Health check
        r = await client.get("/health")
        health = r.json()
        print(f"Health: {health.get('data', {}).get('status', 'unknown')}")

        # Seed demo data
        print("\nSeeding demo data...")
        from shared.utils.mongo import init_db, get_database
        from shared.constants import COLLECTION_VULNERABILITIES, COLLECTION_REPOSITORIES

        # Load seed data
        import sys
        sys.path.insert(0, "/app/scripts")
        from seed_demo import seed, MONGO_URI
        await seed()

        # Trigger ingest with the packages that match our Python demo repos
        print("\nTriggering ingest for CVE-2023-32681 (requests SSRF)...")
        r = await client.post(
            "/vulnerabilities/ingest",
            json={
                "days_back": 365,
                "severities": ["CRITICAL", "HIGH"],
                "packages": [
                    {"name": "requests", "ecosystem": "PyPI"},
                    {"name": "cryptography", "ecosystem": "PyPI"},
                ],
            },
        )
        result = r.json()
        data = result.get("data", {})
        print(json.dumps(data, indent=2))

        if data.get("matched_published", 0) > 0:
            print(
                f"\n✓ {data['matched_published']} vuln.matched event(s) published."
            )
            print("  Watch the chain fire:")
            print("  vuln.matched → vuln.assessed → vuln.scored")
            print("  → patch.generated → ci.started → ci.failed (attempt-1)")
            print("  → patch.retry_requested → patch.validated → mr.created")
            print("\n  docker-compose logs -f reachability_analysis remediation_engine gitlab_integration")
        elif data.get("events_published", 0) == 0:
            print(
                "\n⚠ No new events published — CVEs already in DB."
                "\nRun: docker-compose down -v && make up && make seed-demo"
                "\nThen re-run this script."
            )
        else:
            print(
                f"\n⚠ {data['events_published']} vuln.discovered published but 0 repo matches."
                "\nCheck that make seed-demo ran successfully."
            )


if __name__ == "__main__":
    asyncio.run(main())
