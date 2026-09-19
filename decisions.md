# Technical decisions

## Decision 1
- Choice: Use NGINX as the single reverse proxy and load balancer in front of the Flask application instances.
- Why: The assessment requires a single public entry point and multiple application instances behind a reverse proxy.
- Alternative: Expose the Flask instances directly or use a different proxy.
- Trade-off: NGINX is a single point of failure in this lab topology, but it provides centralized routing and keeps the application containers unexposed to the host.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Run multiple NGINX instances behind a highly available load-balancing layer.

## Decision 2
- Choice: Separate Docker traffic into `frontend` and `backend` networks.
- Why: NGINX needs access to the application containers, while PostgreSQL and Redis should remain internal and accessible only by the application layer.
- Alternative: Put every service on one shared Docker network.
- Trade-off: The split network design adds configuration complexity but reduces unnecessary network reachability.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Apply additional network policies and segmentation at the infrastructure level.

## Decision 3
- Choice: Use named Docker volumes for PostgreSQL and Redis persistence.
- Why: Database and cache data should survive application and container recreation.
- Alternative: Store data only inside containers.
- Trade-off: Named volumes require explicit lifecycle management and backup procedures.
- Evidence / commit: `ccd6ae3` - document persistence test
- Production improvement: Use managed database/cache services or replicated persistent storage with tested disaster-recovery procedures.

## Decision 4
- Choice: Add container health checks and application health/readiness endpoints.
- Why: Container health status and application dependency readiness need to be observable before considering a service ready.
- Alternative: Rely only on process status or container startup completion.
- Trade-off: Health checks add configuration and repeated probes but provide better operational visibility.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Add centralized monitoring, alerting and service-level health dashboards.

## Decision 5
- Choice: Run application containers as a non-root user with a read-only root filesystem, dropped capabilities and `no-new-privileges`.
- Why: Reduce the impact of application compromise and limit unnecessary container privileges.
- Alternative: Run the application as the default container user with a writable filesystem.
- Trade-off: A read-only filesystem requires explicit writable locations such as `/tmp`, which can make some applications more restrictive to operate.
- Evidence / commit: `023c004` - remove secrets from image and compose
- Production improvement: Add image scanning, runtime security monitoring and stronger admission policies.

## Decision 6
- Choice: Supply runtime secrets and connection strings through environment variables instead of copying secret configuration into the application image.
- Why: Secrets should not be baked into the application image or source-controlled configuration.
- Alternative: Copy a secret configuration file into the image.
- Trade-off: Environment-based configuration still requires secure secret storage and injection in a real deployment.
- Evidence / commit: `334afc7` - move runtime secrets to environment; `023c004` - remove secrets from image and compose
- Production improvement: Use a dedicated secrets manager and short-lived credentials.

## Decision 7
- Choice: Pin container images by digest.
- Why: Digest pinning makes the lab deployment reproducible and prevents an image tag from silently changing between builds.
- Alternative: Use mutable image tags only.
- Trade-off: Digest pinning requires deliberate updates when newer images are approved.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Automate controlled dependency updates with image scanning and CI verification.

## Decision 8
- Choice: Use a minimal Python 3.12 slim base image pinned by digest for the application container.
- Why: A slim base reduces unnecessary packages and the pinned digest makes the build reproducible.
- Alternative: Use a full Python image or an unpinned mutable tag.
- Trade-off: A minimal image may require explicitly installing tools needed for diagnostics or health checks.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Continuously scan the image for vulnerabilities and rebuild it through a controlled image-update process.

## Decision 9
- Choice: Use container restart policies, bounded CPU/memory resources, and explicit health-check intervals, timeouts and retries.
- Why: Services should recover from unexpected container exits while resource limits prevent a single application instance from consuming unlimited host resources.
- Alternative: Rely on manual restarts and unlimited container resources.
- Trade-off: Automatic restarts can hide recurring application failures if monitoring and alerting are not present.
- Evidence / commit: `1d04486` - fix deployment and add operational validation
- Production improvement: Add centralized monitoring and alerts for repeated restarts, resource saturation and failed health checks.
