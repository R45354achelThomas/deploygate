# deploygate

Lightweight pre-deploy checklist runner that integrates with GitHub Actions and Slack notifications.

## Installation

```bash
pip install deploygate
```

## Usage

Define your checklist in a `deploygate.yml` file at the root of your project:

```yaml
checks:
  - name: Run tests
    run: pytest
  - name: Lint code
    run: flake8 .
  - name: Check migrations
    run: python manage.py migrate --check

notifications:
  slack:
    webhook_url: $SLACK_WEBHOOK_URL
    channel: "#deployments"
```

Then run the checklist before deploying:

```bash
deploygate run
```

### GitHub Actions Integration

```yaml
- name: Pre-deploy checks
  uses: actions/setup-python@v4
- run: pip install deploygate && deploygate run
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

If any check fails, deploygate exits with a non-zero status and sends a Slack alert automatically.

## License

MIT © 2024 deploygate contributors