#!/usr/bin/env python3
"""
Command Line Interface for Arbitrage Bot
==========================================

Professional CLI entry point for the arbitrage bot.
"""

import argparse
import asyncio
import sys

from arbitrage_bot.utils.config import Config
from arbitrage_bot.utils.logger import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Polymarket-Kalshi Arbitrage Bot - Professional Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  arbitrage-bot run                    # Run bot with default UI
  arbitrage-bot run --ui fastapi        # Run FastAPI dashboard
  arbitrage-bot run --ui terminal       # Run terminal UI
  arbitrage-bot run --ui none           # Run without UI
  arbitrage-bot scan                    # One-time market scan
  arbitrage-bot scan --min-profit 2.0   # Scan with 2% minimum profit
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the arbitrage bot")
    run_parser.add_argument(
        "--ui",
        choices=["fastapi", "terminal", "none"],
        default="fastapi",
        help="UI to use (default: fastapi)"
    )
    run_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    run_parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live trading (disable dry-run)"
    )
    run_parser.add_argument(
        "--port",
        type=int,
        help="Port to run server on"
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to"
    )
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan markets for arbitrage opportunities")
    scan_parser.add_argument(
        "--min-profit",
        type=float,
        help="Minimum profit percentage (default: from config)"
    )
    scan_parser.add_argument(
        "--threshold",
        type=float,
        default=65.0,
        help="Market matching threshold (default: 65)"
    )
    scan_parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    scan_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    
    return parser


async def run_bot(args):
    """Run the arbitrage bot."""
    from arbitrage_bot.bot import ArbitrageBot
    
    # Load configuration
    config = Config.load(args.config)
    
    # Override from command line
    if args.live:
        config.mode.trading_mode = "live"
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    # Create and run bot
    bot = ArbitrageBot(config)
    
    if args.ui == "none":
        # Run bot only
        await bot.run()
    elif args.ui == "terminal":
        # Run with terminal UI
        from arbitrage_bot.ui.terminal import TerminalUI
        ui = TerminalUI(bot, port=args.port or 8080, host=args.host)
        await ui.run()
    else:
        # Run with FastAPI dashboard
        from arbitrage_bot.ui.fastapi_dashboard import FastAPIDashboard
        dashboard = FastAPIDashboard(bot, port=args.port or 8000, host=args.host)
        await dashboard.run()


async def scan_markets(args):
    """Scan markets for arbitrage opportunities."""
    from arbitrage_bot.scanner import MarketScanner
    
    # Load configuration
    config = Config.load(args.config)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Create scanner
    scanner = MarketScanner(config)
    
    # Run scan
    results = await scanner.scan(
        min_profit=args.min_profit,
        threshold=args.threshold
    )
    
    # Output results
    if args.output == "json":
        import json
        print(json.dumps(results, indent=2, default=str))
    else:
        scanner.print_results(results)


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        asyncio.run(run_bot(args))
    elif args.command == "scan":
        asyncio.run(scan_markets(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

