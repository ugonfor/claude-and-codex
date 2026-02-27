"""Tests for the metrics tracking module."""

from __future__ import annotations

from claude_and_codex.metrics import TurnMetrics, AgentMetrics, MetricsTracker
from claude_and_codex.models import Role


class TestAgentMetrics:
    def test_record_single_turn(self) -> None:
        m = AgentMetrics()
        m.record(TurnMetrics(role=Role.CLAUDE, input_tokens=100, output_tokens=50, latency_ms=500))
        assert m.total_input_tokens == 100
        assert m.total_output_tokens == 50
        assert m.total_turns == 1
        assert m.avg_latency_ms == 500.0

    def test_record_multiple_turns(self) -> None:
        m = AgentMetrics()
        m.record(TurnMetrics(role=Role.CLAUDE, input_tokens=100, output_tokens=50, latency_ms=400))
        m.record(TurnMetrics(role=Role.CLAUDE, input_tokens=200, output_tokens=80, latency_ms=600))
        assert m.total_input_tokens == 300
        assert m.total_output_tokens == 130
        assert m.total_turns == 2
        assert m.avg_latency_ms == 500.0

    def test_avg_latency_zero_turns(self) -> None:
        m = AgentMetrics()
        assert m.avg_latency_ms == 0.0


class TestMetricsTracker:
    def test_tracks_per_agent(self) -> None:
        tracker = MetricsTracker()
        tracker.record_turn(TurnMetrics(role=Role.CLAUDE, input_tokens=100, output_tokens=50, latency_ms=300))
        tracker.record_turn(TurnMetrics(role=Role.CODEX, input_tokens=80, output_tokens=40, latency_ms=200))

        claude = tracker.get(Role.CLAUDE)
        assert claude.total_turns == 1
        assert claude.total_input_tokens == 100

        codex = tracker.get(Role.CODEX)
        assert codex.total_turns == 1
        assert codex.total_input_tokens == 80

    def test_summary_format(self) -> None:
        tracker = MetricsTracker()
        tracker.record_turn(TurnMetrics(role=Role.CLAUDE, input_tokens=1000, output_tokens=500, latency_ms=1200))
        summary = tracker.summary()
        assert "Claude:" in summary
        assert "Codex:" in summary
        assert "1000" in summary
        assert "Total tokens:" in summary

    def test_reset(self) -> None:
        tracker = MetricsTracker()
        tracker.record_turn(TurnMetrics(role=Role.CLAUDE, input_tokens=100, output_tokens=50, latency_ms=300))
        tracker.reset()
        assert tracker.get(Role.CLAUDE).total_turns == 0
        assert len(tracker.turns) == 0
