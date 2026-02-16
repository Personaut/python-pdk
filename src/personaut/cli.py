"""Personaut CLI — setup configuration and start the server.

Usage::

    personaut setup          # interactive config wizard
    personaut serve          # start the API + UI server
    personaut serve --api-only  # API only (no web UI)
    personaut info           # show current configuration

Can also be invoked as::

    python -m personaut setup
    python -m personaut serve
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import textwrap
from pathlib import Path
from typing import Any

# ── ANSI colours (degraded gracefully on dumb terminals) ────────────

_NO_COLOUR = not sys.stdout.isatty() or os.environ.get("NO_COLOR")

def _c(code: str, text: str) -> str:  # noqa: E302
    return text if _NO_COLOUR else f"\033[{code}m{text}\033[0m"

def _bold(t: str) -> str:   return _c("1", t)
def _dim(t: str) -> str:    return _c("2", t)
def _green(t: str) -> str:  return _c("32", t)
def _cyan(t: str) -> str:   return _c("36", t)
def _yellow(t: str) -> str: return _c("33", t)
def _red(t: str) -> str:    return _c("31", t)
def _mag(t: str) -> str:    return _c("35", t)


# ── Constants ───────────────────────────────────────────────────────

BANNER = r"""
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║   ██████╗ ███████╗██████╗ ███████╗ ██████╗ ███╗   ██╗ █████╗  ║
  ║   ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗████╗  ██║██╔══██╗ ║
  ║   ██████╔╝█████╗  ██████╔╝███████╗██║   ██║██╔██╗ ██║███████║ ║
  ║   ██╔═══╝ ██╔══╝  ██╔══██╗╚════██║██║   ██║██║╚██╗██║██╔══██║ ║
  ║   ██║     ███████╗██║  ██║███████║╚██████╔╝██║ ╚████║██║  ██║ ║
  ║   ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ║
  ║                                                               ║
  ║           Persona Development Kit · Python SDK                ║
  ╚═══════════════════════════════════════════════════════════════╝
"""

PROVIDERS: list[dict[str, Any]] = [
    {
        "key": "gemini",
        "name": "Google Gemini",
        "env_key": "GOOGLE_API_KEY",
        "default_model": "gemini-2.0-flash",
        "models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.5-pro-preview-05-06",
            "gemini-2.5-flash-preview-04-17",
        ],
        "help": "Get a key at https://aistudio.google.com/apikey",
    },
    {
        "key": "openai",
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
        "help": "Get a key at https://platform.openai.com/api-keys",
    },
    {
        "key": "anthropic",
        "name": "Anthropic (Claude)",
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-5-20250929",
        "models": [
            "claude-opus-4-6",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
        "help": "Get a key at https://console.anthropic.com/settings/keys",
    },
    {
        "key": "bedrock",
        "name": "AWS Bedrock",
        "env_key": "AWS_ACCESS_KEY_ID",
        "default_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "models": [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "meta.llama3-3-70b-instruct-v1:0",
        ],
        "help": "Requires AWS credentials configured",
    },
    {
        "key": "ollama",
        "name": "Ollama (local)",
        "env_key": None,
        "default_model": "llama3.2",
        "models": ["llama3.2", "llama3.1", "mistral", "gemma2"],
        "help": "Run `ollama serve` and `ollama pull <model>` first",
    },
]


# ── Helpers ─────────────────────────────────────────────────────────

def _find_env_path() -> Path:
    """Find the .env file, walking up from cwd to locate a project root."""
    # Prefer a .env next to pyproject.toml or in cwd
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        if (d / "pyproject.toml").exists():
            return d / ".env"
        if d == d.parent:
            break
    return cwd / ".env"


def _read_env(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict (very simple, no quoting support)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


def _prompt(label: str, default: str = "", choices: list[str] | None = None) -> str:
    """Prompt user for input with optional default and choices."""
    parts = [_bold(label)]
    if choices:
        parts.append(_dim(f" [{'/'.join(choices)}]"))
    if default:
        parts.append(_dim(f" (default: {default})"))
    parts.append(": ")

    while True:
        value = input("".join(parts)).strip()
        if not value:
            return default
        if choices and value not in choices:
            print(f"  {_red('✗')} Please choose one of: {', '.join(choices)}")
            continue
        return value


def _prompt_secret(label: str, existing: str = "") -> str:
    """Prompt for a secret value, masking existing value."""
    import getpass

    masked = ""
    if existing:
        masked = existing[:4] + "•" * max(0, len(existing) - 8) + existing[-4:]
        label += f" [{_dim(masked)}]"
    value = getpass.getpass(f"  {_bold(label)}: ").strip()
    return value if value else existing


def _prompt_choice(label: str, options: list[dict[str, str]], default_idx: int = 0) -> int:
    """Prompt user to pick from a numbered list. Returns the index."""
    print(f"\n  {_bold(label)}")
    for i, opt in enumerate(options):
        marker = _cyan("→") if i == default_idx else " "
        name = _bold(opt["name"]) if i == default_idx else opt["name"]
        desc = _dim(f'  {opt.get("desc", "")}') if opt.get("desc") else ""
        print(f"    {marker} {_bold(str(i + 1))}. {name}{desc}")

    while True:
        raw = input(f"\n  Choice [{default_idx + 1}]: ").strip()
        if not raw:
            return default_idx
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print(f"  {_red('✗')} Enter a number 1–{len(options)}")


# ── setup command ───────────────────────────────────────────────────

def cmd_setup(args: argparse.Namespace) -> None:
    """Interactive configuration wizard."""
    print(_mag(BANNER))
    print(_bold("  Welcome to Personaut Setup\n"))
    print("  This wizard will configure your .env file with LLM provider")
    print("  credentials and storage settings.\n")

    env_path = _find_env_path()
    existing = _read_env(env_path)
    config: dict[str, str] = {}

    # ── Step 1: LLM Provider ────────────────────────────────────────
    print(_bold(_cyan("\n  ━━━ Step 1/3: LLM Provider ━━━\n")))

    provider_options = [
        {
            "name": p["name"],
            "desc": p["help"],
        }
        for p in PROVIDERS
    ]

    # Pre-select if existing config
    default_provider_idx = 0
    existing_provider = existing.get("PERSONAUT_LLM_PROVIDER", "").lower()
    for i, p in enumerate(PROVIDERS):
        if p["key"] == existing_provider:
            default_provider_idx = i
            break

    idx = _prompt_choice("Choose your LLM provider:", provider_options, default_provider_idx)
    provider = PROVIDERS[idx]
    config["PERSONAUT_LLM_PROVIDER"] = provider["key"]

    # ── API Key ─────────────────────────────────────────────────────
    if provider["env_key"]:
        print()
        existing_key = existing.get(provider["env_key"], "")

        if provider["key"] == "bedrock":
            # AWS needs multiple keys
            config["AWS_ACCESS_KEY_ID"] = _prompt_secret(
                "AWS Access Key ID", existing.get("AWS_ACCESS_KEY_ID", "")
            )
            config["AWS_SECRET_ACCESS_KEY"] = _prompt_secret(
                "AWS Secret Access Key", existing.get("AWS_SECRET_ACCESS_KEY", "")
            )
            region = _prompt(
                "  AWS Region",
                default=existing.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            config["AWS_DEFAULT_REGION"] = region
        else:
            key = _prompt_secret(provider["env_key"], existing_key)
            if key:
                config[provider["env_key"]] = key
            elif not existing_key:
                print(f"  {_yellow('⚠')}  No key provided. Chat will not work without it.")
                print(f"  {_dim(provider['help'])}")
    else:
        print(f"\n  {_green('✓')} {provider['name']} requires no API key.")
        print(f"    {_dim(provider['help'])}")

    # ── Model selection ─────────────────────────────────────────────
    print(_bold(_cyan("\n  ━━━ Step 2/3: Model ━━━\n")))

    model_options = [
        {"name": m, "desc": "(default)" if m == provider["default_model"] else ""}
        for m in provider["models"]
    ]
    default_model_idx = 0
    existing_model = existing.get("PERSONAUT_LLM_MODEL", "")
    for i, m in enumerate(provider["models"]):
        if m == existing_model:
            default_model_idx = i
            break

    model_idx = _prompt_choice("Choose a model:", model_options, default_model_idx)
    config["PERSONAUT_LLM_MODEL"] = provider["models"][model_idx]

    # ── Storage ─────────────────────────────────────────────────────
    print(_bold(_cyan("\n  ━━━ Step 3/3: Storage ━━━\n")))

    storage_options = [
        {"name": "SQLite", "desc": "Persistent storage (recommended)"},
        {"name": "Memory", "desc": "In-memory only — data lost on restart"},
    ]
    current_storage = existing.get("PERSONAUT_STORAGE_TYPE", "sqlite")
    storage_idx = _prompt_choice(
        "Storage type:",
        storage_options,
        0 if current_storage == "sqlite" else 1,
    )

    if storage_idx == 0:
        config["PERSONAUT_STORAGE_TYPE"] = "sqlite"
        db_path = _prompt(
            "  Database path",
            default=existing.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db"),
        )
        config["PERSONAUT_STORAGE_PATH"] = db_path
    else:
        config["PERSONAUT_STORAGE_TYPE"] = "memory"

    # ── Write .env ──────────────────────────────────────────────────
    print(_bold(_cyan("\n  ━━━ Summary ━━━\n")))

    env_lines = [
        "# Personaut PDK - Environment Configuration",
        f"# Generated by `personaut setup`",
        "",
    ]

    summary_rows = []
    for key, val in config.items():
        display_val = val
        if "KEY" in key or "SECRET" in key:
            display_val = val[:4] + "•" * max(0, len(val) - 8) + val[-4:] if len(val) > 8 else "••••"
        summary_rows.append((key, display_val))

        # Write the actual value (not masked)
        env_lines.append(f"{key}={val}")

    # Pretty-print summary table
    max_key_len = max(len(r[0]) for r in summary_rows) if summary_rows else 0
    for key, val in summary_rows:
        print(f"    {_dim(key.ljust(max_key_len))}  {_bold(val)}")

    print(f"\n  Config file: {_cyan(str(env_path))}")
    confirm = _prompt("\n  Write configuration?", default="yes", choices=["yes", "no"])

    if confirm == "yes":
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("\n".join(env_lines) + "\n")
        print(f"\n  {_green('✓')} Configuration saved to {env_path}")
        print(f"\n  {_bold('Next step:')} run {_cyan('personaut serve')} to start the server!")
    else:
        print(f"\n  {_yellow('⚠')} Configuration not saved.")


# ── serve command ───────────────────────────────────────────────────

def cmd_serve(args: argparse.Namespace) -> None:
    """Start the Personaut server."""
    # Load .env before anything else
    try:
        from dotenv import load_dotenv
        env_path = _find_env_path()
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    api_port: int = args.api_port
    ui_port: int = args.ui_port
    host: str = args.host
    api_only: bool = args.api_only

    print(_mag(BANNER))
    print(_bold("  Starting Personaut Server\n"))

    # Show config summary
    provider = os.environ.get("PERSONAUT_LLM_PROVIDER", _dim("auto-detect"))
    model = os.environ.get("PERSONAUT_LLM_MODEL", _dim("default"))
    storage = os.environ.get("PERSONAUT_STORAGE_TYPE", "sqlite")
    db_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")

    print(f"    Provider    {_bold(provider)}")
    print(f"    Model       {_bold(model)}")
    print(f"    Storage     {_bold(storage)}", end="")
    if storage == "sqlite":
        print(f"  →  {_dim(db_path)}")
    else:
        print()
    print(f"    API         {_cyan(f'http://{host}:{api_port}')}")
    if not api_only:
        print(f"    Web UI      {_cyan(f'http://{host}:{ui_port}')}")
    else:
        print(f"    Web UI      {_dim('disabled (--api-only)')}")
    print()

    # Import and start the server
    from personaut.server import LiveInteractionServer

    server = LiveInteractionServer()

    # Graceful shutdown on Ctrl-C
    def _signal_handler(sig: int, frame: Any) -> None:
        print(f"\n\n  {_yellow('⚠')} Shutting down...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print(f"  {_green('●')} Server is starting...\n")

    server.start(
        api_port=api_port,
        ui_port=ui_port if not api_only else None,
        host=host,
        api_only=api_only,
        blocking=True,
    )


# ── info command ────────────────────────────────────────────────────

def cmd_info(args: argparse.Namespace) -> None:
    """Show current configuration."""
    # Load .env
    try:
        from dotenv import load_dotenv
        env_path = _find_env_path()
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    print(_mag(BANNER))
    print(_bold("  Current Configuration\n"))

    env_path = _find_env_path()
    exists = env_path.exists()
    print(f"    Config file    {_cyan(str(env_path))} {'✓' if exists else _red('✗ not found')}")

    if exists:
        config = _read_env(env_path)
    else:
        config = {}

    # Provider
    provider = config.get("PERSONAUT_LLM_PROVIDER", os.environ.get("PERSONAUT_LLM_PROVIDER", ""))
    print(f"    LLM Provider   {_bold(provider) if provider else _dim('not set (auto-detect)')}")

    # Model
    model = config.get("PERSONAUT_LLM_MODEL", os.environ.get("PERSONAUT_LLM_MODEL", ""))
    print(f"    LLM Model      {_bold(model) if model else _dim('not set (provider default)')}")

    # API Keys
    for p in PROVIDERS:
        if p["env_key"]:
            val = config.get(p["env_key"], os.environ.get(p["env_key"] or "", ""))
            if val:
                masked = val[:4] + "•" * max(0, len(val) - 8) + val[-4:] if len(val) > 8 else "••••"
                status = _green(f"✓ {masked}")
            else:
                status = _dim("not set")
            # Bedrock has two keys
            if p["key"] == "bedrock":
                key2 = config.get("AWS_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY", ""))
                if val and key2:
                    status = _green("✓ configured")
                elif val or key2:
                    status = _yellow("⚠ partial")
            print(f"    {p['env_key']:<27} {status}")

    # Storage
    storage = config.get("PERSONAUT_STORAGE_TYPE", os.environ.get("PERSONAUT_STORAGE_TYPE", "sqlite"))
    db_path = config.get("PERSONAUT_STORAGE_PATH", os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db"))
    print(f"\n    Storage        {_bold(storage)}")
    if storage == "sqlite":
        db_exists = Path(db_path).exists()
        size = ""
        if db_exists:
            size_bytes = Path(db_path).stat().st_size
            if size_bytes > 1_048_576:
                size = f" ({size_bytes / 1_048_576:.1f} MB)"
            else:
                size = f" ({size_bytes / 1024:.0f} KB)"
        print(f"    Database       {_dim(db_path)}{size} {'✓' if db_exists else _yellow('(will be created)')}")

    # Version
    try:
        import importlib.metadata
        version = importlib.metadata.version("personaut")
    except Exception:
        version = "dev"
    print(f"\n    Version        {_bold(version)}")
    print()

    if not exists:
        print(f"  {_yellow('💡')} Run {_cyan('personaut setup')} to create your configuration.\n")


# ── Main entry point ────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="personaut",
        description="Personaut PDK — Persona Development Kit for Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              personaut setup                # configure LLM provider & storage
              personaut serve                # start API + Web UI
              personaut serve --api-only     # API only, no web UI
              personaut serve -p 9000 -u 3000  # custom ports
              personaut info                 # show current configuration
        """),
    )
    parser.add_argument(
        "--version", action="version",
        version=f"%(prog)s {_get_version()}",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # setup
    setup_parser = subparsers.add_parser(
        "setup",
        help="Interactive configuration wizard",
        description="Walk through LLM provider, model, and storage configuration.",
    )
    setup_parser.set_defaults(func=cmd_setup)

    # serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the Personaut server",
        description="Start the FastAPI backend and Flask web UI.",
    )
    serve_parser.add_argument(
        "-p", "--api-port", type=int, default=8000,
        help="Port for the FastAPI API server (default: 8000)",
    )
    serve_parser.add_argument(
        "-u", "--ui-port", type=int, default=5000,
        help="Port for the Flask web UI (default: 5000)",
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--api-only", action="store_true",
        help="Start API server only, no web UI",
    )
    serve_parser.set_defaults(func=cmd_serve)

    # info
    info_parser = subparsers.add_parser(
        "info",
        help="Show current configuration",
        description="Display the current configuration from .env and environment variables.",
    )
    info_parser.set_defaults(func=cmd_info)

    return parser


def _get_version() -> str:
    """Get the package version."""
    try:
        import importlib.metadata
        return importlib.metadata.version("personaut")
    except Exception:
        return "0.1.0-dev"


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
