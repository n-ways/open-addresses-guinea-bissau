# Security

## Reporting a problem

If you find a security problem in the registry server, the engine or the published data (for example a way to issue or change codes without a key, to read data the registry does not publish, to crash a deployment, or a weakness in the check digit's protection), write to **hello@nways.ng** with "Security" in the subject. Describe the problem, how to reproduce it and what it affects. Please do not open a public issue until it is fixed.

We acknowledge a report within three working days, and we tell you what we will do and when. We credit reporters who wish to be named.

## Running a deployment safely

- A read-only deployment (no `ISSUE_KEYS`) cannot change any code. Run read-only unless the deployment is the designated issuer (GOVERNANCE.md, "One issuer").
- On the issuing deployment, generate long random keys (`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`), give each operator their own, keep them out of version control (`.env` is ignored by git), and remove a key from `ISSUE_KEYS` to revoke it.
- Serve the API over HTTPS behind a reverse proxy, and bind the server itself to the proxy only (server/README.md).
- Back up the database every day and keep the exports: they are the record of every code issued.

## What the registry holds

The registry describes places, never people: no names, telephone numbers or household details, and residential buildings carry no names. Its data is public under ODbL 1.0.
