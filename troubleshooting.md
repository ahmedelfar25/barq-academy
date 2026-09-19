# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry 1 / 2026-09-19 / Runtime configuration and secrets
- Symptom: The application configuration contained runtime database and Redis connection settings that needed to be kept outside the application image and Compose source.
- Hypothesis: Runtime secrets/configuration should be supplied through environment variables rather than copied into the image.
- Command or test:
  - `cat .env.example`
  - `docker compose config -q`
  - `docker compose up -d --build`
  - `docker run --rm barq-assessment-app-01 sh -c 'test ! -e /srv/config/app.env && echo "PASS: no app.env in image"'`
  - `git check-ignore -v .env`
- Actual output:
  - `docker compose config -q` completed successfully.
  - Container image check returned `PASS: no app.env in image`.
  - `.env` was ignored by `.gitignore`.
- Failed attempt and what changed your thinking: No failed runtime attempt was recorded for this investigation. This was a proactive security correction based on the assessment requirement to keep secrets out of images, code, and Compose.
- Root cause: Runtime configuration had previously been represented by a file that was not appropriate to include in the application image.
- Fix: Moved runtime database and Redis configuration to environment variables, added safe placeholder values to `.env.example`, removed `config/app.env` from the repository, and verified that the application image does not contain the file.
- Retest evidence: `docker compose config -q` passed, the application image check confirmed that `app.env` is absent, and the running stack passed `scripts/validate.sh`.
- Related commit: `334afc7` and `023c004`
- Remaining uncertainty: The removed secret file remains present in Git history because it existed in an earlier commit. Repository-history rewriting was not performed.

## Entry 2 / 2026-09-19 / PostgreSQL backup and restore
- Symptom: The backup/restore workflow needed to be verified using the PostgreSQL database running in the Compose stack.
- Hypothesis: A PostgreSQL custom-format dump created with `pg_dump -Fc` should be restorable with `pg_restore`.
- Command or test:
  - `./scripts/backup.sh`
  - An initial restore verification attempted to connect to a test database before that database existed.
  - `docker exec postgres psql -U barq_app -d postgres -c "CREATE DATABASE barq_tasks_restore_test;"`
  - `./scripts/restore.sh <backup-file> barq_tasks_restore_test`
  - Query the restored database to verify the application data.
- Actual output:
  - The initial verification attempt returned:
    `FATAL: database "barq_tasks_restore_test" does not exist`
  - After creating the test database, the restore completed successfully.
  - Backup files were created under `backups/`.
- Failed attempt and what changed your thinking: The first restore verification failed because the target database had not been created. This showed that the restore verification needed an explicit target-database creation step before calling `pg_restore`.
- Root cause: The restore target database did not exist.
- Fix: Created the restore test database before running the restore command and then verified the restored contents.
- Retest evidence: `scripts/backup.sh` produced PostgreSQL dump files and `scripts/restore.sh` successfully restored the dump into the test database.
- Related commit: `1d04486`
- Remaining uncertainty: The backup files are intentionally ignored by Git and are local evidence rather than repository artifacts.

## Entry 3 / 2026-09-19 / PostgreSQL persistence after container recreation
- Symptom: The assessment required proof that application data survives recreation of application and PostgreSQL containers.
- Hypothesis: The named PostgreSQL volume should preserve database data independently of the PostgreSQL container lifecycle.
- Command or test:
  - `curl -s -X POST -H 'Content-Type: application/json' -d '{"title":"Persistence after container recreation"}' http://127.0.0.1:8080/records`
  - `curl -s http://127.0.0.1:8080/records`
  - `docker volume ls | grep barq`
  - `docker compose up -d --force-recreate app-01 app-02 postgres`
  - `curl -s http://127.0.0.1:8080/records`
  - `./scripts/validate.sh`
- Actual output:
  - The new record was created successfully with ID `4`.
  - `/records` returned the new record before recreation.
  - Named volumes included `barq-assessment_postgres-data` and `barq-assessment_redis-data`.
  - After recreating `app-01`, `app-02`, and `postgres`, the same record remained available.
  - `scripts/validate.sh` passed and reported `records=4`.
- Failed attempt and what changed your thinking: No failed attempt was recorded. The test was designed as a controlled persistence verification.
- Root cause: Not applicable; the persistence mechanism behaved as expected.
- Fix: Not applicable. The existing named PostgreSQL volume provided persistence across container recreation.
- Retest evidence: Record ID `4` remained available after container recreation and the full validation script passed.
- Related commit: `1d04486`
- Remaining uncertainty: This test verifies persistence across container recreation, not destruction of the named volume.

## Entry 4 / 2026-09-19 / Backend failure and recovery
- Symptom: The assessment required a controlled backend failure test to verify that the service remains available and recovers when a backend container is restored.
- Hypothesis: With two application instances behind NGINX, stopping one backend should still allow requests to be served by the remaining healthy backend.
- Command or test:
  - `python3 failure_test.py`
  - The test stopped `app-01`, generated 20 requests, started `app-01` again, waited for it to become healthy, and generated another 20 requests.
- Actual output:
  - During failure:
    - `total_requests=20`
    - `successful_requests=20`
    - `gateway_errors=0`
    - `other_responses=0`
    - `app-02_responses=20`
  - After recovery:
    - `total_requests=20`
    - `successful_requests=20`
    - `recovery_errors=0`
    - `app-01_responses=10`
    - `app-02_responses=10`
  - Final result: `FAILURE TEST PASSED`
- Failed attempt and what changed your thinking: The test reported `WARNING: no gateway errors observed during failure.` This was not a test failure. It demonstrated that NGINX continued routing requests to the surviving backend instead of exposing the stopped backend failure to the client.
- Root cause: `app-01` was intentionally stopped as part of the controlled failure test.
- Fix: Restarted `app-01` and waited for its health check to report healthy before validating recovery traffic.
- Retest evidence: All 20 requests during the failure were successfully served by `app-02`. After recovery, both `app-01` and `app-02` served requests and there were zero recovery errors.
- Related commit: `6b7e9ab`
- Remaining uncertainty: This test demonstrates recovery from loss of one application container; it does not test simultaneous failure of both application instances or failure of NGINX itself.

## Entry 5 / 2026-09-19 / Historical log correlation and duplicate request IDs
- Symptom: The supplied access and application logs contained repeated request IDs, so counting raw log lines could overstate the number of distinct client requests and dependency failures.
- Hypothesis: Request IDs should be used as the correlation key and duplicate request IDs should not be counted as separate client requests.
- Command or test:
  - Analyze `logs/access.log`, `logs/error.log`, and `logs/application.log` with Bash/Python processing.
  - Compare total log entries with unique request IDs.
  - Correlate access status codes with application dependency errors and NGINX error messages.
- Actual output:
  - Access log: 725 entries and 720 unique request IDs.
  - Five request IDs appeared more than once in the access log.
  - Application log: 1364 `http_request` entries but 680 unique request IDs.
  - There were 94 dependency-error log lines representing 47 unique dependency-error request IDs.
  - Unique access status counts were:
    - `200`: 615
    - `503`: 47
    - `502`: 40
    - `404`: 10
    - `504`: 8
  - The 47 unique dependency failures matched the 47 unique HTTP `503` responses.
- Failed attempt and what changed your thinking: Raw-line counting was not used as the final request denominator because repeated request IDs were present. The correlation analysis showed that unique request IDs provide a more accurate basis for request and incident counts.
- Root cause: The supplied logs contain duplicate log records for some requests.
- Fix: Used request IDs for deduplication and correlated the three log sources using those IDs and timestamps.
- Retest evidence: The deduplicated access-log status counts and dependency-error counts aligned, including 47 unique dependency failures corresponding to 47 unique `503` responses.
- Related commit: N/A - analysis/documentation work
- Remaining uncertainty: The logs show correlation between request IDs, proxy errors, and dependency errors, but they do not prove causes that are not directly represented in the logs.

## Entry 6 / 2026-09-19 / Historical NGINX and application incidents
- Symptom: The supplied logs contained several distinct failure periods that needed to be separated into proxy/connectivity failures, dependency failures, and slow upstream responses.
- Hypothesis: Correlating access, NGINX error, and application logs by request ID and timestamp would distinguish the failure classes.
- Command or test:
  - Correlate `logs/access.log`, `logs/error.log`, and `logs/application.log`.
  - Group failures by status code, timestamp, upstream, dependency, and request ID.
- Actual output:
  - At approximately `11:05–11:09`, there were 40 unique `502` responses, all targeting `172.23.0.12:8080`. NGINX reported `connect() failed (111: Connection refused) while connecting to upstream`.
  - At approximately `11:12–11:15`, there were 31 unique Redis dependency failures with `TimeoutError`, corresponding to `503` responses.
  - At approximately `11:20–11:21`, there were 16 unique PostgreSQL dependency failures with `InvalidPassword`, corresponding to `503` responses.
  - At approximately `11:25–11:26`, there were 8 unique `504` responses for `/records`. NGINX reported `upstream timed out (110: Operation timed out) while reading response header from upstream`.
  - Correlated application entries for the `504` requests recorded successful application responses with approximately 2700 ms duration, while NGINX had already timed out after approximately 2 seconds.
- Failed attempt and what changed your thinking: The log evidence showed that the `504` responses should not be classified as application-level `5xx` responses simply because the application log later recorded status `200`. The timestamps demonstrated that NGINX timed out before the application response was completed.
- Root cause: The supplied logs demonstrate different failure classes: refused upstream connections, Redis timeouts, PostgreSQL authentication failures, and upstream response timeouts. The exact underlying cause of the slow application operation is not proven by the supplied logs.
- Fix: No runtime fix was applied to the historical incidents. They were analyzed and classified using the supplied evidence.
- Retest evidence: Cross-log correlation by request ID and timestamp produced consistent incident windows and failure classifications.
- Related commit: N/A - analysis/documentation work
- Remaining uncertainty: The historical logs alone cannot establish the deeper cause of the slow `/records` responses or identify why the Redis and PostgreSQL dependency failures occurred beyond the logged error types.

Do not fabricate a failed attempt just to fill the template. Record actual attempts only.
