"""Coordinator surface (`lab` CLI). Must not hold trading credentials."""

from mm_lab_cli.cli import main

__phase__ = 3
LIVE_TRADING_ENABLED = False

__all__ = ["LIVE_TRADING_ENABLED", "main"]
