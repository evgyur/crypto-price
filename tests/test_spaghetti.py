import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "get_price_chart.py"

spec = importlib.util.spec_from_file_location("get_price_chart", SCRIPT)
assert spec is not None and spec.loader is not None
gpc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpc)


def test_parse_spaghetti_args_symbols_and_duration():
    symbols, total_minutes, label, gradient = gpc._parse_spaghetti_args(["SP500", "GOLD", "SILVER", "6mo"])
    assert symbols == ["SP500", "GOLD", "SILVER"]
    assert total_minutes == 6 * 30 * 24 * 60
    assert label == "6mo"
    assert gradient is False


def test_parse_spaghetti_args_handles_commas_and_gradient():
    symbols, total_minutes, label, gradient = gpc._parse_spaghetti_args(["SP500,GOLD,SILVER", "1", "month", "--gradient"])
    assert symbols == ["SP500", "GOLD", "SILVER"]
    assert total_minutes == 30 * 24 * 60
    assert label == "1mo"
    assert gradient is True


def test_normalized_series_uses_first_close_as_zero_percent():
    candles = [
        (1_000, 10.0, 10.0, 10.0, 10.0),
        (2_000, 12.0, 12.0, 12.0, 12.0),
        (3_000, 15.0, 15.0, 15.0, 15.0),
    ]
    series = gpc._normalise_close_series(candles)
    assert series == [(1_000, 0.0), (2_000, 20.0), (3_000, 50.0)]


def test_spaghetti_chart_renderer_creates_png(tmp_path):
    series = {
        "SP500": [(1_000, 0.0), (2_000, 1.0), (3_000, 2.0)],
        "GOLD": [(1_000, 0.0), (2_000, -1.0), (3_000, 3.0)],
        "SILVER": [(1_000, 0.0), (2_000, 4.0), (3_000, -2.0)],
    }
    chart = gpc._build_spaghetti_chart(series, "6mo", output_dir=str(tmp_path))
    assert chart is not None
    path = Path(chart)
    assert path.exists()
    assert path.suffix == ".png"
    assert path.stat().st_size > 1000
