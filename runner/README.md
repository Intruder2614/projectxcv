# Local isolated runner

The app intentionally does not execute submitted Python, Java, or C++ in the FastAPI process. Build this image if you want local code-run functionality:

```bash
docker build -t codingal-runner:local -f runner/Dockerfile runner
```

Each run uses a newly created container with no network, limited CPU/memory/PIDs, a read-only root filesystem, a non-root UID, dropped capabilities and temporary storage. This is a useful local pilot baseline, not a guarantee against all sandbox escapes. For production, isolate runner capacity in a separate account/subnet/service, consider hardened sandboxes or microVMs, test escape resistance, add central quotas and monitoring, and never pass production credentials to student workloads.
