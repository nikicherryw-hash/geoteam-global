# SOURCE_MISMATCH — GeoTeam Global homepage finalisation

Status: BLOCKED BEFORE UI IMPLEMENTATION

## Evidence

- Requested base branch: `geoteam-v18-49-timeweb-native-preflight`
- Requested source path: `preview-v18-7/index.html`
- GitHub blob SHA on the requested branch: `33aeb08580e8c6c9c52ca52cdfd9109bf1f99899`
- The same blob SHA is also present on `geoteam-approved-original-preview-20261102`.
- The published staging page already renders the newer approved Russian headline: **«Интеллектуальная платформа решений»**.
- The requested GitHub source does not contain that approved phrase. It is therefore not the source of the currently published page.

## Safety decision

No homepage design code was changed in this branch. Applying changes to the stale GitHub HTML would create a pull request that could overwrite the current staging implementation at a later deployment.

No staging/production deployment, merge, backend, RFQ, authentication, DNS, or mail integration was changed.

## Required reconciliation before implementation

1. Export the current server-side `index.html` (and its directly used home assets/scripts) to a reviewed Git commit.
2. Record the server-side SHA-256 and the Git blob SHA in the reconciliation commit.
3. Base the homepage design branch on that reconciled commit.
4. Then implement and test the approved typography, navigation, compact search link, direction marker, ten-language news behaviour, and responsive layouts.

## Scope preserved

The intended work remains limited to the homepage desktop/mobile UX. The current globe, sourcing and RFQ architecture must remain unchanged.
