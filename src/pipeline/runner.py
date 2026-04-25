"""Pipeline runner: per-stage timing + hard exit-code contract + --validate gate."""
import glob
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.pipeline.stages import STAGES

logger = logging.getLogger('pipeline')


def _setup_logging(log_dir: str = 'logs') -> logging.Logger:
    """Configure a RotatingFileHandler on the 'pipeline' logger.

    Safe to call multiple times — duplicate handlers are suppressed.
    """
    os.makedirs(log_dir, exist_ok=True)
    lg = logging.getLogger('pipeline')
    lg.setLevel(logging.INFO)
    # Avoid duplicate handlers across repeated run_all() invocations
    if not any(isinstance(h, RotatingFileHandler) for h in lg.handlers):
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'pipeline.log'),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3,
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        )
        lg.addHandler(handler)
    return lg


def _cleanup_figures(figures_dir: str = 'figures') -> int:
    """Delete all *.html files from figures_dir before a full pipeline run.

    Returns the number of files removed.
    """
    removed = 0
    for f in glob.glob(os.path.join(figures_dir, '*.html')):
        try:
            os.remove(f)
            removed += 1
        except OSError:
            pass
    return removed


class Pipeline:
    def __init__(self, config=None):
        self.config = config
        # Build name -> fn lookup from the registry
        self._by_name = {name: fn for name, fn in STAGES}

    def _stage_sequence(self, validate: bool):
        """Returns the stage list for a run. walk_forward is gated by validate."""
        for name, fn in STAGES:
            if name == 'walk_forward' and not validate:
                continue
            yield name, fn

    def run_all(self, validate: bool = False) -> dict:
        _setup_logging()
        n_removed = _cleanup_figures()
        logger.info('[CLEANUP] removed %d stale HTML file(s) from figures/', n_removed)
        stage_times: dict[str, float] = {}
        prev: Optional[dict] = None
        for name, fn in self._stage_sequence(validate):
            t0 = time.perf_counter()
            logger.info('[START] %s', name)
            try:
                # Stages that need prev dict accept it as kwarg
                try:
                    result = fn(self.config, prev=prev)
                except TypeError:
                    result = fn(self.config)
            except Exception as e:
                logger.exception('[FAIL] %s: %s', name, e)
                sys.exit(1)
            elapsed = time.perf_counter() - t0
            stage_times[name] = elapsed
            logger.info('[DONE] %s - %.1fs', name, elapsed)
            if isinstance(result, dict):
                prev = result
        total = sum(stage_times.values())
        logger.info('[TOTAL] %.0fs', total)
        print(f"\nPipeline complete in {total:.0f}s")
        for name, t in stage_times.items():
            print(f"  {name:18s} {t:6.1f}s")
        return stage_times

    def run_stage(self, stage_name: str) -> dict:
        _setup_logging()
        if stage_name not in self._by_name:
            raise KeyError(f"Unknown stage: {stage_name}. Known: {list(self._by_name)}")
        fn = self._by_name[stage_name]
        try:
            return fn(self.config) or {}
        except Exception as e:
            logger.exception('[FAIL] %s: %s', stage_name, e)
            sys.exit(1)

    def run_from(self, stage_name: str, validate: bool = False) -> dict:
        _setup_logging()
        started = False
        stage_times: dict[str, float] = {}
        prev = None
        for name, fn in self._stage_sequence(validate):
            if name == stage_name:
                started = True
            if not started:
                continue
            t0 = time.perf_counter()
            try:
                try:
                    result = fn(self.config, prev=prev)
                except TypeError:
                    result = fn(self.config)
            except Exception as e:
                logger.exception('[FAIL] %s: %s', name, e)
                sys.exit(1)
            stage_times[name] = time.perf_counter() - t0
            if isinstance(result, dict):
                prev = result
        if not started:
            raise KeyError(f"Unknown stage: {stage_name}")
        return stage_times
