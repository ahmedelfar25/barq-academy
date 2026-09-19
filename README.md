<img src="assets/barq-logo.svg" alt="BARQ Systems" width="180">

# DevOps Internship Task - Starter v2

**Due date:** ____________________

**Time window:** 4 calendar days from the invitation email date/time.

Read [the task](assessment/TASK.md), then [the API contract](assessment/APPLICATION.md).
Everyone receives this same release. The environment is intentionally broken.
Hidden issue types and count are not disclosed. Investigate this project; do not replace it.

## Included

- Flask API, PostgreSQL, Redis, Docker and NGINX starter files.
- Three historical logs, a question template and documentation templates.
- App-only tests and a recorded challenge script.
- Unimplemented validation, failure-test and backup/restore placeholders.

Use synthetic lab accounts/data only. Supplied values are for this disposable exercise,
never for real services. Keep the lab on your local machine; do not expose it publicly.

## Before you start

- Linux or WSL2, Python 3.12, Git and Docker with Compose.
- Docker Desktop must use Linux containers. Run shell scripts in Linux/WSL.
- Suggested capacity: 2 CPU cores, 4 GB free RAM and 3 GB free disk, plus Docker overhead.
- Internet for first downloads and GitHub. No cloud account or paid registry required.
- Use a machine where container names app-01, app-02, nginx, postgres and redis are unused.
  Do not delete someone else's containers to free those names.
- Intended public port: 8080 before the video, 8090 after the live change.
  If either is occupied, ask the organizer for a documented workstation exception.

## Start

Clone the supplied Git bundle/repository. Keep both release commits and the v2 baseline tag.
Set your own Git name/email before making changes.

From the repository root:

```bash
git status
git log -2 --oneline
cp .env.example .env
docker version
docker compose version
docker compose -p barq-assessment up --build -d
docker compose -p barq-assessment ps -a
docker compose -p barq-assessment logs --no-color
```

The initial environment is not expected to pass. Record what actually happens.
The intended URL is http://127.0.0.1:8080; do not assume the starter configuration is correct.

App-only checks use fake dependencies, not real SQL/Redis or Docker networking:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Your work

- Complete [assessment/TASK.md](assessment/TASK.md).
- Implemented operational validation with `scripts/validate.sh`.
- Implemented backend failure/recovery testing with `failure_test.py`.
- Implemented PostgreSQL backup and restore with `scripts/backup.sh` and `scripts/restore.sh`.
- Added GitHub Actions CI in `.github/workflows/ci.yml`.
- Runtime secrets are supplied through `.env` and are not copied into application images.
- PostgreSQL and Redis use named volumes for persistence.
- Complete the root report templates and `docs/EVIDENCE_INDEX.md`.
- Add `architecture.png` or `architecture.pdf`.
- Keep backups, `.env`, virtual environments and challenge state out of Git.

## Recorded challenge

Use the supplied video_challenge.sh unchanged. Read its code if needed; do not run it early.
After repairing the environment, run it once, for the first time in the video working copy,
during the continuous 12-18 minute recording. The script requires healthy services, both
initial instances and the target network layout. Preflight failures make no runtime changes.

```bash
./video_challenge.sh
```

If you deliberately changed the project name, pass --project YOUR_PROJECT.
An organizer-approved alternate local URL can be passed with --url http://127.0.0.1:PORT.
The script touches only matching Compose-owned lab containers/networks.
Keep the receipt in .assessment/challenge.json for the evidence index. Do not delete the
one-run marker to retry. A local marker is not tamper-proof; ownership is judged from evidence.
Do not use docker compose down to reset the runtime challenge.

## Stop safely

Outside the recorded challenge, `docker compose -p barq-assessment down` stops this lab.

Do not use `--volumes` during persistence tests because the PostgreSQL and Redis named
volumes contain persistent state. Avoid global Docker prune/cleanup commands.

Back up anything you need before removing containers; investigate whether data actually
persists.

## Persistence test


Create a record:

```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"title":"Persistence after container recreation"}' \
  http://127.0.0.1:8080/records
```

Verify the record:

```bash
curl -s http://127.0.0.1:8080/records
```

Recreate the application and PostgreSQL containers while keeping the volumes:

```bash
docker compose up -d --force-recreate app-01 app-02 postgres
```

Verify the services are healthy:

```bash
docker compose ps
```

Verify the record survived container recreation:

```bash
curl -s http://127.0.0.1:8080/records
```

## Validation

Run the operational validation after starting the stack:

    ./scripts/validate.sh

The validation checks:

- All required containers are running and healthy.
- NGINX is exposed on the expected host port.
- Required API endpoints return successful responses.
- Both application instances report distinct instance identities.
- PostgreSQL records can be created and retrieved.
- Redis counter operations work.
- PostgreSQL, Redis and application containers are not unnecessarily exposed on host ports.
- Application containers run as the non-root `app` user.
- Application containers use a read-only filesystem.

A successful run ends with:

    VALIDATION PASSED

## Failure and Recovery Test

Run the controlled backend failure test:

    python3 failure_test.py

The test:

1. Stops `app-01`.
2. Sends requests through NGINX while `app-01` is unavailable.
3. Verifies that the remaining backend continues serving requests.
4. Restarts `app-01`.
5. Waits for the application health check.
6. Sends recovery traffic and verifies that both instances can serve requests.

The completed test passed with all 20 failure-period requests served by `app-02`, zero gateway errors, and successful recovery of `app-01`.

## Backup and Restore

Create a PostgreSQL backup:

    ./scripts/backup.sh

Backups are written to:

    backups/

The backup directory is ignored by Git.

Restore a backup into a prepared PostgreSQL database:

    ./scripts/restore.sh <backup-file> <database-name>

The restore workflow was verified using a separate test database.

## API Endpoints

The application exposes the following endpoints through NGINX:

- `/` - application response.
- `/health` - application health check.
- `/ready` - readiness check including dependencies.
- `/instance` - returns the application instance identity.
- `/records` - PostgreSQL-backed records.
- `/counter` - Redis-backed counter.

The application instances use distinct identities:

- `app-01`
- `app-02`

## Network and Port Exposure

The deployment uses two Docker networks:

- `frontend` - NGINX and application instances.
- `backend` - application instances, PostgreSQL and Redis.

The backend network is internal to Docker.

Only NGINX is exposed on the host:

    127.0.0.1:8080

The application containers, PostgreSQL and Redis do not publish host ports.

Service-to-service communication uses Docker Compose service names rather than fixed container IP addresses.

## Security Hardening

The application containers include the following hardening measures:

- Run as the non-root `app` user.
- Read-only root filesystem.
- Temporary writable filesystem only where required.
- `no-new-privileges`.
- All Linux capabilities dropped.
- CPU and memory limits.
- Health checks.
- Restart policy.
- Runtime configuration supplied through environment variables.
- Secrets are not copied into the application image.
- `.env` is excluded from Git.
- `.env.example` contains only safe lab placeholders.

## Persistence

PostgreSQL and Redis use named Docker volumes.

PostgreSQL persistence was verified by:

1. Creating a record.
2. Recreating `app-01`, `app-02` and `postgres`.
3. Querying `/records` again.
4. Confirming that the previously created record remained available.

The persistence test completed successfully.

## Documentation

Additional project documentation:

- [Troubleshooting journal](troubleshooting.md)
- [Historical log analysis](log_analysis.md)
- [Architecture decisions](decisions.md)
- [Security review](security_review.md)
- [AI usage](AI_USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Evidence index](docs/EVIDENCE_INDEX.md)

## Verification Summary

The repaired environment was verified with:

- `docker compose config -q`
- `scripts/validate.sh`
- `failure_test.py`
- PostgreSQL backup and restore
- PostgreSQL persistence after container recreation
- Application image secret check
- Git working-tree and repository checks

The validation, failure/recovery, backup/restore, and persistence workflows were completed successfully.
