"""
Configuration Management
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API configuration."""

    polymarket_rest_url: str = "https://clob.polymarket.com"
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    kalshi_api_url: str = "https://api.elections.kalshi.com/trade-api/v2"

    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    private_key: Optional[str] = None

    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class TradingConfig:
    """Trading configuration."""

    min_edge: float = 0.01  # 1% minimum edge
    bundle_arb_enabled: bool = True
    min_spread: float = 0.05  # 5c spread for market making
    mm_enabled: bool = False

    default_order_size: float = 5.0
    min_order_size: float = 2.0
    max_order_size: float = 10.0

    slippage_tolerance: float = 0.02
    order_timeout_seconds: int = 60

    maker_fee_bps: int = 0
    taker_fee_bps: int = 150
    estimated_gas_per_order: float = 0.02


@dataclass
class RiskConfig:
    """Risk management configuration."""

    max_position_per_market: float = 15.0
    max_global_exposure: float = 50.0
    max_daily_loss: float = 10.0
    max_drawdown_pct: float = 0.15

    trade_only_high_volume: bool = False
    min_24h_volume: float = 10000.0

    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)

    kill_switch_enabled: bool = True
    auto_unwind_on_breach: bool = False


@dataclass
class ModeConfig:
    """Mode configuration."""

    trading_mode: str = "dry_run"  # "dry_run" or "live"
    data_mode: str = "real"  # "real" or "simulation"
    cross_platform_enabled: bool = True
    kalshi_enabled: bool = True
    min_match_similarity: float = 0.6

    dry_run_initial_balance: float = 10000.0
    simulate_fills: bool = True
    fill_probability: float = 0.8


@dataclass
class Config:
    """Main configuration class."""

    api: APIConfig = field(default_factory=APIConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    mode: ModeConfig = field(default_factory=ModeConfig)
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """
        Load configuration from file.

        Args:
            path: Path to configuration file. If None, tries to find
                  config.yaml or .env in current directory.

        Returns:
            Config instance

        Raises:
            ValueError: If config file format is unknown
            FileNotFoundError: If config file doesn't exist
        """
        if path is None:
            # Try to find config.yaml in current directory
            path = "config.yaml"
            if not Path(path).exists():
                # Try .env file
                env_path = Path(".env")
                if env_path.exists():
                    return cls.load_from_env(env_path)
                return cls()  # Return default config

        config_path = Path(path)

        if config_path.suffix in (".yaml", ".yml"):
            return cls.load_from_yaml(config_path)
        elif config_path.name == ".env":
            return cls.load_from_env(config_path)
        else:
            raise ValueError(f"Unknown config file format: {path}")
    
    @classmethod
    def load_from_yaml(cls, path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        config = cls()
        
        # Load API config
        if "api" in data:
            api_data = data["api"]
            config.api = APIConfig(
                polymarket_rest_url=api_data.get("polymarket_rest_url", config.api.polymarket_rest_url),
                polymarket_ws_url=api_data.get("polymarket_ws_url", config.api.polymarket_ws_url),
                gamma_api_url=api_data.get("gamma_api_url", config.api.gamma_api_url),
                kalshi_api_url=api_data.get("kalshi_api_url", config.api.kalshi_api_url),
                api_key=api_data.get("api_key") or os.getenv("POLYMARKET_API_KEY"),
                api_secret=api_data.get("api_secret") or os.getenv("POLYMARKET_API_SECRET"),
                private_key=api_data.get("private_key") or os.getenv("POLYMARKET_PRIVATE_KEY"),
                timeout_seconds=api_data.get("timeout_seconds", config.api.timeout_seconds),
                max_retries=api_data.get("max_retries", config.api.max_retries),
                retry_delay_seconds=api_data.get("retry_delay_seconds", config.api.retry_delay_seconds),
            )
        
        # Load trading config
        if "trading" in data:
            trading_data = data["trading"]
            config.trading = TradingConfig(
                min_edge=trading_data.get("min_edge", config.trading.min_edge),
                bundle_arb_enabled=trading_data.get("bundle_arb_enabled", config.trading.bundle_arb_enabled),
                min_spread=trading_data.get("min_spread", config.trading.min_spread),
                mm_enabled=trading_data.get("mm_enabled", config.trading.mm_enabled),
                default_order_size=trading_data.get("default_order_size", config.trading.default_order_size),
                min_order_size=trading_data.get("min_order_size", config.trading.min_order_size),
                max_order_size=trading_data.get("max_order_size", config.trading.max_order_size),
                slippage_tolerance=trading_data.get("slippage_tolerance", config.trading.slippage_tolerance),
                order_timeout_seconds=trading_data.get("order_timeout_seconds", config.trading.order_timeout_seconds),
                maker_fee_bps=trading_data.get("maker_fee_bps", config.trading.maker_fee_bps),
                taker_fee_bps=trading_data.get("taker_fee_bps", config.trading.taker_fee_bps),
                estimated_gas_per_order=trading_data.get("estimated_gas_per_order", config.trading.estimated_gas_per_order),
            )
        
        # Load risk config
        if "risk" in data:
            risk_data = data["risk"]
            config.risk = RiskConfig(
                max_position_per_market=risk_data.get("max_position_per_market", config.risk.max_position_per_market),
                max_global_exposure=risk_data.get("max_global_exposure", config.risk.max_global_exposure),
                max_daily_loss=risk_data.get("max_daily_loss", config.risk.max_daily_loss),
                max_drawdown_pct=risk_data.get("max_drawdown_pct", config.risk.max_drawdown_pct),
                trade_only_high_volume=risk_data.get("trade_only_high_volume", config.risk.trade_only_high_volume),
                min_24h_volume=risk_data.get("min_24h_volume", config.risk.min_24h_volume),
                whitelist=risk_data.get("whitelist", config.risk.whitelist),
                blacklist=risk_data.get("blacklist", config.risk.blacklist),
                kill_switch_enabled=risk_data.get("kill_switch_enabled", config.risk.kill_switch_enabled),
                auto_unwind_on_breach=risk_data.get("auto_unwind_on_breach", config.risk.auto_unwind_on_breach),
            )
        
        # Load mode config
        if "mode" in data:
            mode_data = data["mode"]
            config.mode = ModeConfig(
                trading_mode=mode_data.get("trading_mode", config.mode.trading_mode),
                data_mode=mode_data.get("data_mode", config.mode.data_mode),
                cross_platform_enabled=mode_data.get("cross_platform_enabled", config.mode.cross_platform_enabled),
                kalshi_enabled=mode_data.get("kalshi_enabled", config.mode.kalshi_enabled),
                min_match_similarity=mode_data.get("min_match_similarity", config.mode.min_match_similarity),
                dry_run_initial_balance=mode_data.get("dry_run_initial_balance", config.mode.dry_run_initial_balance),
                simulate_fills=mode_data.get("simulate_fills", config.mode.simulate_fills),
                fill_probability=mode_data.get("fill_probability", config.mode.fill_probability),
            )
        
        return config
    
    @classmethod
    def load_from_env(cls, path: Path) -> "Config":
        """
        Load configuration from .env file.

        Args:
            path: Path to .env file

        Returns:
            Config instance
        """
        load_dotenv(path)
        
        config = cls()
        
        # Load from environment variables
        config.api.api_key = os.getenv("POLYMARKET_API_KEY")
        config.api.api_secret = os.getenv("POLYMARKET_API_SECRET")
        config.api.private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
        
        # Kalshi
        kalshi_key = os.getenv("KALSHI_API_KEY")
        kalshi_secret = os.getenv("KALSHI_API_SECRET")
        
        # Trading
        if os.getenv("MIN_ARBITRAGE_PROFIT_PCT"):
            config.trading.min_edge = float(os.getenv("MIN_ARBITRAGE_PROFIT_PCT")) / 100
        
        if os.getenv("DRY_RUN"):
            config.mode.trading_mode = "dry_run" if os.getenv("DRY_RUN").lower() == "true" else "live"
        
        return config
    
    @property
    def is_dry_run(self) -> bool:
        """Check if running in dry-run mode."""
        return self.mode.trading_mode == "dry_run"

