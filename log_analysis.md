# Log analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?
2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?
3. What are the final client status counts and error rate? State your denominator.
4. Which paths, time windows and backends account for the failures?
5. What are the median and p95 client latencies? State the percentile method and units.
6. Which requests retried upstream? How many succeeded after retrying?
7. Build an incident timeline using evidence from access, error AND application logs.
8. Show one correlated failed request and one successful request. Include IDs and timestamps.
9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?
10. What do the logs not prove? What would you check next in a running environment?

## Commands / scripts

The three supplied logs were analyzed with Python/Bash processing.
Basic file and line checks:
wc -l logs/access.log logs/error.log logs/application.log
Request-ID deduplication was performed using the `request_id` field. For access-log request counts, the first record for each request ID was retained so retries represented by multiple upstreams were not counted as multiple client requests.
Latency was calculated from the access-log `request_time` field in seconds.
Application latency was calculated from the application-log `duration_ms` field in milliseconds.
Cross-log correlation used:
request_id
timestamp
status
path
upstream
upstream_status
instance_id
dependency
error_type

## Results

### 1. UTC interval and line quality

The supplied logs cover approximately:
2026-08-20 11:00:00 UTC
to
2026-08-20 11:30:00 UTC
The access log contains:
725 total JSON records
720 unique request IDs
5 duplicate request IDs / extra records
0 malformed JSON records
The application log contains:
1458 JSON records
1364 http_request records
94 dependency_error records
680 unique request IDs associated with the application records
For the `http_request` events:
1364 total http_request records
680 unique request IDs
684 extra http_request records associated with repeated request IDs
For dependency errors:
94 dependency_error records
47 unique dependency-error request IDs
47 extra dependency-error records
The NGINX error log contains:
68 text log entries
67 error entries
1 notice entry
0 malformed NGINX log lines
The final notice was:
2026/08/20 11:30:00 [notice] log collector rotated stream
The three logs therefore require different parsing rules: the access and application logs are JSON, while the NGINX error log is plain text.

### 2. Distinct client requests and deduplication

The final access-log request count is:
720 distinct client requests
The raw access log contained 725 records.
Five request IDs occurred more than once:
lab-000121
lab-000241
lab-000361
lab-000481
lab-000601
Therefore:
725 raw access records

- 5 duplicate records
  \= 720 distinct client requests

Retries were not counted as additional client requests. Requests containing multiple upstream attempts were identified from values such as:
upstream_status: "502, 200"
upstream: "172.23.0.12:8080, 172.23.0.11:8080"
The final client request count uses the unique `request_id` as the denominator.

### 3. Final client status counts and error rate

After deduplicating by request ID:
200 = 615
502 = 40
503 = 47
504 = 8
404 = 10
Total = 720
Server-error responses:
502 + 503 + 504 = 95
Server-error rate:
95 / 720 = 13.19%
Non-2xx responses including the 404 responses:
40 + 47 + 8 + 10 = 105
105 / 720 = 14.58%
The primary server-error denominator is therefore 720 distinct client requests.

### 4. Paths, time windows and backends responsible for failures

#### Incident 1 — upstream connection failures

Time window:
11:05–11:09 UTC
There were:
40 unique 502 responses
All 40 targeted:
172.23.0.12:8080
Path distribution:
/health   = 10
/records  = 10
/counter  = 10
/         = 10
The NGINX error log reports:
connect() failed (111: Connection refused) while connecting to upstream
The other backend continued serving requests.
There were also 19 requests that initially received a 502 from `172.23.0.12` and then succeeded through `172.23.0.11`.

#### Incident 2 — Redis dependency failures

Time window:
11:12–11:15 UTC
There were:
31 unique Redis dependency failures
The application logs identify:
dependency = redis
error_type = TimeoutError
Corresponding client responses were `503`.
Distribution by minute:
11:12 = 8
11:13 = 7
11:14 = 8
11:15 = 8
The corresponding 503 paths were:
/ready    = 23
/counter  = 16
/records  = 8

#### Incident 3 — PostgreSQL authentication failures

Time window:
11:20–11:21 UTC
There were:
16 unique PostgreSQL dependency failures
The application logs identify:
dependency = postgres
error_type = InvalidPassword
Corresponding client responses were `503`.
Distribution:
11:20 = 8
11:21 = 8

#### Incident 4 — upstream response timeouts

Time window:
11:25–11:26 UTC
There were:
8 unique 504 responses
All were:
GET /records
Backend distribution:
172.23.0.11:8080 = 4
172.23.0.12:8080 = 4
NGINX reported:
upstream timed out (110: Operation timed out)
while reading response header from upstream
The access-log request time was approximately:
2.001 seconds
while the corresponding application requests eventually logged approximately:
2700 ms

### 5. Median and p95 client latency

Client latency was taken from the access-log `request_time` field.
Units:
seconds in the source log
For the 720 unique requests:
Median = 0.054 seconds = 54 ms
p95    = 2.001 seconds = 2001 ms
The percentile method used is nearest-rank:
rank = ceil(0.95 × N)
For:
N = 720
the p95 value is the value at:
ceil(0.95 × 720) = 684
after sorting the latency values.
The high client p95 is driven by the 2.001-second NGINX timeout requests during the `/records` incident.
For comparison, application `http_request` durations after request-ID deduplication were:
Median = 57 ms
p95    = 2025 ms
The application logs also contain the slow `/records` requests with approximately `2700 ms` duration.

### 6. Upstream retries

There were:
19 requests with multiple upstream attempts
They show:
upstream_status = "502, 200"
and:
upstream = "172.23.0.12:8080, 172.23.0.11:8080"
All 19 eventually succeeded.
Therefore:
19 retried requests
19 succeeded after retrying
0 remained failed after the retry
These requests were counted once in the 720-client-request denominator.

### 7. Incident timeline

| Time UTCEvidenceObservation |                      |                                                                                                        |
| --------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------ |
| 11:05–11:09                 | Access + NGINX error | 40 unique `502` responses; connection refused to `172.23.0.12:8080`                                    |
| 11:05–11:09                 | Access               | 19 requests show `502, 200` upstream status and succeed through the other backend                      |
| 11:12–11:15                 | Application + access | 31 Redis `TimeoutError` dependency failures corresponding to `503` responses                           |
| 11:20–11:21                 | Application + access | 16 PostgreSQL `InvalidPassword` dependency failures corresponding to `503` responses                   |
| 11:25–11:26                 | Access + NGINX error | 8 `504` `/records` requests due to upstream response timeout                                           |
| 11:25–11:26                 | Application          | Corresponding `/records` requests eventually logged status `200` with approximately `2700 ms` duration |
| 11:30                       | NGINX error log      | Log collector rotated the stream                                                                       |

### 8. Correlated failed and successful requests

#### Failed request

Request:
request_id = lab-000606
Access log:
timestamp    = 2026-08-20T11:25:14.501Z
path         = /records
status       = 504
upstream     = 172.23.0.12:8080
request_time = 2.001
NGINX error log:
2026/08/20 11:25:14
upstream timed out (110: Operation timed out)
while reading response header from upstream
request_id=lab-000606
Application log:
timestamp   = 2026-08-20T11:25:15.200Z
request_id  = lab-000606
instance_id = app-02
path        = /records
status      = 200
duration_ms = 2700
This shows that NGINX returned the `504` before the application completed its approximately 2700 ms operation.

#### Successful request

Request:
request_id = lab-000123
Access log:
timestamp    = 2026-08-20T11:05:05.089Z
path         = /health
status       = 200
upstream     = 172.23.0.11:8080
request_time = 0.089
Application log:
timestamp   = 2026-08-20T11:05:05.089Z
request_id  = lab-000123
instance_id = app-01
path        = /health
status      = 200
duration_ms = 89.0
This request succeeded normally through the healthy backend.

### 9. Proxy/connectivity versus dependency/application issues

#### Proxy/connectivity evidence

The `502` incident is supported by NGINX errors:
connect() failed (111: Connection refused) while connecting to upstream
The access log identifies:
status = 502
upstream = 172.23.0.12:8080
This is evidence of an upstream connection failure observed by NGINX.
The `504` incident is supported by:
upstream timed out (110: Operation timed out)
while reading response header from upstream
The access log shows approximately:
request_time = 2.001 seconds
status = 504

#### Dependency/application evidence

The Redis failures are explicitly recorded by the application as:
dependency = redis
error_type = TimeoutError
The PostgreSQL failures are explicitly recorded as:
dependency = postgres
error_type = InvalidPassword
Both groups correspond to client-facing `503` responses.
The logs therefore provide direct evidence for separate proxy/connectivity and dependency-level failure classes.

### 10. What the logs do not prove

The logs do not prove the deeper infrastructure cause behind every failure.
For example:

- The `502` logs prove that NGINX could not connect to `172.23.0.12:8080`, but they do not prove why that backend refused the connection.
- The Redis logs prove `TimeoutError`, but they do not by themselves prove the underlying Redis/network/resource cause.
- The PostgreSQL logs prove `InvalidPassword`, but they do not prove which configuration change or credential source caused the mismatch.
- The `504` logs prove that NGINX timed out while waiting for the upstream response. The application later logged `200` after approximately 2700 ms, but the supplied logs do not prove why `/records` took that long.
- The historical logs describe the supplied test dataset and do not establish the current runtime state of the repaired environment.

In a running environment, I would check:
docker compose ps
docker compose logs nginx app-01 app-02 postgres redis
docker inspect app-01 app-02 postgres redis
docker stats
docker network inspect barq-assessment_frontend
docker network inspect barq-assessment_backend
For the dependency incidents I would additionally check Redis and PostgreSQL connectivity, credentials/environment variables, container health, resource usage, and network connectivity.

## Timeline and correlated examples

The main incident sequence is:
11:05–11:09  -> 40 x 502
NGINX connection refused to app-02
11:12–11:15  -> 31 x 503
Redis TimeoutError
11:20–11:21  -> 16 x 503
PostgreSQL InvalidPassword
11:25–11:26  -> 8 x 504
/records upstream timeout
application later logged \~2700 ms / 200
11:30        -> log collector rotated stream
The complete correlation method uses:
request_id + timestamp + status + path + upstream + application instance
This prevents retries and duplicate log records from being mistaken for additional client requests.

## Conclusions and limits

The supplied logs contain 720 distinct client requests.
The deduplicated client status distribution is:
200 = 615
502 = 40
503 = 47
504 = 8
404 = 10
The server-error rate is:
95 / 720 = 13.19%
The most significant observed failure classes were:
502 -> upstream connection refusal
503 -> Redis timeout / PostgreSQL authentication failure
504 -> upstream response timeout on /records
The logs also show 19 upstream retries that all eventually succeeded.
The analysis uses request IDs to correlate the three log sources and avoid double-counting duplicate records and retries.
The historical logs are evidence of the supplied test scenarios only. They do not prove the current runtime state or the deeper root cause of failures that are not directly recorded in the logs.
