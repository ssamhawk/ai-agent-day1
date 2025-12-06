# GitHub Actions CI/CD

## What is GitHub Actions?

GitHub Actions is a CI/CD platform that allows you to automate your build, test, and deployment pipeline. You can create workflows that run on specific events in your repository.

## Basic Workflow Structure

Workflows are defined in YAML files in the `.github/workflows` directory.

```yaml
name: CI Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Run tests
        run: npm test
      - name: Build
        run: npm run build
```

## Common Triggers

- `push`: When code is pushed to a branch
- `pull_request`: When a PR is opened or updated
- `schedule`: Run on a cron schedule
- `workflow_dispatch`: Manual trigger
- `release`: When a release is published

## GitHub Actions vs Jenkins

**GitHub Actions advantages:**
- Native GitHub integration
- No server maintenance required
- Free minutes for public repositories
- Modern YAML syntax

**Jenkins advantages:**
- More plugins and customization
- Self-hosted control
- Better for complex enterprise pipelines

## Secrets Management

Store sensitive data in GitHub Secrets:

```yaml
steps:
  - name: Deploy
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: ./deploy.sh
```

## Matrix Builds

Test across multiple versions:

```yaml
strategy:
  matrix:
    node-version: [14, 16, 18]
    os: [ubuntu-latest, windows-latest, macos-latest]
```

## Deployment Example

```yaml
- name: Deploy to Production
  if: github.ref == 'refs/heads/main'
  run: |
    echo "Deploying to production"
    ./deploy-prod.sh
```
