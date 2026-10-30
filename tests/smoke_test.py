"""Non-destructive smoke tests against a running local Codingal Code Studio API.

Usage: python tests/smoke_test.py [http://127.0.0.1:8000]
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")

def get(path):
    req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        if response.status != 200:
            raise AssertionError(f"{path}: unexpected HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))

checks = []
health = get("/api/health")
assert health.get("status") == "ok", health
checks.append("health")
overview = get("/api/overview")
assert overview["metrics"]["students"] >= 1
assert len(overview["concepts"]) >= 1
checks.append("overview and concept aggregates")
learners = get("/api/students")
assert learners["total"] >= 1 and "mastery" in learners["items"][0]
checks.append("learner listing")
learner_id = learners["items"][0]["id"]
detail = get(f"/api/students/{learner_id}")
assert "concepts" in detail and "submissions" in detail
checks.append("learner detail")
assignments = get("/api/assignments")
assert assignments["total"] >= 1
checks.append("assignments")
notes = get("/api/notes")
assert "items" in notes
checks.append("teacher follow-ups")
projects = get("/api/projects")
assert projects["total"] >= 1
project_id = projects["items"][0]["id"]
versions = get(f"/api/projects/{project_id}/versions")
assert "items" in versions
checks.append("Git-backed project and version API")
print(f"PASS: {len(checks)} smoke tests ({', '.join(checks)})")
