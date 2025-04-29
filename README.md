# FessCTL [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**fessctl** is a command-line interface (CLI) tool to manage [Fess](https://fess.codelibs.org/) via its Admin API.

Fess is an open-source enterprise search server based on OpenSearch.  
`fessctl` allows developers and operators to automate and script administrative tasks such as:

- Creating or updating crawler configurations
- Managing users and roles
- Starting or stopping scheduled jobs
- Exporting and importing settings
- Monitoring system health

(Currently under development, more features and improvements are on the way. Stay tuned for updates!)

## Installation

### Requirements

- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) (recommended for environment setup)

### Setup

```bash
git clone https://github.com/your-org/fessctl.git
cd fessctl
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e src
```

## Run CLI

```bash
fessctl --help
```

### Example Commands

```bash
export FESS_ACCESS_TOKEN=...
fessctl ping
fessctl user list
fessctl webconfig create --name TestConfig --url https://test.config.com/
```

## Docker Build and Run

### Build Docker Image

```bash
docker build -t fessctl:latest .
```

### Run fessctl in Docker

You need to provide the following environment variables when running:

- FESS_ENDPOINT: The URL of your Fess server’s API endpoint. (Default: `http://localhost:8080`)
- FESS_ACCESS_TOKEN: Your access token to authenticate with the Fess API.

Example:

```bash
docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  fessctl --help
```

To run an actual command, for example:

```bash
docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  fessctl webconfig list
```

## License

This project is licensed under the Apache License 2.0.
See the LICENSE file for details.

## Contributing

Pull requests are welcome!
Feel free to open issues or discussions to suggest features, report bugs, or ask questions.
