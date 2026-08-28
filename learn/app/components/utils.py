"""
Utility Functions
Helper functions for GPU, memory, and session management
"""

import platform

import psutil
from state.cache import clear_cache_state
from state.persistence import save_session
from state.workflow import clear_workflow_state, get_session_id
import torch


def get_compute_device() -> dict:
    """
    Detect available compute device with detailed info.

    Returns dict with:
        - type: "CUDA", "MPS", or "CPU"
        - name: Device name (e.g., "NVIDIA RTX 3080", "Apple M1")
        - available: bool
    """
    try:
        if torch.cuda.is_available():
            return {
                "type": "CUDA",
                "name": torch.cuda.get_device_name(0),
                "available": True,
            }
        elif torch.backends.mps.is_available():
            return {
                "type": "MPS",
                "name": _get_apple_chip_name(),
                "available": True,
            }
        else:
            return {
                "type": "CPU",
                "name": platform.processor() or "Unknown",
                "available": True,
            }
    except Exception:
        return {"type": "CPU", "name": "Unknown", "available": True}


def _get_apple_chip_name() -> str:
    """Get Apple Silicon chip name on macOS."""
    try:
        import subprocess
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "Apple Silicon"
    except Exception:
        return "Apple Silicon"


def get_gpu_memory() -> str:
    """Get GPU memory info if available."""
    try:
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            allocated = torch.cuda.memory_allocated(0) / 1e9
            return f"{allocated:.1f}/{total:.1f} GB"
        elif torch.backends.mps.is_available():
            # MPS doesn't expose memory directly, show system unified memory
            return "Unified"
        else:
            return "N/A"
    except Exception:
        return "N/A"


def get_system_memory() -> str:
    """Get system RAM info."""
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        return f"{used_gb:.1f}/{total_gb:.1f} GB"
    except Exception:
        return "N/A"


def get_cpu_info() -> dict:
    """Get CPU information."""
    try:
        return {
            "cores": psutil.cpu_count(logical=False) or 0,
            "threads": psutil.cpu_count(logical=True) or 0,
            "usage": psutil.cpu_percent(interval=0.1),
        }
    except Exception:
        return {"cores": 0, "threads": 0, "usage": 0}


def get_platform_info() -> str:
    """Get platform/OS info."""
    system = platform.system()
    if system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    elif system == "Linux":
        return "Linux"
    elif system == "Windows":
        return f"Windows {platform.release()}"
    return system


# Legacy functions for backwards compatibility
def check_gpu_available() -> bool:
    """Check if GPU is available (legacy)."""
    device = get_compute_device()
    return device["type"] in ("CUDA", "MPS")


def get_memory_info() -> str:
    """Get memory info string (legacy)."""
    return get_gpu_memory()


def clear_session():
    """
    Clear all session state (workflow + cache, preserving UI preferences)
    Saves current session to disk before clearing
    """
    # Save current session before clearing
    current_session_id = get_session_id()
    if current_session_id:
        save_session(current_session_id)

    # Clear state
    clear_workflow_state()
    clear_cache_state()
    # Note: Intentionally NOT clearing UI state (theme) to preserve user preferences
