from app.models import DataSummary, DataSummaryMetrics


def build_summary(points: list[dict]) -> DataSummary:
    """Compute period / count / basic stats / trend from raw data points.

    Each point is a dict with "date" (ISO string) and "value" (number).
    """
    if not points:
        return DataSummary(
            period="데이터 없음",
            count=0,
            metrics=DataSummaryMetrics(total=0, average=0, max=0, min=0),
            trend="데이터 없음",
        )

    sorted_points = sorted(points, key=lambda p: p["date"])
    values = [p["value"] for p in sorted_points]
    count = len(values)
    total = sum(values)
    average = total / count

    return DataSummary(
        period=f"{sorted_points[0]['date']} ~ {sorted_points[-1]['date']}",
        count=count,
        metrics=DataSummaryMetrics(
            total=round(total, 2),
            average=round(average, 2),
            max=max(values),
            min=min(values),
        ),
        trend=_calc_trend(sorted_points),
    )


def _calc_trend(sorted_points: list[dict]) -> str:
    count = len(sorted_points)
    half = count // 2
    if half == 0:
        return "유지 (데이터 부족)"

    first_half = sorted_points[:half]
    second_half = sorted_points[-half:]
    first_avg = sum(p["value"] for p in first_half) / len(first_half)
    second_avg = sum(p["value"] for p in second_half) / len(second_half)

    change_pct = 0.0 if first_avg == 0 else (second_avg - first_avg) / abs(first_avg) * 100

    if change_pct > 3:
        return f"상승 (최근 구간 평균 대비 +{change_pct:.1f}%)"
    if change_pct < -3:
        return f"하락 (최근 구간 평균 대비 {change_pct:.1f}%)"
    return "유지 (큰 변화 없음)"
