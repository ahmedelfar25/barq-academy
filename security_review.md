# Security and production-readiness review

## Finding 1 - Runtime secrets must not be baked into the image
- Risk and evidence: A tracked `config/app.env` file previously contained runtime configuration. Keeping secrets in an image or repository can expose credentials to anyone with access to the image or Git history.
- Impact: Database credentials and connection information could be disclosed and reused.
- Implemented fix / commit: Runtime configuration was moved to environment variables and the old application secret file was removed. Commits `334afc7` and `023c004`.
- Production follow-up: Use a dedicated secrets manager instead of `.env` files.
- How to verify: Confirm `config/app.env` is absent, `.env` is ignored, and inspect the image to ensure no `app.env` is present.

## Finding 2 - Unnecessary host port exposure
- Risk and evidence: Exposing application, PostgreSQL or Redis ports directly on the host would bypass the intended NGINX entry point.
- Impact: Internal services could become directly reachable and increase the attack surface.
- Implemented fix / commit: Only NGINX publishes the host port; application, PostgreSQL and Redis containers have no host port mappings. Commit `1d04486`.
- Production follow-up: Keep internal services on private networks and expose only explicitly required ingress endpoints.
- How to verify: Run `docker compose ps` and confirm only NGINX has a host port.

## Finding 3 - Application containers should not run as root
- Risk and evidence: Running the Flask application as root increases the potential impact of an application compromise.
- Impact: A container-level compromise could provide unnecessary privileges inside the container.
- Implemented fix / commit: The application image creates and uses the non-root `app` user. Commit `1d04486`.
- Production follow-up: Enforce non-root execution through deployment policy.
- How to verify: Run `docker compose exec app-01 id` and confirm the process runs as the `app` user.

## Finding 4 - Writable application filesystems increase tampering risk
- Risk and evidence: A fully writable root filesystem gives a compromised process more opportunity to modify application files or persist unwanted changes.
- Impact: An attacker could modify files inside the running container.
- Implemented fix / commit: Application containers use `read_only: true` with `/tmp` as a temporary writable filesystem. Commit `1d04486`.
- Production follow-up: Minimize writable paths further and use runtime security controls.
- How to verify: Inspect the Compose configuration and container mount configuration.

## Finding 5 - Excess Linux capabilities should be removed
- Risk and evidence: Containers do not require the default Linux capabilities for this Flask workload.
- Impact: Retaining unnecessary capabilities can increase the impact of container compromise.
- Implemented fix / commit: Application containers use `cap_drop: ALL` and `no-new-privileges:true`. Commit `1d04486`.
- Production follow-up: Apply equivalent restrictions through the production container platform.
- How to verify: Inspect the Compose configuration and container security options.

## Finding 6 - Network segmentation limits unnecessary service access
- Risk and evidence: Putting NGINX, application services, PostgreSQL and Redis on one shared network would allow broader lateral connectivity.
- Impact: A compromised application or proxy could potentially reach services that do not need to be directly accessible from that layer.
- Implemented fix / commit: `frontend` contains NGINX and applications; `backend` contains applications, PostgreSQL and Redis; the backend network is internal. Commit `1d04486`.
- Production follow-up: Add infrastructure-level network policies and explicit service-to-service allow rules.
- How to verify: Run `docker network inspect` and confirm the expected service membership.

## Finding 7 - Resource exhaustion needs explicit limits
- Risk and evidence: Application containers without CPU or memory limits could consume excessive host resources during abnormal load.
- Impact: One application instance could degrade other services or the entire lab environment.
- Implemented fix / commit: Application containers have a 256 MB memory limit and 0.50 CPU limit. Commit `1d04486`.
- Production follow-up: Tune limits from production metrics and configure alerts for sustained resource saturation.
- How to verify: Inspect the Compose configuration and container resource settings.

## Finding 8 - Service failure requires health and recovery checks
- Risk and evidence: A running process is not sufficient evidence that an application is ready to serve dependency-backed requests.
- Impact: Traffic could be sent to an unhealthy instance or a dependency failure could remain undetected.
- Implemented fix / commit: Health checks, `/health`, `/ready`, validation checks and the backend failure/recovery test were implemented. Commits `1d04486` and `6b7e9ab`.
- Production follow-up: Add centralized monitoring and alerting for health-check failures and repeated recovery events.
- How to verify: Run `./scripts/validate.sh` and `python3 failure_test.py`.

## Finding 9 - Persistent data requires backup and restore procedures
- Risk and evidence: Named volumes provide persistence across container recreation but do not by themselves provide backup or disaster recovery.
- Impact: Data could still be lost if the underlying Docker storage is deleted or corrupted.
- Implemented fix / commit: PostgreSQL backup and restore scripts were added and a restore workflow was tested. Commit `1d04486`.
- Production follow-up: Store backups outside the Docker host, encrypt them, retain multiple recovery points and test restoration regularly.
- How to verify: Run `./scripts/backup.sh` and restore a generated dump into a test database.

## Finding 10 - Redis persistence is not equivalent to a highly available cache
- Risk and evidence: Redis uses a named volume and append-only persistence, but the lab has a single Redis instance.
- Impact: Redis service failure remains a single point of failure and persistence alone does not provide high availability.
- Implemented fix / commit: Redis persistence is configured through the named `redis-data` volume and AOF mode. Commit `1d04486`.
- Production follow-up: Use a managed or replicated Redis deployment when cache availability is business-critical.
- How to verify: Inspect the Redis volume and persistence configuration and perform a controlled container recreation.

## Finding 11 - Logging is useful but not sufficient for production monitoring
- Risk and evidence: The supplied historical logs provide request IDs, statuses, upstream information and dependency errors, but they do not provide full infrastructure metrics or distributed tracing.
- Impact: Some root causes may remain ambiguous during a live incident.
- Implemented fix / commit: Historical logs were correlated in `log_analysis.md`, and troubleshooting evidence was recorded in `troubleshooting.md`. Commits `25564ec` and `a3a812b`.
- Production follow-up: Add centralized log aggregation, metrics, alerting and distributed tracing.
- How to verify: Correlate request IDs across proxy and application logs and verify that alerts are generated for dependency and availability failures.

## Finding 12 - NGINX is a single point of failure in the lab topology
- Risk and evidence: The final architecture has one NGINX entry point in front of the application instances.
- Impact: NGINX failure would make the application inaccessible even if the Flask instances remain healthy.
- Implemented fix / commit: Documented as an intentional lab limitation in `architecture.png` and `docs/ARCHITECTURE.md`.
- Production follow-up: Deploy redundant ingress/reverse-proxy instances behind a highly available load-balancing layer.
- How to verify: Review the architecture diagram and perform a controlled NGINX failure test in an environment where such testing is permitted.

## Finding 13 - Image selection and supply-chain control
- Risk and evidence: Using large or mutable container images can increase the attack surface and make deployments less reproducible.
- Impact: Unnecessary packages may introduce additional vulnerabilities, while mutable tags can change the deployed software without a corresponding source change.
- Implemented fix / commit: The application uses a Python 3.12 slim base image pinned by digest, and service images are also pinned by digest. Commit `1d04486`.
- Production follow-up: Use approved minimal images, scan images for vulnerabilities and update pinned digests through a controlled CI process.
- How to verify: Inspect `Dockerfile` and `docker-compose.yml` and confirm the expected image tags and digests are pinned.
