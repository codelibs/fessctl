# FessCTL

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

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

### Run CLI

```bash
fessctl --help
```

## Example Commands

```bash
fessctl crawl start --job-id default_crawler
fessctl user create --username admin --password secret
fessctl config export --output fess-settings.json
```


## License

This project is licensed under the Apache License 2.0.
See the LICENSE file for details.

## Contributing

Pull requests are welcome!
Feel free to open issues or discussions to suggest features, report bugs, or ask questions.
