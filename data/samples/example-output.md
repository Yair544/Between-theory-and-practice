# Incident postmortem (DRAFT): Checkout failures after v2.4.1

> **This is a draft produced by IncidentIQ, not a reviewed postmortem.**
> The root cause below has *not* been confirmed. Every hypothesis needs its
> recommended test run before any of this is treated as settled.

- Generated: 2026-08-03T08:26:02+00:00
- Engine: gemini / gemini-2.5-flash
- Evidence items: 59
- Grounding: 100% of checkable claims cite valid evidence

## Summary

Starting around 10:15 UTC, approximately one-third of checkout attempts are failing with generic errors, and successful payments are slow. This critical incident began shortly after the v2.4.1 release at 10:02 UTC, which introduced a pooled client and retry logic for payment gateway calls. While payment gateway latency was already increasing before the deployment, the new changes appear to have caused connection pool exhaustion and read timeouts, leading to customer-facing 'card declined' messages and reported double charges. The exact interplay between the deployment and the external payment provider's performance remains under investigation.

Evidence: `[E1, E4, E5, E8, E12, E41, E42, E43, E44, E51, E52, E55, E57]`

### For non-technical readers

**Manager:** Starting around 10:15 AM UTC, about one-third of customer checkouts are failing, resulting in error messages like 'card declined' and very slow transaction times. This began shortly after a software update (v2.4.1) to our checkout system. Evidence suggests the issue stems from slow responses from our payment processing partner, which is now exacerbated by the new update's handling of these delays. Customers are experiencing significant disruption, including some being charged multiple times.

**Support:** We are aware of an issue affecting checkout, causing some transactions to fail or take a long time to complete. Customers may see 'card declined' messages even if their card is valid. Our engineering team is actively investigating and working to resolve this as quickly as possible. Please advise customers to try again later if possible, and we will update you as soon as we have more information.

## Timeline

| Time | Event | Source | Evidence |
|---|---|---|---|
| 2026-05-02T09:47:12+00:00 | 2026-05-02T09:47:12Z INFO  payment-client  gateway call completed status=200 duration=1180ms | observed | E2, E3 |
| 2026-05-02T09:58:03+00:00 | 2026-05-02T09:58:03Z WARN  payment-client  gateway call slow status=200 duration=3890ms | observed | E4 |
| 2026-05-02T10:02:11+00:00 | 2026-05-02T10:02:11Z INFO  deploy          release v2.4.1 rolled out to 6/6 pods | observed | E5 |
| 2026-05-02T10:04:55+00:00 | 2026-05-02T10:04:55Z WARN  payment-client  gateway call slow status=200 duration=4420ms | observed | E6, E7 |
| 2026-05-02T10:11:00+00:00 | Payment Gateway Latency Critical | inferred | E43 |
| 2026-05-02T10:14:03+00:00 | 2026-05-02T10:14:03Z ERROR payment-client  gateway call failed: read timeout after 5000ms attempt=1/3 | observed | E8, E9, E10 |
| 2026-05-02T10:14:13+00:00 | 2026-05-02T10:14:13Z ERROR checkout        order 88213 failed: PaymentGatewayTimeout | observed | E11 |
| 2026-05-02T10:15:02+00:00 | 2026-05-02T10:15:02Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E12, E13, E14, E15 |
| 2026-05-02T10:15:41+00:00 | 2026-05-02T10:15:41Z ERROR checkout        order 88231 failed: PaymentGatewayTimeout | observed | E16 |
| 2026-05-02T10:16:02+00:00 | 2026-05-02T10:16:02Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E17, E18 |
| 2026-05-02T10:16:28+00:00 | 2026-05-02T10:16:28Z INFO  payment-client  gateway call completed status=200 duration=4910ms | observed | E19 |
| 2026-05-02T10:16:44+00:00 | 2026-05-02T10:16:44Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E20, E21, E22 |
| 2026-05-02T10:17:29+00:00 | 2026-05-02T10:17:29Z ERROR checkout        order 88240 failed: PaymentGatewayTimeout | observed | E23 |
| 2026-05-02T10:17:52+00:00 | 2026-05-02T10:17:52Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E24 |
| 2026-05-02T10:18:06+00:00 | 2026-05-02T10:18:06Z WARN  payment-pool    active=10 idle=0 pending=23 maxPoolSize=10 | observed | E25 |
| 2026-05-02T10:18:31+00:00 | 2026-05-02T10:18:31Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E26, E27, E28 |
| 2026-05-02T10:19:22+00:00 | 2026-05-02T10:19:22Z WARN  payment-pool    active=10 idle=0 pending=39 maxPoolSize=10 | observed | E29 |
| 2026-05-02T10:19:44+00:00 | 2026-05-02T10:19:44Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E30 |
| 2026-05-02T10:20:01+00:00 | 2026-05-02T10:20:01Z INFO  payment-client  gateway call completed status=200 duration=5120ms | observed | E31 |
| 2026-05-02T10:20:18+00:00 | 2026-05-02T10:20:18Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E32, E33, E34, E35 |
| 2026-05-02T10:22:03+00:00 | 2026-05-02T10:22:03Z WARN  payment-pool    active=10 idle=0 pending=47 maxPoolSize=10 | observed | E36 |
| 2026-05-02T10:22:31+00:00 | 2026-05-02T10:22:31Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E37, E38 |
| 2026-05-02T10:23:40+00:00 | 2026-05-02T10:23:40Z INFO  inventory       stock reservation ok sku=A-4471 duration=42ms | observed | E39 |
| 2026-05-02T10:24:11+00:00 | 2026-05-02T10:24:11Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms | observed | E40 |

## What we know

- Checkout attempts began failing around 10:15 UTC, affecting approximately one-third of transactions, with successful payments being slow. `[E1, E44]`
- Release v2.4.1 was deployed to all 6 pods at 10:02 UTC. `[E5, E49]`
- v2.4.1 replaced the per-request HTTP client for the payment gateway with a pooled client (HikariCP-backed, maxPoolSize=10, connectionTimeout=30s). `[E51]`
- v2.4.1 added retry logic with 3 attempts and a 5-second per-attempt read timeout on payment gateway calls. `[E52, E41]`
- Payment gateway call durations were increasing before the v2.4.1 deployment, from 1.1s at 09:47 to 3.8s at 09:58. `[E2, E3, E4, E43]`
- After deployment, gateway call durations continued to be high, reaching 4.8s at 10:09 before the first read timeouts. `[E6, E7, E43]`
- The `payment-client` started logging `read timeout after 5000ms` errors for gateway calls from 10:14:03. `[E8, E9, E10]`
- The checkout service logs `PaymentGatewayTimeout` errors, indicating no response from `gateway.acme-pay.com` within 5000ms. `[E11, E16, E23, E41]`
- The `HikariPool-payment` started logging `Connection is not available, request timed out after 30000ms` errors from 10:15:02. `[E12, E42]`
- The `payment-pool` reports `active=10`, `idle=0`, and an increasing number of `pending` requests (23, 39, 47). `[E25, E29, E36, E46]`
- Customer reports include 'card declined' complaints, slow checkout processes (30 seconds), double charges, and successful checkouts after multiple attempts. `[E1, E55, E56, E57, E58]`
- A merchant partner using the same payment provider reports their own checkout is also slow. `[E59]`
- Database connections are nominal, and all checkout pods are passing readiness checks. `[E47, E48]`

## What we are assuming

- **The 'payment-client' logs and 'HikariPool-payment' logs refer to the `PooledGatewayClient` introduced in v2.4.1.**
  - Why: The naming conventions and timing align closely with the deployment notes of v2.4.1, which specify a pooled client.
  - To verify: Confirm the logging configuration and code paths for the `payment-client` and HikariPool within the deployed v2.4.1 service.
- **The 'generic error' and 'card declined' customer complaints are directly caused by the observed `PaymentGatewayTimeout` and `HikariPool-payment` errors.**
  - Why: The customer experiences match the nature of the internal errors, where payment processing fails or times out.
  - To verify: Correlate customer support tickets with specific internal error logs for individual transactions, if possible, or reproduce the customer experience with failed payments.

## Candidate root causes

Ranked by how much of the evidence each one accounts for. **None is confirmed.**

### 1. v2.4.1 deployment's pooled client and retry logic exhaust connections due to increasing upstream gateway latency.

*Confidence: 75% (well supported)*

The v2.4.1 release introduced a pooled client with a small `maxPoolSize` of 10 and retry logic with a 5-second per-attempt read timeout. The payment gateway was already experiencing increasing latency before the deployment. When gateway call durations approached or exceeded the 5-second timeout, the retry mechanism caused multiple attempts for a single transaction, each consuming a pool connection for at least 5 seconds. This quickly exhausted the small connection pool, leading to `Connection is not available` errors after the 30-second `connectionTimeout` and subsequent `PaymentGatewayTimeout` failures for users.

- Evidence for: `[E1, E4, E5, E6, E7, E8, E9, E10, E11, E12, E19, E25, E29, E31, E36, E41, E42, E43, E44, E45, E46, E49, E51, E52, E56]`
- Evidence against: _(none found — note that this may mean nobody looked)_
- **Test that would settle it:** Temporarily roll back v2.4.1 to observe if the error rate and HikariPool exhaustion subside. Alternatively, disable the retry mechanism in v2.4.1 or increase the `maxPoolSize` and monitor connection pool metrics and error rates.

> **Counter-argument:** The hypothesis fails to explain E57 ('charged twice') where a client-timed-out request resulted in a charge. This actively contradicts the claim that connections are merely consumed for 5s and fail, or that pool exhaustion primarily causes PaymentGatewayTimeout (E11, E12). Instead, the upstream gateway (already slow, E43, E59) processes requests beyond our 5s timeout, effectively holding connections longer and causing duplicates (E57) when v2.4.1's retry logic (E52) initiates new attempts. Falsify by examining gateway logs for transactions correlating to our read timeout errors (E8, E9, E10); if these consistently show true gateway failures, not delayed successes, the hypothesis is incorrect.

### 2. Independent degradation of the external payment gateway causes widespread slowness and timeouts.

*Confidence: 60% (plausible)*

The payment gateway (`gateway.acme-pay.com`) began showing increased latency around 09:47 UTC, well before the v2.4.1 deployment. This external degradation in performance is independently causing widespread slowness and timeouts. The v2.4.1 deployment, with its new timeouts and retry logic, may be exacerbating the symptoms or making them more visible, but the underlying issue of a struggling payment provider is external and not directly caused by our deployment.

- Evidence for: `[E4, E43, E59, E2, E3]`
- Evidence against: `[E51, E52, E12, E42, E25, E29, E36, E46]`
- **Test that would settle it:** Contact the payment gateway provider (Acme-Pay) to inquire about their system status, recent performance issues, and observed latency spikes around the incident timeframe.

### 3. V2.4.1's pooled client (HikariCP) is misconfigured or has a bug leading to connection exhaustion.

*Confidence: 50% (plausible)*

The HikariCP-backed pooled client introduced in v2.4.1 might have a misconfiguration (e.g., incorrect connection timeout handling, or improper connection release on certain error paths) or an underlying bug. This could lead to connections not being returned to the pool efficiently or correctly, causing the pool to deplete regardless of the external payment gateway's performance, although external slowness would hasten the exhaustion.

- Evidence for: `[E5, E12, E25, E29, E36, E42, E46, E51]`
- Evidence against: `[E4, E43]`
- **Test that would settle it:** Review the `PooledGatewayClient.java` code, particularly how HikariCP connections are acquired, used, and released, especially during timeout or exception scenarios. Simulate the exact gateway responses (slow and timeout) in a test environment to observe HikariPool behavior and connection management.

### 4. Unidentified internal resource contention within the checkout service, unrelated to the payment client, is causing overall slowness.

*Confidence: 20% (weak)*

Despite `NodeHealth` and `DatabaseConnections` being reported as healthy, another internal dependency or resource within the checkout service (e.g., an internal queue, another service call, or inefficient processing logic) might be experiencing contention or slowness. This could be delaying the initiation or completion of payment gateway calls, causing them to hit the new 5-second read timeouts introduced in v2.4.1, and thus contributing to the HikariPool exhaustion.

- Evidence for: `[E1, E45, E56]`
- Evidence against: `[E2, E3, E4, E6, E7, E43, E39]`
- **Test that would settle it:** Analyze metrics for other critical internal dependencies of the checkout service, such as internal message queue depths, other service call latencies, and CPU/memory utilization across the checkout pods, specifically looking for bottlenecks that emerged around 09:47 UTC or 10:15 UTC.

## Reasoning risks in this investigation

These describe how *this analysis* may be going wrong, not what broke in production.

### Confirmation bias (high, detected by heuristic)

- Where: 1 hypothesis/es list supporting evidence but nothing contradicting: "v2.4.1 deployment's pooled client and retry logic exhaust connections due to increasing upstream gateway latency.".
- Effect: Evidence that would weaken the favoured explanation was never collected, so its confidence score reflects the search, not the world.
- Reduce it by: For each one, state what you would expect to see in the logs if it were false, then go and look for it.

### Post hoc fallacy (medium, detected by model)

- Where: The initial framing of the incident as 'Checkout failures after v2.4.1' and the immediate focus on the deployment in Hypothesis 1.
- Effect: This could lead to overemphasizing the deployment as the sole cause and underestimating pre-existing issues or independent factors.
- Reduce it by: Acknowledged pre-deployment latency increase (e.g., in Hypothesis 2 and the timeline) and included a hypothesis that doesn't blame the deployment directly.

### Anchoring bias (low, detected by model)

- Where: Focusing heavily on 'read timeout after 5000ms' and 'Connection is not available' errors as the primary symptoms.
- Effect: This might limit the investigation to only the immediate failure points (timeouts) and miss broader architectural issues or a more upstream cause like external provider degradation.
- Reduce it by: Traced the timeouts back to increasing gateway latency and considered both internal (pool misconfiguration) and external (provider degradation) upstream causes.

## Next steps

| Priority | Action | Owner | Because of |
|---|---|---|---|
| P1 | Contact Acme-Pay (payment gateway provider) to inquire about their system status and recent performance issues, providing timestamps from our logs (starting ~09:47 UTC). | sre | E4, E43, E59 |
| P1 | Initiate a rollback of v2.4.1. | engineer | E1, E5, E8, E12, E44, E49, E51, E52 |
| P2 | Review the source code for `PooledGatewayClient.java` (lines 71, 114) and `CheckoutService.java` (line 88) from v2.4.1, focusing on connection acquisition/release and exception handling, especially after timeouts. | engineer | E41, E42, E51 |
| P2 | Monitor metrics for `payment-pool` (`active`, `idle`, `pending`, `maxPoolSize`) and `payment-client` gateway call durations continuously for any changes in trends. | sre | E25, E29, E36, E46 |

## Open questions

- What specifically changed in v2.4.1's `PooledGatewayClient` implementation compared to the previous per-request HTTP client regarding connection handling, timeouts, and error paths?
  - Why it matters: Understanding the exact behavioral differences in connection management is crucial for diagnosing why the pool is being exhausted and if the new client's configuration is suboptimal for the observed payment gateway latency.
- Are there any service-level metrics available from Acme-Pay (our payment gateway provider) that would confirm external degradation in performance?
  - Why it matters: Direct evidence from the payment provider would strongly support Hypothesis 2 and help determine the extent to which the problem is external vs. internal.
- What is the intended behavior of `maxPoolSize=10` in a production environment given the expected volume of checkout requests and the observed latency from the payment gateway?
  - Why it matters: This will help evaluate if the pool size is inherently too small, especially when combined with retries, even under normal operating conditions, or if it's only an issue when the gateway is severely degraded.

## Verification of AI claims

- Claims checked: 29
- Grounding score: 100%
- Statements with no citation: 0
- Citations pointing at non-existent evidence: 0

Grounding measures traceability, not correctness: a claim can cite a real line
and still misread it.

---

_Generated by IncidentIQ. Review, edit and sign before circulating._