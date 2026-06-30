import unittest

from src.analysis import calculate_weighted_similarity, resolve_similar_patterns


def _snapshot() -> dict[str, object]:
    return {
        "trend": {"state": "up"},
        "trend_slope": {"score": 72.0},
        "adx": 28.0,
        "rsi": 61.0,
        "atr": 2.4,
        "squeeze": {"state": "released"},
        "market_structure": {"state": "higher_high"},
    }


def _pattern(
    pattern_id: str = "pattern-1",
    trend: str = "up",
    trend_slope: float = 72.0,
    adx: float = 28.0,
    rsi: float = 61.0,
    atr: float = 2.4,
    squeeze: str = "released",
    market_structure: str = "higher_high",
    outcome: str = "win",
) -> dict[str, object]:
    return {
        "pattern_id": pattern_id,
        "trend": trend,
        "trend_slope": trend_slope,
        "adx": adx,
        "rsi": rsi,
        "atr": atr,
        "squeeze": squeeze,
        "market_structure": market_structure,
        "outcome": outcome,
    }


class SimilarPatternResolverTest(unittest.TestCase):
    def test_empty_pattern_library(self) -> None:
        result = resolve_similar_patterns(_snapshot(), [])

        self.assertEqual(result, {"matches": []})

    def test_exact_match_returns_100_similarity(self) -> None:
        result = resolve_similar_patterns(_snapshot(), [_pattern()])

        self.assertEqual(result["matches"][0]["similarity"], 100.0)
        self.assertEqual(calculate_weighted_similarity(_snapshot(), _pattern()), 100.0)

    def test_close_numeric_values_rank_higher_than_distant_values(self) -> None:
        close = _pattern(pattern_id="close", trend_slope=70.0, adx=29.0, rsi=60.0, atr=2.5)
        distant = _pattern(pattern_id="distant", trend_slope=25.0, adx=8.0, rsi=20.0, atr=8.0)

        result = resolve_similar_patterns(_snapshot(), [distant, close])

        self.assertEqual(result["matches"][0]["pattern_id"], "close")
        self.assertGreater(
            result["matches"][0]["similarity"],
            result["matches"][1]["similarity"],
        )

    def test_categorical_mismatch_lowers_score(self) -> None:
        exact_score = calculate_weighted_similarity(_snapshot(), _pattern())
        mismatch_score = calculate_weighted_similarity(
            _snapshot(),
            _pattern(trend="down", squeeze="compression"),
        )

        self.assertLess(mismatch_score, exact_score)

    def test_top_k_limits_results(self) -> None:
        patterns = [
            _pattern(pattern_id="one"),
            _pattern(pattern_id="two", rsi=58.0),
            _pattern(pattern_id="three", rsi=50.0),
        ]

        result = resolve_similar_patterns(_snapshot(), patterns, top_k=2)

        self.assertEqual(len(result["matches"]), 2)
        self.assertEqual(
            [match["pattern_id"] for match in result["matches"]],
            ["one", "two"],
        )

    def test_missing_fields_do_not_crash(self) -> None:
        result = resolve_similar_patterns(
            {"trend": {"state": "up"}},
            [{"pattern_id": "partial", "trend": "up"}],
        )

        self.assertEqual(result["matches"][0]["pattern_id"], "partial")
        self.assertGreaterEqual(result["matches"][0]["similarity"], 0.0)
        self.assertLessEqual(result["matches"][0]["similarity"], 100.0)


if __name__ == "__main__":
    unittest.main()
