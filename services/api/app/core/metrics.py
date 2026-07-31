"""Small dependency-free Prometheus registry for bounded ShopLens labels."""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from threading import Lock

_DEFAULT_BUCKETS = (1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0)


def _labels_key(labels: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((labels or {}).items()))


def _labels_text(labels: Iterable[tuple[str, str]], extra: tuple[str, str] | None = None) -> str:
    values = [*labels]
    if extra is not None:
        values.append(extra)
    if not values:
        return ""
    escaped = []
    for key, value in values:
        safe_value = value.replace("\\", "\\\\").replace('"', '\\"')
        escaped.append(f'{key}="{safe_value}"')
    return "{" + ",".join(escaped) + "}"


class MetricsRegistry:
    """Thread-safe counters, gauges, and fixed-bucket histograms."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[
            tuple[str, tuple[tuple[str, str], ...]], tuple[list[int], int, float]
        ] = {}
        self._help: dict[str, tuple[str, str]] = {}

    def counter(
        self,
        name: str,
        *,
        labels: Mapping[str, str] | None = None,
        value: float = 1.0,
        help_text: str = "ShopLens counter",
    ) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            self._help[name] = (help_text, "counter")
            self._counters[key] += value

    def gauge(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
        help_text: str = "ShopLens gauge",
    ) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            self._help[name] = (help_text, "gauge")
            self._gauges[key] = value

    def histogram(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
        help_text: str = "ShopLens histogram",
        buckets: tuple[float, ...] = _DEFAULT_BUCKETS,
    ) -> None:
        key = (name, _labels_key(labels))
        with self._lock:
            self._help[name] = (help_text, "histogram")
            counts, count, total = self._histograms.get(key, ([0 for _ in buckets], 0, 0.0))
            for index, boundary in enumerate(buckets):
                if value <= boundary:
                    counts[index] += 1
            self._histograms[key] = (counts, count + 1, total + value)

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for name in sorted(self._help):
                help_text, metric_type = self._help[name]
                lines.extend((f"# HELP {name} {help_text}", f"# TYPE {name} {metric_type}"))
                if metric_type == "counter":
                    for (metric, labels), value in sorted(self._counters.items()):
                        if metric == name:
                            lines.append(f"{name}{_labels_text(labels)} {value:g}")
                elif metric_type == "gauge":
                    for (metric, labels), value in sorted(self._gauges.items()):
                        if metric == name:
                            lines.append(f"{name}{_labels_text(labels)} {value:g}")
                else:
                    for (metric, labels), (counts, count, total) in sorted(
                        self._histograms.items()
                    ):
                        if metric != name:
                            continue
                        for boundary, bucket_count in zip(_DEFAULT_BUCKETS, counts, strict=True):
                            lines.append(
                                f"{name}_bucket{_labels_text(labels, ('le', f'{boundary:g}'))} "
                                f"{bucket_count}"
                            )
                        lines.append(f"{name}_bucket{_labels_text(labels, ('le', '+Inf'))} {count}")
                        lines.append(f"{name}_sum{_labels_text(labels)} {total:g}")
                        lines.append(f"{name}_count{_labels_text(labels)} {count}")
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._help.clear()


metrics = MetricsRegistry()
