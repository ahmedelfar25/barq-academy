# Evidence and submission index

- Repository URL: https://gitlab.com/barqsystems/barq-academy.git
- Final commit: Pending final submission
- Matching CI run: Pending final push
- Continuous 12-18 minute video URL: Pending recording
- Challenge receipt ID: Pending recorded challenge
- Starting video commit: Pending final challenge preparation
- Later documentation-only commits, if any: Pending

## Requirement evidence

| Requirement | Evidence | Commit |
|---|---|---|
| Dockerized Flask application | `Dockerfile`, `docker-compose.yml` | `1d04486` |
| Two application instances | `docker-compose.yml`, `scripts/validate.sh` | `1d04486` |
| NGINX reverse proxy | `nginx/nginx.conf`, `docker-compose.yml` | `1d04486` |
| Frontend/backend network separation | `docker-compose.yml` | `1d04486` |
| PostgreSQL integration | `app/`, `database/init.sql`, `docker-compose.yml` | `1d04486` |
| Redis integration | `app/`, `docker-compose.yml` | `1d04486` |
| Health/readiness checks | `/health`, `/ready`, Compose healthchecks | `1d04486` |
| Operational validation | `scripts/validate.sh` | `1d04486` |
| Backend failure/recovery test | `failure_test.py` | `6b7e9ab` |
| Persistence test | `README.md`, `docs/ARCHITECTURE.md` | `ccd6ae3` |
| PostgreSQL backup/restore | `scripts/backup.sh`, `scripts/restore.sh` | `1d04486` |
| Secrets removed from image/config | `.env.example`, `.gitignore`, `Dockerfile`, `docker-compose.yml` | `334afc7`, `023c004` |
| CI validation | `.github/workflows/ci.yml` | `d841446` |
| Historical log analysis | `log_analysis.md` | `25564ec` |
| Troubleshooting journal | `troubleshooting.md` | `a3a812b` |
| Technical decisions | `decisions.md` | `0f099a6` |
| Security review | `security_review.md` | `c84a0c8` |
| AI usage disclosure | `AI_USAGE.md` | `d744a79` |
| Architecture diagram | `architecture.png`, `docs/ARCHITECTURE.md` | `0602b77` |
| README documentation | `README.md` | `8d69b51` |

## Validation evidence

- `docker compose config -q` passed.
- `./scripts/validate.sh` passed.
- Required endpoints returned successful responses.
- Both application instances reported distinct identities.
- PostgreSQL records were created and retrieved successfully.
- Redis counter operations worked.
- Only NGINX was exposed on the host.
- Application containers ran as the non-root `app` user.
- Application containers used a read-only filesystem.
- `failure_test.py` passed with backend failure and recovery.
- PostgreSQL persistence survived application and database container recreation.
- PostgreSQL backup and restore were tested.

## Submission notes

The final submission must keep the repository, architecture diagram, documentation, CI configuration and recorded challenge evidence consistent with the final three-instance target state and public port 8090.

The current operational validation covers the repaired two-instance deployment. The recorded challenge will demonstrate the final live change to three application instances and port 8090.

The video URL, challenge receipt ID, matching CI run and final challenge commit should be filled after the recorded challenge is completed.
