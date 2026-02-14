# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Personaut PDK seriously. If you discover a security vulnerability, please follow responsible disclosure practices.

### How to Report

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report vulnerabilities by emailing:

> **anthony@zivia.ai**

### What to Include

To help us triage and resolve the issue quickly, please include:

- **Description** — A clear summary of the vulnerability.
- **Impact** — What an attacker could achieve (e.g., data exposure, privilege escalation).
- **Reproduction steps** — Detailed steps or a minimal proof-of-concept to reproduce the issue.
- **Affected versions** — Which version(s) of the PDK are affected.
- **Suggested fix** *(optional)* — If you have a recommendation for how to address it.

### What to Expect

| Timeframe     | Action                                                                 |
| ------------- | ---------------------------------------------------------------------- |
| **24 hours**  | We will acknowledge receipt of your report.                            |
| **72 hours**  | We will provide an initial assessment and estimated timeline.          |
| **30 days**   | We aim to release a fix for confirmed vulnerabilities.                 |

After a fix is released, we will publicly credit the reporter (unless you prefer to remain anonymous).

### Scope

The following are **in scope** for responsible disclosure:

- Authentication and authorization flaws in the API server
- Injection vulnerabilities (prompt injection, SQL injection, path traversal)
- Sensitive data exposure (API keys, credentials leaking in logs or responses)
- Dependency vulnerabilities with a demonstrated exploit path
- Denial-of-service vectors in the server or simulation engine

The following are **out of scope**:

- Vulnerabilities in third-party LLM provider APIs (OpenAI, Gemini, Bedrock, Ollama)
- Social engineering attacks
- Issues requiring physical access to the host machine
- Denial-of-service attacks that require significant computational resources

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- **Authorized** under the Computer Fraud and Abuse Act (CFAA) and similar laws
- **Exempt** from DMCA restrictions on circumvention of technology controls
- **Lawful** and conducted in good faith

We will not pursue legal action against researchers who follow this policy.

## Security Best Practices for Users

When deploying the Personaut PDK:

1. **Never commit API keys** — Use environment variables or `.env` files (which are `.gitignore`d by default).
2. **Run the server behind a reverse proxy** — Do not expose the development server directly to the internet.
3. **Keep dependencies updated** — Run `pip install --upgrade personaut[all]` regularly.
4. **Review LLM outputs** — Generated content should be treated as untrusted input in downstream systems.
5. **Restrict file storage paths** — Configure `PERSONAUT_STORAGE_PATH` to a dedicated directory with appropriate permissions.
