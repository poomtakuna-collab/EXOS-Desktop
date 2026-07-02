from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import unittest
from typing import Any

from src.analysis_pipeline import AnalysisPipelineV2Request, PipelineConfig
from src.canonical_result import (
    CanonicalBrainResultV1,
    CanonicalDiagnosticsV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
)
from src.snapshot_payload_v2 import (
    SNAPSHOT_PAYLOAD_SCHEMA_VERSION_V2,
    SnapshotPayloadV2,
    build_snapshot_payload_v2,
)


class SnapshotPayloadV2Test(unittest.TestCase):
    def test_required_sections_exist(self) -> None:
        payload = build_snapshot_payload_v2(
            analysis_result=_analysis_result(),
            canonical_result=_canonical_result(),
            request=_request(),
            created_at=_created_at(),
        )

        output = payload.to_dict()

        self.assertIsInstance(payload, SnapshotPayloadV2)
        self.assertEqual(
            tuple(output),
            (
                "identity",
                "provenance",
                "input",
                "analysis",
                "context",
                "strategy",
                "display_summary",
                "diagnostics",
                "compatibility",
            ),
        )
        self.assertEqual(
            output["identity"]["payload_schema_version"],
            SNAPSHOT_PAYLOAD_SCHEMA_VERSION_V2,
        )
        self.assertEqual(output["identity"]["symbol"], "AAPL")
        self.assertEqual(output["identity"]["market_date"], "2026-07-02")

    def test_ohlcv_input_window_is_captured_when_provided(self) -> None:
        rows = (
            {"date": "2026-07-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000},
            {"date": "2026-07-02", "open": 101.0, "high": 102.0, "low": 100.0, "close": 101.5, "volume": 1200},
        )

        payload = build_snapshot_payload_v2(
            canonical_result=_canonical_result(),
            request=_request(rows=rows),
            ohlcv_rows=rows,
            created_at=_created_at(),
        ).to_dict()

        window = payload["input"]["ohlcv_window"]
        self.assertEqual(window["row_count"], 2)
        self.assertEqual(window["first_date"], "2026-07-01")
        self.assertEqual(window["last_date"], "2026-07-02")
        self.assertEqual(window["rows"], list(rows))

    def test_created_at_is_true_creation_timestamp(self) -> None:
        payload = build_snapshot_payload_v2(
            canonical_result=_canonical_result(),
        ).to_dict()

        created_at = payload["provenance"]["created_at"]
        parsed = datetime.fromisoformat(created_at)

        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset(), UTC.utcoffset(parsed))
        self.assertIn("T", created_at)

    def test_created_at_can_be_supplied_for_deterministic_builds(self) -> None:
        payload = build_snapshot_payload_v2(
            canonical_result=_canonical_result(),
            created_at=_created_at(),
        ).to_dict()

        self.assertEqual(
            payload["provenance"]["created_at"],
            "2026-07-02T09:30:00+00:00",
        )

    def test_no_outcomes_settings_ui_or_cache_tables_are_embedded(self) -> None:
        payload = build_snapshot_payload_v2(
            analysis_result=_analysis_result(),
            canonical_result=_canonical_result(),
            request=_request(),
            context={
                "market": {"trend": "up"},
                "settings": {"theme": "dark"},
                "ui": {"selected_tab": "Research"},
            },
            strategy={
                "strategy_score": 80,
                "outcomes": [{"return_pct": 5.0}],
            },
            provenance={
                "data_source": {
                    "source": "sqlite",
                    "cache_tables": ["ohlcv_daily"],
                    "market_data_cache": {"rows": 1000},
                },
            },
            compatibility={
                "signal_id": "signal-1",
                "legacy_signal_record_projection": {
                    "signal_id": "signal-1",
                    "outcome_records": [{"outcome_id": "outcome-1"}],
                    "settings": {"theme": "dark"},
                },
            },
            created_at=_created_at(),
        ).to_dict()

        encoded = json.dumps(payload, sort_keys=True)

        self.assertNotIn("outcome_records", encoded)
        self.assertNotIn("outcomes", encoded)
        self.assertNotIn("settings", encoded)
        self.assertNotIn("selected_tab", encoded)
        self.assertNotIn("cache_tables", encoded)
        self.assertNotIn("market_data_cache", encoded)
        self.assertIn("signal-1", encoded)
        self.assertIn("brain_snapshot", payload["analysis"])


def _created_at() -> datetime:
    return datetime(2026, 7, 2, 9, 30, tzinfo=UTC)


def _request(
    *,
    rows: tuple[dict[str, object], ...] = (),
) -> AnalysisPipelineV2Request:
    return AnalysisPipelineV2Request(
        symbol="AAPL",
        config=PipelineConfig(timeframe="1D", include_backtest=False),
        ohlcv_rows=list(rows),
        similar_patterns=[{"pattern_id": "pattern-1", "outcome": {"forward_10d_return": 3.0}}],
        start_date="2026-07-01",
        end_date="2026-07-02",
        limit=250,
        run_id="run-1",
        run_name="daily research",
    )


def _canonical_result() -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol="AAPL",
            timeframe="1D",
            snapshot_id="legacy-snapshot-1",
            snapshot_date="2026-07-02",
            analysis_date="2026-07-02",
            source="analysis_pipeline_v2",
            pipeline_name="analyze_symbol_v2",
            pipeline_version="v2",
            run_id="run-1",
        ),
        brain=CanonicalBrainResultV1(
            snapshot={"metadata": {"symbol": "AAPL"}, "score": {"overall_score": 80}},
            resolver_output={"matches": [{"pattern_id": "pattern-1"}]},
            probability={"probability_positive": 62.5},
            projection={"expected_return_10d": 4.0},
            target_zone={"target_zone": {"base": 110.0}},
            risk_zone={"risk_zone": {"base": 95.0}},
            prediction_summary={"confidence": 72.0, "evidence_count": 10},
            metadata={"adapter": "canonical_brain_adapter_v1"},
            notes=("brain note",),
        ),
        diagnostics=CanonicalDiagnosticsV1(
            source_pipeline="analyze_symbol_v2",
            available_sections=("brain", "prediction"),
            row_count=2,
            similar_pattern_count=1,
            adapter_version="canonical_result_adapter_v1",
        ),
        prediction=CanonicalPredictionResultV1(
            confidence=72.0,
            evidence_count=10,
            probability_positive=62.5,
            expected_return_10d=4.0,
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol="AAPL",
            signal_date="2026-07-02",
            timeframe="1D",
            signal_type="setup",
            confidence=72.0,
            snapshot_id="legacy-snapshot-1",
            snapshot_date="2026-07-02",
            context_summary={"market": {"trend": "up"}},
            strategy_summary={"strategy_score": 80},
            prediction_summary={"confidence": 72.0},
        ),
    )


@dataclass(frozen=True)
class _AnalysisResultFixture:
    request: AnalysisPipelineV2Request
    symbol: str = "AAPL"
    timeframe: str = "1D"
    data_source_metadata: dict[str, Any] = field(default_factory=lambda: {"market_data": {"source": "fixture"}})
    metadata: dict[str, Any] = field(default_factory=lambda: {"future_rows": 0})
    notes: list[str] = field(default_factory=lambda: ["fixture analysis"])


def _analysis_result() -> _AnalysisResultFixture:
    return _AnalysisResultFixture(request=_request())


if __name__ == "__main__":
    unittest.main()
