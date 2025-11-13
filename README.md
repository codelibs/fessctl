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

## Installation and Usage

There are three ways to use fessctl:

### Method 1: Using Pre-built Docker Image

The easiest way to get started is using the pre-built Docker image:

```bash
docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  -e FESS_VERSION=15.3.2 \
  ghcr.io/codelibs/fessctl:0.1.0 --help
```

Run actual commands:

```bash
docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  -e FESS_VERSION=15.3.2 \
  ghcr.io/codelibs/fessctl:0.1.0 ping

docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  -e FESS_VERSION=15.3.2 \
  ghcr.io/codelibs/fessctl:0.1.0 user list
```

### Method 2: Building Your Own Docker Image

Clone the repository and build the Docker image locally:

```bash
git clone https://github.com/your-org/fessctl.git
cd fessctl
docker build -t fessctl:latest .
```

Then run with your custom image:

```bash
docker run --rm \
  -e FESS_ENDPOINT=https://your-fess-server \
  -e FESS_ACCESS_TOKEN=your_access_token_here \
  -e FESS_VERSION=15.3.2 \
  fessctl:latest --help
```

### Method 3: Install from Source with pip

For development or when you need to modify the source code:

#### Requirements
- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) (recommended for environment setup)

#### Setup
```bash
git clone https://github.com/your-org/fessctl.git
cd fessctl
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e src
```

#### Usage
```bash
export FESS_ACCESS_TOKEN=your_access_token_here
export FESS_ENDPOINT=https://your-fess-server
export FESS_VERSION=15.3.2

fessctl --help
fessctl ping
fessctl user list
fessctl webconfig create --name TestConfig --url https://test.config.com/
```

## Environment Variables

All three methods require the following environment variables:

- `FESS_ENDPOINT`: The URL of your Fess server's API endpoint (default: `http://localhost:8080`)
- `FESS_ACCESS_TOKEN`: Bearer token for API authentication (required)
- `FESS_VERSION`: Target Fess version for API compatibility (default: `15.3.2`)

## License

This project is licensed under the Apache License 2.0.
See the LICENSE file for details.

## Contributing

Pull requests are welcome!
Feel free to open issues or discussions to suggest features, report bugs, or ask questions.
