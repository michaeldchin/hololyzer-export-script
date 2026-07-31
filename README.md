-# Setup

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Quick Start

1. **Configure your API key:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Holodex API key:
   ```
   HOLODEX_API_KEY=your_actual_api_key_here
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run the script:**
   ```bash
   uv run --env-file=.env main.py
   ```

   ```bash
   uv run --env-file=.env main.py --latest-only
   ```
