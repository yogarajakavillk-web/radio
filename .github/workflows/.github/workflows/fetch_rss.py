name: Fetch RSS Feeds

on:
  schedule:
    - cron: '*/30 * * * *'   # every 30 minutes
  workflow_dispatch:           # manual trigger from GitHub UI

jobs:
  fetch-rss:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Fetch RSS feeds
        run: python3 .github/workflows/fetch_rss.py

      - name: Commit updated data
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/news.json
          git diff --staged --quiet || git commit -m "RSS update $(date -u '+%Y-%m-%d %H:%M UTC')"
          git push

