# Atlas Program KB

## Goals

**EU Launch** — target date 2026-09-15.

## Decisions

### Choose Stripe as payment provider
Status: accepted (2026-05-10). Based on PCI Compliance Audit 2026. Lower fees and stronger EU coverage than the incumbent.

### Use event sourcing for the billing ledger
Status: accepted (2026-05-22). Based on Latency Report Q2. Append-only ledger simplifies audit and replay.

### Deprecate the legacy REST API
Status: proposed (2026-06-03). Based on User Research June. Interviewees rely on the new endpoints already.

### Ship the EU region first
Status: accepted (2026-06-11). Based on User Research June. Largest waitlisted cohort is in the EU.

### Adopt Postgres 16 for the ledger store
Status: superseded (2026-04-18). Based on Latency Report Q2. Superseded by the event sourcing decision.

## Open Questions

### Do we need SOC2 certification before launch?
Status: open. Until answered this blocks Run the penetration test.

### Can the exporter reuse the ledger schema?
Status: open. Until answered this blocks Build the invoice PDF exporter.

### Is the latency budget 200ms or 300ms?
Status: resolved.

### Who signs the Stripe contract?
Status: open. Until answered this blocks Integrate the Stripe checkout flow.

## Billing workstream

### Integrate the Stripe checkout flow
Owned by Alice Chen. Status: doing. Priority: high. Due 2026-08-05. Covers hosted checkout and webhook handling. Gated by Choose Stripe as payment provider.

### Migrate historical invoices to the ledger
Owned by Alice Chen. Status: todo. Priority: high. Due 2026-08-20. Backfill of roughly forty thousand historical invoices. Gated by Integrate the Stripe checkout flow and Use event sourcing for the billing ledger.

### Notify customers about the billing change
Owned by Dev Patel. Status: todo. Priority: med. Due 2026-09-01. Email plus in-app banner announcement. Gated by Migrate historical invoices to the ledger.

### Reconcile refunds against the old system
Owned by Dev Patel. Status: todo. Priority: low. Reconciliation window is the last two fiscal years. Gated by Migrate historical invoices to the ledger.

### Build the invoice PDF exporter
Owned by Alice Chen. Status: todo. Priority: med. Exports must match the ledger totals exactly.

### Set up billing alerts and dashboards
Owned by Dev Patel. Status: done. Priority: low. Dashboards live in the shared observability space.

### Localize the checkout UI for German
Owned by Alice Chen. Status: todo. Priority: med. Part of EU Launch. Covers currency, date formats, and checkout copy. Gated by Integrate the Stripe checkout flow.

## Search workstream

### Rebuild the search indexing pipeline
Owned by Bob Marsh. Status: doing. Priority: high. Due 2026-08-12. Replaces the nightly batch indexer with streaming updates.

### Add typo tolerance to product search
Owned by Bob Marsh. Status: todo. Priority: med. Uses edit-distance matching for product names. Gated by Rebuild the search indexing pipeline.

### Benchmark query latency at ten times load
Owned by Bob Marsh. Status: done. Priority: high. Load profile mirrors the June traffic snapshot.

### Ship the search relevance A/B test
Owned by Dev Patel. Status: todo. Priority: med. Experiment runs on ten percent of traffic. Gated by Add typo tolerance to product search.

### Archive the old search cluster
Owned by Bob Marsh. Status: todo. Priority: low. Cluster is kept read-only for thirty days first. Gated by Rebuild the search indexing pipeline.

### Cache hot queries at the edge
Owned by Carol Diaz. Status: doing. Priority: med. Cache keys include region and locale. Gated by Ship the EU region first.

## Platform workstream

### Provision the EU data region
Owned by Carol Diaz. Status: doing. Priority: high. Due 2026-08-01. Part of EU Launch. Region is provisioned in Frankfurt. Gated by Ship the EU region first.

### Set up GDPR data-retention jobs
Owned by Erin Fox. Status: todo. Priority: high. Due 2026-08-25. Part of EU Launch. Retention defaults to ninety days for event data. Gated by Provision the EU data region.

### Run the penetration test
Owned by Erin Fox. Status: todo. Priority: high. Part of EU Launch. Scope covers the public API and the admin console.

### Automate blue-green deploys
Owned by Carol Diaz. Status: done. Priority: med. Cutover rehearsed in the staging environment.

### Rotate all production secrets
Owned by Erin Fox. Status: done. Priority: high. Rotation includes database and third-party credentials.

## People

### Alice Chen
Role: backend engineer. Team: Billing.

### Bob Marsh
Role: data engineer. Team: Search.

### Carol Diaz
Role: platform engineer. Team: Platform.

### Dev Patel
Role: product manager. Team: Billing.

### Erin Fox
Role: security engineer. Team: Platform.

## Sources

### PCI Compliance Audit 2026
Origin: external audit report, May 2026.

### Latency Report Q2
Origin: internal measurement, June 2026.

### User Research June
Origin: twelve customer interviews.
