# Evidence and submission index

- Repository URL: https://github.com/ahmedelfar25/barq-academy
- Final commit: `2e597a9`
- Matching CI run: `Barq Assessment CI #4` — Passed
- Continuous 12-18 minute video URL: https://drive.google.com/file/d/1_OzhyuEBwTo9O4Sn1LUI3sWKJOS2EaMq/view?usp=sharing
- Challenge receipt ID: `799ed0b2a82948f29a804fa4f650d223`
- Starting video commit: `97edab8`
- Later documentation-only commits, if any: Pending

For each requirement, link: file/output -> commit -> video timestamp.

## Video evidence

| Requirement / video step | File/output | Commit | Video timestamp |
|---|---|---|---|
| Show repository, starting commit and clean Git status | Git repository, `git status`, `git log` | `97edab8` | 00:00 |
| Build and start the environment; show service health | `docker-compose.yml`, Docker Compose service status | `1d04486` , `97edab8` | 01:16 |
| Test `/`, `/health`, `/ready`, `/records` and `/counter` | Application endpoints | `1d04486` | 02:43 |
| Run operational validation | `scripts/validate.sh` | `1d04486`, `2e597a9` | 02:25 |
| Prove both initial backends serve repeated requests through NGINX | `/instance`, `nginx/nginx.conf` | `1d04486` | 03:56 |
| Stop one backend and show continued traffic/errors | Docker runtime commands and endpoint output | `1d04486` | 04:47 |
| Recover the backend and prove it serves again | Docker runtime commands and endpoint output | `1d04486` | 06:02 |
| Show a created record surviving application and PostgreSQL container recreation | PostgreSQL data, `README.md` | `ccd6ae3` | 06:36 |
| Demonstrate one historical-log finding | `log_analysis.md`, historical logs | `25564ec` | 09:53 |
| Run `./video_challenge.sh` for the first time in the recorded working copy | `video_challenge.sh`, challenge receipt | `97edab8` | 11:12 |
| Diagnose the challenge runtime fault | Docker runtime/network/readiness output | `97edab8` | 11:44 |
| Repair the runtime fault without `docker compose down` | Docker runtime/network repair | `97edab8` | 16:18 |
| Add `app-03` live | `docker-compose.yml`, `scripts/validate.sh` | `2e597a9` | 17:50 |
| Change public port from 8080 to 8090 | `.env`, `docker-compose.yml` | `2e597a9` | 19:18 |
| Prove all three application instances respond through NGINX | `/instance`, `scripts/validate.sh` | `2e597a9` | 23:10 |
| Rerun final validation | `scripts/validate.sh` | `2e597a9` | 28:36 |
| Show final `git status` and `git diff` | Git output | `2e597a9` | 31:23 |
| Show commit hashes and push the video commits | Git history / GitHub | `2e597a9` | 32:18 |

## Recorded challenge

- Challenge receipt ID: `799ed0b2a82948f29a804fa4f650d223`
- Starting video commit: `97edab8`
- Final technical commit: `2e597a9`
- Final public port: `8090`
- Final application instances: `app-01`, `app-02`, `app-03`

## Final validation evidence

- `./scripts/validate.sh` passed.
- `/`, `/health`, `/ready`, `/instance`, `/records` and `/counter` returned successful responses.
- `app-01`, `app-02` and `app-03` were observed through `/instance`.
- NGINX was exposed on `127.0.0.1:8090`.
- All required containers were healthy.

## Historical log evidence

- Time window: `11:05–11:09 UTC`
- 40 unique HTTP 502 responses.
- All 40 targeted `172.23.0.12:8080`.
- NGINX reported `Connection refused` while connecting to the upstream.
- 19 requests initially received a 502 from `172.23.0.12` and subsequently succeeded through `172.23.0.11`.
- Request IDs were used to avoid double-counting duplicated records.

## Submission notes

The final implementation uses three application instances behind NGINX with public port 8090.

The Evidence Index is updated after the recorded technical work as a documentation-only commit.
