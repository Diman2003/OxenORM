#!/usr/bin/env python3
"""
OxenORM uvloop Configuration

Automatically configures uvloop for enhanced performance when available.
"""

import asyncio
import os
import sys
import logging

logger = logging.getLogger(__name__)

_uvloop_enabled = False
_original_event_loop_policy = None


def is_uvloop_available() -> bool:
    """Check if uvloop is available."""
    try:
        import uvloop
        return True
    except ImportError:
        return False


def should_use_uvloop() -> bool:
    """Determine if uvloop should be used."""
    if not is_uvloop_available():
        return False
    
    uvloop_env = os.getenv('OXEN_UVLOOP', 'auto').lower()
    if uvloop_env == 'disabled':
        return False
    elif uvloop_env == 'enabled':
        return True
    else:
        return True


def configure_uvloop() -> bool:
    """Configure uvloop as the event loop policy."""
    global _uvloop_enabled, _original_event_loop_policy
    
    if not should_use_uvloop():
        return False
    
    try:
        import uvloop
        _original_event_loop_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        _uvloop_enabled = True
        logger.info("✅ uvloop configured for enhanced performance")
        return True
    except ImportError:
        logger.warning("⚠️ uvloop not available")
        return False


def is_uvloop_active() -> bool:
    """Check if uvloop is currently active."""
    return _uvloop_enabled


def get_event_loop_info() -> dict:
    """Get information about the current event loop."""
    try:
        loop = asyncio.get_event_loop()
        return {
            'loop_type': type(loop).__name__,
            'uvloop_enabled': is_uvloop_active(),
            'uvloop_available': is_uvloop_available(),
            'platform': sys.platform
        }
    except Exception as e:
        return {'error': str(e)}


# Auto-configure on import
if should_use_uvloop():
    configure_uvloop() 