"""Experiment framework for comparing agent collaboration configurations."""

from .metrics import ExperimentRunResult, RoundMetrics, DispatchMetrics, VerificationResult
from .benchmarks import Benchmark, load_benchmark, load_benchmarks
from .modes import ExperimentMode, ModeConfig
from .sandbox import Sandbox, create_sandbox, cleanup_sandbox, preserve_sandbox
from .runner import ExperimentRunner, ExperimentPlan
from .report import generate_markdown_report, generate_charts, save_results_json

__all__ = [
    "ExperimentRunResult", "RoundMetrics", "DispatchMetrics", "VerificationResult",
    "Benchmark", "load_benchmark", "load_benchmarks",
    "ExperimentMode", "ModeConfig",
    "Sandbox", "create_sandbox", "cleanup_sandbox", "preserve_sandbox",
    "ExperimentRunner", "ExperimentPlan",
    "generate_markdown_report", "generate_charts", "save_results_json",
]
