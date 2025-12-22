# Setup Production Deploy for models-varroa-bottom

## Objective
Set up GitHub workflow deployment for models-varroa-bottom similar to models-bee-detector and models-frame-resources.

## Plan
- [x] Review existing deploy workflows in models-bee-detector and models-frame-resources
- [x] Review current docker-compose setup in models-varroa-bottom
- [x] Create .github/workflows/deploy.yml
- [x] Create restart.sh script
- [x] Fix branches array syntax in workflow
- [ ] Test deployment workflow (user to verify)

## Implementation Details

### GitHub Workflow
- Triggers on push to master branch or manual dispatch
- Runs on self-hosted runner
- Working directory: `/www/models-varroa-bottom/`
- Steps:
  1. Pull latest changes with `git reset --hard && git pull`
  2. Execute restart.sh script

### Restart Script
- Uses COMPOSE_PROJECT_NAME=gratheon for consistency with other services
- Uses docker-compose.prod.yml for production configuration
- Stops containers gracefully before rebuild
- Builds and starts containers in detached mode

### Production Configuration
- Port 8750 exposed
- network_mode: host (consistent with models-bee-detector)
- ENV_ID=prod environment variable
- Auto-restart enabled

## Files Changed
- `.github/workflows/deploy.yml` (new)
- `restart.sh` (new)
- `setup-production-deploy.md` (new - this file)

