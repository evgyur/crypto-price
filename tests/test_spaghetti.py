import importlib.util
from pathlib import Path

from matplotlib.figure import Figure

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


def test_watermark_is_drawn_on_standard_chart(monkeypatch):
    calls = []

    def fake_savefig(self, path, *args, **kwargs):
        Path(path).write_bytes(b"png")

    monkeypatch.setattr(gpc.time, "time", lambda: 1_234_567)
    monkeypatch.setattr(Figure, "text", lambda self, *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(Figure, "savefig", fake_savefig, raising=False)

    chart = gpc._build_chart(
        "HYPE",
        [(1_000, 10.0, 11.0, 9.0, 10.5), (2_000, 10.5, 12.0, 10.0, 11.5)],
        "usd",
        "1h",
    )

    assert chart is not None
    watermark = next((args, kwargs) for args, kwargs in calls if args[2] == "Telegram: @human20")
    args, kwargs = watermark
    assert args[0] == 0.985
    assert args[1] == 0.018
    assert kwargs["ha"] == "right"
    assert kwargs["va"] == "bottom"
    assert kwargs["fontsize"] == 10


def test_watermark_is_drawn_on_spaghetti_chart(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setattr(Figure, "text", lambda self, *args, **kwargs: calls.append((args, kwargs)))

    series = {
        "HYPE": [(1_000, 0.0), (2_000, 10.0)],
        "ASTER": [(1_000, 0.0), (2_000, -5.0)],
    }
    chart = gpc._build_spaghetti_chart(series, "6mo", output_dir=str(tmp_path))

    assert chart is not None
    assert any(args[2] == "Telegram: @human20" for args, _kwargs in calls)
