# Deployment

The browser bundle and static assets can run on Cloudflare Workers. A Worker handles admission and routes a room to a game server through Workers VPC and a Cloudflare Tunnel. A Dockerized Colyseus service on Hetzner runs match authority. The templates in `assets/deploy/` are starting points; set project names, domains, and image tags per game. Keep local `.env*` ignored and configure production credentials in the platform's secret store.

Build the client, test its asset URLs and WebSocket upgrade route, then deploy a staging Worker and server image. Verify room creation, reconnect, snapshot flow, and a complete match before promotion. Pin deployment artifacts by immutable image digest or commit when promoting, while dependency manifests continue to use caret ranges. Maintain a room directory so the Worker can find the authority host. Keep CORS, origin validation, and health endpoints explicit.
