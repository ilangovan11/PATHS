"""Retraining entry point.

Usage:
    python training/retrain.py                 # train candidate, register (+promote if better)
    python training/retrain.py --activate v2   # explicitly activate a stored version

Uses the exact same pipeline as initial training (model.trainer.train), so
the base trainer and retrainer can never drift.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import settings
from core.logging import configure_logging, get_logger
from model import registry

configure_logging()


def run_retrain() -> dict:
    from model.trainer import train

    result = train(settings.BACKEND_DATA_PATH)
    return result


def activate(version: str) -> dict:
    registry_state = registry.load_registry(settings.MODEL_STORE_DIR)
    matching = [e for e in registry_state["history"] if e["version"] == version]
    if not matching:
        raise ValueError(f"Unknown model version: {version}")
    if not (settings.MODEL_STORE_DIR / version / "model.pkl").exists():
        raise ValueError(f"Artifacts missing for version {version}")

    for entry in registry_state["history"]:
        entry["active"] = entry["version"] == version
    registry_state["active_model"] = version
    registry.save_registry(settings.MODEL_STORE_DIR, registry_state)
    get_logger().info("Model activation: %s set active", version)
    return {"version": version, "active_model": registry.load_registry(settings.MODEL_STORE_DIR)["active_model"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PATHS model retraining")
    parser.add_argument("--activate", help="activate a stored version instead of retraining")
    args = parser.parse_args()

    if args.activate:
        print(json.dumps(activate(args.activate), indent=2))
    else:
        print(json.dumps(run_retrain()["version"]))