import os
import time
from pathlib import Path

import pytest
import requests
from testcontainers.compose import DockerCompose


@pytest.fixture(scope="session")
def fess_service():
    project_root = Path(__file__).resolve().parent
    print(f"Project root: {project_root}")
    
    # Determine which compose file to use based on FESS_VERSION
    fess_version = os.getenv("FESS_VERSION", "15.7.0")
    if fess_version.startswith("15."):
        compose_file = "compose-fess15.yaml"
    else:
        compose_file = "compose-fess14.yaml"
    
    print(f"Using compose file: {compose_file} for Fess version: {fess_version}")
    compose = DockerCompose(str(project_root), compose_file, pull=True)
    compose.start()

    host = compose.get_service_host("fessctl_fess01", 8080)
    port = compose.get_service_port("fessctl_fess01", 8080)
    endpoint = f"http://{host}:{port}"

    timeout_seconds = 60
    start = time.time()
    # Fess 15.7+ serves the health check at /api/v2/health (the legacy /api/v1/health
    # was removed); earlier versions use /api/v1/health.
    try:
        major, minor, *_ = (int(p) for p in fess_version.split(".")[:2])
        is_api_v2 = (major, minor) >= (15, 7)
    except (ValueError, TypeError):
        is_api_v2 = False
    health_path = "/api/v2/health" if is_api_v2 else "/api/v1/health"
    health_url = f"{endpoint}{health_path}"
    while True:
        try:
            res = requests.get(health_url, timeout=1)
            if res.status_code == 200:
                break
        except requests.RequestException:
            pass
        if time.time() - start > timeout_seconds:
            pytest.skip(
                f"Fess did not become healthy within {timeout_seconds}s")
        time.sleep(1)
        print(".", end="")
    print("\nFess is healthy and ready for tests.")

    access_token = "CHANGEME"  # Placeholder for access token
    os.environ["FESS_ENDPOINT"] = endpoint
    os.environ["FESS_ACCESS_TOKEN"] = access_token
    yield {"endpoint": endpoint, "token": access_token}

    compose.stop()
