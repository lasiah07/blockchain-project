"""Jembatan MetaMask: komponen Streamlit dua arah berbasis ethers.js."""
from __future__ import annotations

import streamlit.components.v1 as components

from . import config

_bridge = components.declare_component("hc_metamask_bridge", path=str(config.COMPONENT_DIR))

DEFAULT_STATE = {"installed": None, "account": None, "chainId": None, "error": None, "tx": None, "rev": 0}


def render_bridge(action: dict | None) -> dict:
    """Render komponen (harus dipanggil pada posisi tetap di setiap run) dan kembalikan status wallet."""
    value = _bridge(
        chainId=config.CHAIN_ID,
        chainName=config.CHAIN_NAME,
        rpcUrl=config.RPC_URL,
        action=action,
        key="hc_wallet_bridge",
        default=DEFAULT_STATE,
    )
    return value if isinstance(value, dict) else dict(DEFAULT_STATE)
