from pathlib import Path

import html
import json
import re


# ============================================================
# DASHBOARD AGENT
# ============================================================

def format_label(value):
    """Convert technical names into readable dashboard labels."""

    if value is None:
        return ""

    text = str(value).strip()

    text = text.replace("_", " ")

    text = re.sub(r"\s+", " ", text).strip()

    return text.title()


def safe_number(value):
    """Convert a value to float safely."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_money_metric(metric_name):
    """
    Detect metrics that are likely monetary.

    This is intentionally generic and does not depend on
    a specific dataset or business domain.
    """

    metric = str(metric_name).lower()

    money_keywords = {
        "sales",
        "sale",
        "revenue",
        "income",
        "profit",
        "cost",
        "price",
        "amount",
        "spend",
        "expense",
        "expenses",
        "payment",
        "payments",
        "balance",
        "mrr",
        "arr",
        "value",
        "total_value",
    }

    return any(
        keyword == metric
        or keyword in metric
        for keyword in money_keywords
    )


def format_metric_value(value, metric_name=""):
    """
    Format numeric values for dashboard display.

    The formatting is generic and does not assume a specific
    business domain.
    """

    number = safe_number(value)

    if number is None:
        return "N/A"

    metric = str(metric_name).lower()

    percentage_keywords = {
        "rate",
        "percent",
        "percentage",
        "margin",
    }

    if any(
        keyword in metric
        for keyword in percentage_keywords
    ):
        return f"{number:.1f}%"

    prefix = "$" if is_money_metric(metric) else ""

    absolute_number = abs(number)

    if absolute_number >= 1_000_000_000:
        return f"{prefix}{number / 1_000_000_000:.2f}B"

    if absolute_number >= 1_000_000:
        return f"{prefix}{number / 1_000_000:.2f}M"

    if absolute_number >= 1_000:
        return f"{prefix}{number / 1_000:.1f}K"

    if number.is_integer():
        return f"{prefix}{int(number):,}"

    return f"{prefix}{number:,.2f}"


def escape_html(value):
    """Safely escape dynamic values inserted into HTML."""

    return html.escape(str(value))


def safe_chart_id(value):
    """Create a safe HTML/JavaScript identifier."""

    text = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        str(value)
    )

    return text or "chart"


# ============================================================
# KPI BUILDING
# ============================================================

def build_kpi_cards(analysis_result):
    """
    Build KPI cards from the actual Analysis Agent output.

    Expected structure:

        metrics:
            primary_metric:
                column
                total
                average
                minimum
                maximum

            secondary_metrics:
                metric_name:
                    total
                    average
                    minimum
                    maximum

            record_count
            unique_id_count
    """

    metrics = analysis_result.get(
        "metrics",
        {}
    )

    if not isinstance(metrics, dict):
        return []

    kpis = []

    # --------------------------------------------------------
    # PRIMARY METRIC
    # --------------------------------------------------------

    primary = metrics.get(
        "primary_metric"
    )

    if isinstance(primary, dict):

        column = primary.get(
            "column"
        )

        total = primary.get(
            "total"
        )

        if column and total is not None:

            kpis.append(
                {
                    "label": f"Total {format_label(column)}",
                    "value": format_metric_value(
                        total,
                        column
                    ),
                    "subtitle": "Primary metric",
                    "type": "primary",
                }
            )

    # --------------------------------------------------------
    # SECONDARY METRICS
    # --------------------------------------------------------

    secondary_metrics = metrics.get(
        "secondary_metrics",
        {}
    )

    if isinstance(
        secondary_metrics,
        dict
    ):

        for metric_name, metric_data in secondary_metrics.items():

            if len(kpis) >= 4:
                break

            if not isinstance(
                metric_data,
                dict
            ):
                continue

            total = metric_data.get(
                "total"
            )

            if total is None:
                continue

            kpis.append(
                {
                    "label": (
                        f"Total "
                        f"{format_label(metric_name)}"
                    ),
                    "value": format_metric_value(
                        total,
                        metric_name
                    ),
                    "subtitle": "Secondary metric",
                    "type": "secondary",
                }
            )

    # --------------------------------------------------------
    # RECORD COUNT
    # --------------------------------------------------------

    record_count = metrics.get(
        "record_count"
    )

    if (
        record_count is not None
        and len(kpis) < 6
    ):

        kpis.append(
            {
                "label": "Records",
                "value": format_metric_value(
                    record_count,
                    "record_count"
                ),
                "subtitle": "Analyzed rows",
                "type": "secondary",
            }
        )

    # --------------------------------------------------------
    # UNIQUE ID COUNT
    # --------------------------------------------------------

    unique_id_count = metrics.get(
        "unique_id_count"
    )

    if (
        unique_id_count is not None
        and len(kpis) < 6
    ):

        kpis.append(
            {
                "label": "Unique IDs",
                "value": format_metric_value(
                    unique_id_count,
                    "unique_id_count"
                ),
                "subtitle": "Detected identifiers",
                "type": "secondary",
            }
        )

    return kpis[:6]


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def build_executive_summary(analysis_result):
    """
    Build a short automatically generated executive summary.

    The summary uses verified analysis results rather than
    hardcoded domain-specific text.
    """

    domain = analysis_result.get(
        "domain",
        {}
    )

    if not isinstance(domain, dict):
        domain = {}

    metrics = analysis_result.get(
        "metrics",
        {}
    )

    if not isinstance(metrics, dict):
        metrics = {}

    primary_metric = domain.get(
        "primary_metric"
    )

    primary_data = metrics.get(
        "primary_metric",
        {}
    )

    if not isinstance(
        primary_data,
        dict
    ):
        primary_data = {}

    total = primary_data.get(
        "total"
    )

    records = metrics.get(
        "record_count"
    )

    unique_ids = metrics.get(
        "unique_id_count"
    )

    domain_label = (
        domain.get("domain_label")
        or format_label(
            domain.get(
                "domain",
                "Business Data"
            )
        )
    )

    parts = []

    if total is not None and primary_metric:
        parts.append(
            f"{format_label(primary_metric)} "
            f"reached "
            f"{format_metric_value(total, primary_metric)}"
        )

    if records is not None:
        parts.append(
            f"across "
            f"{format_metric_value(records, 'record_count')} "
            f"analyzed records"
        )

    if unique_ids is not None:
        parts.append(
            f"with "
            f"{format_metric_value(unique_ids, 'unique_id_count')} "
            f"unique identifiers detected"
        )

    if not parts:
        return (
            f"{domain_label} data was successfully analyzed "
            "using the detected dataset structure."
        )

    return (
        f"{domain_label} analysis: "
        + ", ".join(parts)
        + "."
    )


# ============================================================
# CHART DATA
# ============================================================

def build_chart_data(analysis_result):
    """
    Convert the actual Analysis Agent result into dashboard
    chart specifications.
    """

    charts = []

    domain = analysis_result.get(
        "domain",
        {}
    )

    if not isinstance(domain, dict):
        domain = {}

    primary_metric = domain.get(
        "primary_metric"
    )

    # --------------------------------------------------------
    # 1. TIME TREND
    # --------------------------------------------------------

    trend_analysis = analysis_result.get(
        "trend_analysis"
    )

    if isinstance(
        trend_analysis,
        dict
    ):

        trend_data = trend_analysis.get(
            "data",
            []
        )

        if isinstance(
            trend_data,
            list
        ):

            labels = []
            values = []

            for item in trend_data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                period = item.get(
                    "period"
                )

                total = item.get(
                    "total"
                )

                numeric_value = safe_number(
                    total
                )

                if period is None:
                    continue

                if numeric_value is None:
                    continue

                labels.append(
                    str(period)
                )

                values.append(
                    numeric_value
                )

            if labels and values:

                trend_metric = (
                    trend_analysis.get("metric")
                    or primary_metric
                    or "metric"
                )

                charts.append(
                    {
                        "id": "trend_chart",
                        "title": (
                            f"{format_label(trend_metric)} "
                            f"Trend"
                        ),
                        "type": "line",
                        "labels": labels,
                        "values": values,
                        "metric": trend_metric,
                    }
                )

    # --------------------------------------------------------
    # 2. RECOMMENDED DIMENSION CHARTS
    # --------------------------------------------------------

    dimension_analysis = analysis_result.get(
        "dimension_analysis",
        {}
    )

    if not isinstance(
        dimension_analysis,
        dict
    ):
        dimension_analysis = {}

    recommended_charts = domain.get(
        "recommended_charts",
        []
    )

    selected_dimensions = []

    # First respect domain configuration recommendations.
    if isinstance(
        recommended_charts,
        list
    ):

        for recommendation in recommended_charts:

            if not isinstance(
                recommendation,
                dict
            ):
                continue

            chart_type = recommendation.get(
                "type"
            )

            dimension = recommendation.get(
                "x"
            )

            if chart_type not in {
                "bar",
                "pie",
                "scatter",
            }:
                continue

            if (
                dimension
                and dimension in dimension_analysis
                and dimension not in selected_dimensions
            ):

                selected_dimensions.append(
                    dimension
                )

    # Then fill remaining slots from available dimensions.
    for dimension in dimension_analysis.keys():

        if dimension in selected_dimensions:
            continue

        selected_dimensions.append(
            dimension
        )

    # Maximum of four categorical charts.
    selected_dimensions = selected_dimensions[:4]

    # --------------------------------------------------------
    # BUILD DIMENSION CHARTS
    # --------------------------------------------------------

    for dimension in selected_dimensions:

        dimension_data = dimension_analysis.get(
            dimension
        )

        if not isinstance(
            dimension_data,
            dict
        ):
            continue

        top_values = dimension_data.get(
            "top_values",
            []
        )

        if not isinstance(
            top_values,
            list
        ):
            continue

        labels = []
        values = []

        for row in top_values[:10]:

            if not isinstance(
                row,
                dict
            ):
                continue

            label = row.get(
                "value"
            )

            total = row.get(
                "total"
            )

            numeric_value = safe_number(
                total
            )

            if label is None:
                continue

            if numeric_value is None:
                continue

            labels.append(
                str(label)
            )

            values.append(
                numeric_value
            )

        if not labels:
            continue

        chart_id = (
            f"dimension_{safe_chart_id(dimension)}"
        )

        charts.append(
            {
                "id": chart_id,
                "title": (
                    f"{format_label(primary_metric or 'Metric')} "
                    f"by {format_label(dimension)}"
                ),
                "type": "bar",
                "labels": labels,
                "values": values,
                "metric": (
                    primary_metric
                    or "metric"
                ),
                "dimension": dimension,
            }
        )

    return charts


# ============================================================
# PERFORMER SECTIONS
# ============================================================

def build_performer_sections(analysis_result):
    """
    Build top/bottom performer sections from:

        performer_analysis:
            dimension:
                top:
                    value
                    metric

                bottom:
                    value
                    metric
    """

    performer_analysis = analysis_result.get(
        "performer_analysis",
        {}
    )

    if not isinstance(
        performer_analysis,
        dict
    ):
        return []

    sections = []

    for (
        dimension_name,
        performer_data
    ) in performer_analysis.items():

        if not isinstance(
            performer_data,
            dict
        ):
            continue

        top = performer_data.get(
            "top",
            []
        )

        bottom = performer_data.get(
            "bottom",
            []
        )

        if not isinstance(
            top,
            list
        ):
            top = []

        if not isinstance(
            bottom,
            list
        ):
            bottom = []

        if not top and not bottom:
            continue

        sections.append(
            {
                "dimension": dimension_name,
                "top": top[:5],
                "bottom": bottom[:5],
            }
        )

    return sections[:4]


# ============================================================
# INSIGHTS
# ============================================================

def clean_text_items(
    items,
    limit
):
    """Convert insight/recommendation results into safe strings."""

    if not isinstance(
        items,
        list
    ):
        return []

    cleaned = []

    for item in items:

        if isinstance(
            item,
            dict
        ):

            text = (
                item.get("text")
                or item.get("insight")
                or item.get("recommendation")
                or item.get("description")
            )

        else:

            text = str(item)

        if text:

            cleaned.append(
                str(text).strip()
            )

    return cleaned[:limit]


def build_insight_cards(
    analysis_result
):

    insights = analysis_result.get(
        "insights",
        []
    )

    return clean_text_items(
        insights,
        8
    )


def build_recommendations(
    analysis_result
):

    recommendations = analysis_result.get(
        "recommendations",
        []
    )

    return clean_text_items(
        recommendations,
        6
    )


# ============================================================
# HTML COMPONENTS
# ============================================================

def render_kpis(kpis):

    if not kpis:

        return """
        <div class="empty-state">
            No KPI data is available.
        </div>
        """

    cards = []

    for index, kpi in enumerate(kpis):

        card_class = (
            "kpi-card primary"
            if kpi.get("type") == "primary"
            else "kpi-card"
        )

        cards.append(
            f"""
            <div class="{card_class}">

                <div class="kpi-top">

                    <span class="kpi-label">
                        {escape_html(
                            kpi.get(
                                "label",
                                ""
                            )
                        )}
                    </span>

                    <span class="kpi-number">
                        {str(index + 1).zfill(2)}
                    </span>

                </div>

                <div class="kpi-value">
                    {escape_html(
                        kpi.get(
                            "value",
                            "N/A"
                        )
                    )}
                </div>

                <div class="kpi-subtitle">
                    {escape_html(
                        kpi.get(
                            "subtitle",
                            ""
                        )
                    )}
                </div>

            </div>
            """
        )

    return "\n".join(
        cards
    )


def render_charts(charts):

    if not charts:

        return """
        <section class="panel empty-panel">

            <h2>
                Visual Analysis
            </h2>

            <p class="muted">
                No chartable analysis was available
                for this dataset.
            </p>

        </section>
        """

    sections = []

    for chart in charts:

        sections.append(
            f"""
            <section class="chart-card">

                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            DATA VISUALIZATION
                        </span>

                        <h2>
                            {escape_html(
                                chart.get(
                                    "title",
                                    "Chart"
                                )
                            )}
                        </h2>

                    </div>

                    <span class="chart-type">
                        {escape_html(
                            format_label(
                                chart.get(
                                    "type",
                                    "chart"
                                )
                            )
                        )}
                    </span>

                </div>

                <div class="chart-wrapper">

                    <canvas
                        id="{escape_html(chart["id"])}"
                    ></canvas>

                </div>

            </section>
            """
        )

    return "\n".join(
        sections
    )


def format_table_value(
    value,
    metric_name
):

    numeric_value = safe_number(
        value
    )

    if numeric_value is not None:

        return format_metric_value(
            numeric_value,
            metric_name
        )

    return str(value)


def render_performers(
    sections,
    primary_metric
):

    if not sections:

        return """
        <section class="panel">

            <div class="section-header">

                <div>

                    <span class="eyebrow">
                        PERFORMANCE
                    </span>

                    <h2>
                        Performance Highlights
                    </h2>

                </div>

            </div>

            <p class="muted">
                No performer analysis is available
                for this dataset.
            </p>

        </section>
        """

    output = []

    for section in sections:

        top_rows = []

        for item in section.get(
            "top",
            []
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            label = (
                item.get("value")
                or item.get("label")
                or item.get("name")
                or "Unknown"
            )

            value = item.get(
                "metric"
            )

            top_rows.append(
                f"""
                <tr>

                    <td>
                        {escape_html(label)}
                    </td>

                    <td>
                        {escape_html(
                            format_table_value(
                                value,
                                primary_metric
                            )
                        )}
                    </td>

                </tr>
                """
            )

        bottom_rows = []

        for item in section.get(
            "bottom",
            []
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            label = (
                item.get("value")
                or item.get("label")
                or item.get("name")
                or "Unknown"
            )

            value = item.get(
                "metric"
            )

            bottom_rows.append(
                f"""
                <tr>

                    <td>
                        {escape_html(label)}
                    </td>

                    <td>
                        {escape_html(
                            format_table_value(
                                value,
                                primary_metric
                            )
                        )}
                    </td>

                </tr>
                """
            )

        output.append(
            f"""
            <section class="panel">

                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            DIMENSION
                        </span>

                        <h2>
                            {escape_html(
                                format_label(
                                    section.get(
                                        "dimension"
                                    )
                                )
                            )}
                        </h2>

                    </div>

                </div>

                <div class="performance-grid">

                    <div class="performance-column top-performance">

                        <h3>
                            <span class="performance-dot top-dot"></span>
                            Top performers
                        </h3>

                        <table>

                            <thead>

                                <tr>
                                    <th>Item</th>
                                    <th>Value</th>
                                </tr>

                            </thead>

                            <tbody>
                                {"".join(top_rows)}
                            </tbody>

                        </table>

                    </div>


                    <div class="performance-column bottom-performance">

                        <h3>
                            <span class="performance-dot bottom-dot"></span>
                            Lowest performers
                        </h3>

                        <table>

                            <thead>

                                <tr>
                                    <th>Item</th>
                                    <th>Value</th>
                                </tr>

                            </thead>

                            <tbody>
                                {"".join(bottom_rows)}
                            </tbody>

                        </table>

                    </div>

                </div>

            </section>
            """
        )

    return "\n".join(
        output
    )


def render_list_panel(
    title,
    items,
    icon
):

    if not items:
        return ""

    rows = []

    for index, item in enumerate(
        items,
        start=1
    ):

        rows.append(
            f"""
            <div class="list-item">

                <div class="list-index">
                    {str(index).zfill(2)}
                </div>

                <div class="list-icon">
                    {escape_html(icon)}
                </div>

                <div class="list-text">
                    {escape_html(item)}
                </div>

            </div>
            """
        )

    return f"""
    <section class="panel">

        <div class="section-header">

            <div>

                <span class="eyebrow">
                    AI ANALYSIS
                </span>

                <h2>
                    {escape_html(title)}
                </h2>

            </div>

            <span class="analysis-count">
                {len(rows):02d}
            </span>

        </div>

        <div class="list-container">
            {"".join(rows)}
        </div>

    </section>
    """


# ============================================================
# JAVASCRIPT
# ============================================================

def build_chart_javascript(
    charts
):

    scripts = []

    for chart in charts:

        chart_id = json.dumps(
            chart["id"]
        )

        labels = json.dumps(
            chart["labels"]
        )

        values = json.dumps(
            chart["values"]
        )

        chart_type = json.dumps(
            chart["type"]
        )

        metric_label = json.dumps(
            format_label(
                chart.get(
                    "metric",
                    "Value"
                )
            )
        )

        scripts.append(
            f"""
            (() => {{

                const canvas =
                    document.getElementById(
                        {chart_id}
                    );

                if (!canvas) {{
                    return;
                }}

                new Chart(
                    canvas,
                    {{
                        type: {chart_type},

                        data: {{

                            labels: {labels},

                            datasets: [{{
                                label: {metric_label},

                                data: {values},

                                borderWidth: 2,

                                borderRadius:
                                    {chart_type} === "bar"
                                        ? 8
                                        : 0,

                                tension: 0.35,

                                fill:
                                    {chart_type} === "line"
                                        ? true
                                        : false,

                                pointRadius:
                                    {chart_type} === "line"
                                        ? 3
                                        : 0,

                                pointHoverRadius:
                                    6
                            }}]

                        }},

                        options: {{

                            responsive: true,

                            maintainAspectRatio: false,

                            interaction: {{
                                mode: "index",
                                intersect: false
                            }},

                            plugins: {{

                                legend: {{
                                    display: false
                                }},

                                tooltip: {{
                                    enabled: true,

                                    padding: 12,

                                    displayColors: false,

                                    callbacks: {{

                                        label: function(context) {{

                                            const value =
                                                context.parsed.y
                                                ?? context.parsed;

                                            if (
                                                typeof value ===
                                                "number"
                                            ) {{

                                                return (
                                                    "{escape_html(format_label(chart.get("metric", "Value")))}: "
                                                    + value.toLocaleString()
                                                );

                                            }}

                                            return value;

                                        }}

                                    }}
                                }}

                            }},

                            scales: {{

                                x: {{

                                    grid: {{
                                        display: false
                                    }},

                                    ticks: {{

                                        maxRotation: 45,

                                        minRotation: 0,

                                        color: "#64748b",

                                        font: {{
                                            size: 11
                                        }}

                                    }}

                                }},

                                y: {{

                                    beginAtZero: true,

                                    grid: {{
                                        color:
                                            "rgba(148, 163, 184, 0.15)"
                                    }},

                                    ticks: {{

                                        color: "#64748b",

                                        font: {{
                                            size: 11
                                        }},

                                        callback: function(value) {{

                                            if (
                                                Math.abs(value)
                                                >= 1000000
                                            ) {{

                                                return (
                                                    (
                                                        value / 1000000
                                                    ).toFixed(1)
                                                    + "M"
                                                );

                                            }}

                                            if (
                                                Math.abs(value)
                                                >= 1000
                                            ) {{

                                                return (
                                                    (
                                                        value / 1000
                                                    ).toFixed(1)
                                                    + "K"
                                                );

                                            }}

                                            return value;

                                        }}

                                    }}

                                }}

                            }}

                        }}

                    }}
                );

            }})();
            """
        )

    return "\n".join(
        scripts
    )


# ============================================================
# COMPLETE HTML
# ============================================================

def build_dashboard_html(
    analysis_result,
    kpis,
    charts,
    performers,
    insights,
    recommendations
):
    """Build the complete responsive dashboard HTML."""

    domain = analysis_result.get(
        "domain",
        {}
    )

    if not isinstance(
        domain,
        dict
    ):
        domain = {}

    domain_label = (
        domain.get(
            "domain_label"
        )
        or format_label(
            domain.get(
                "domain",
                "Business Data"
            )
        )
    )

    primary_metric = domain.get(
        "primary_metric"
    )

    date_column = domain.get(
        "date_column"
    )

    id_column = domain.get(
        "id_column"
    )

    metrics = analysis_result.get(
        "metrics",
        {}
    )

    if not isinstance(
        metrics,
        dict
    ):
        metrics = {}

    records = metrics.get(
        "record_count",
        "N/A"
    )

    dataset = analysis_result.get(
        "dataset",
        {}
    )

    if not isinstance(
        dataset,
        dict
    ):
        dataset = {}

    columns = dataset.get(
        "columns",
        "N/A"
    )

    executive_summary = build_executive_summary(
        analysis_result
    )

    performer_html = render_performers(
        performers,
        primary_metric or "metric"
    )

    insights_html = render_list_panel(
        "AI Insights",
        insights,
        "✦"
    )

    recommendations_html = render_list_panel(
        "Recommendations",
        recommendations,
        "→"
    )

    chart_html = render_charts(
        charts
    )

    chart_js = build_chart_javascript(
        charts
    )

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {escape_html(domain_label)}
        Analytics Dashboard
    </title>

    <script
        src="https://cdn.jsdelivr.net/npm/chart.js"
    ></script>

    <style>

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        :root {{
    --bg: #f3f6f8;
    --surface: #ffffff;
    --surface-soft: #f8fafc;
    --border: #e2e8f0;
    --text: #1e293b;
    --muted: #64748b;
    --muted-light: #94a3b8;
    --dark: #0f4c5c;
    --dark-soft: #164e63;
    --accent: #0f4c5c;
    --accent-soft: #e6f3f5;
    --blue: #2563eb;
    --blue-soft: #eff6ff;
    --success: #16a34a;
    --success-soft: #f0fdf4;
    --danger: #dc2626;
    --danger-soft: #fef2f2;
}}

        body {{
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            background: var(--bg);

            color: var(--text);

            min-height: 100vh;
        }}

        .dashboard {{
            width: min(1500px, 100%);

            margin: 0 auto;

            padding: 32px;
        }}

        /* ====================================================
           HERO
           ==================================================== */

        .hero {{
            position: relative;

            overflow: hidden;

            background:
    linear-gradient(
        135deg,
        #0f4c5c,
        #164e63
    );

            color: white;

            border-radius: 26px;

            padding: 42px;

            margin-bottom: 20px;

            box-shadow:
                0 24px 55px
                rgba(15, 23, 42, 0.14);
        }}

        .hero::before {{
            content: "";

            position: absolute;

            width: 420px;
            height: 420px;

            right: -160px;
            bottom: -260px;

            border-radius: 50%;

            background:
    rgba(37, 99, 235, 0.16);
        }}

        .hero::after {{
            content: "";

            position: absolute;

            width: 260px;
            height: 260px;

            right: -80px;
            top: -100px;

            border-radius: 50%;

            background:
                rgba(255, 255, 255, 0.06);
        }}

        .hero-content {{
            position: relative;

            z-index: 1;
        }}

        .hero-topline {{
            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 20px;

            margin-bottom: 18px;
        }}

        .eyebrow {{
            display: inline-block;

            font-size: 11px;

            font-weight: 700;

            letter-spacing: 0.12em;

            color: var(--muted);

            margin-bottom: 8px;
        }}

        .hero .eyebrow {{
            color: #99d5d9;
        }}

        .status-badge {{
            display: inline-flex;

            align-items: center;

            gap: 8px;

            padding: 8px 12px;

            border-radius: 999px;

            background:
                rgba(5, 150, 105, 0.14);

            border:
                1px solid
                rgba(110, 231, 183, 0.18);

            color: #a7f3d0;

            font-size: 11px;

            font-weight: 700;

            white-space: nowrap;
        }}

        .status-dot {{
            width: 7px;
            height: 7px;

            border-radius: 50%;

            background: #34d399;

            box-shadow:
                0 0 0 4px
                rgba(52, 211, 153, 0.12);
        }}

        .hero h1 {{
            font-size:
                clamp(30px, 5vw, 50px);

            line-height: 1.05;

            letter-spacing: -0.03em;

            margin-bottom: 12px;
        }}

        .hero-description {{
            color: #cbd5e1;

            max-width: 780px;

            line-height: 1.7;

            font-size: 15px;
        }}

        .metadata {{
            display: flex;

            flex-wrap: wrap;

            gap: 10px;

            margin-top: 24px;
        }}

        .badge {{
            padding: 9px 14px;

            border-radius: 999px;

            background:
                rgba(255,255,255,0.08);

            border:
                1px solid
                rgba(255,255,255,0.12);

            color: #e2e8f0;

            font-size: 12px;
        }}

        /* ====================================================
           EXECUTIVE SUMMARY
           ==================================================== */

        .summary-panel {{
            display: flex;

            align-items: center;

            gap: 18px;

            background: var(--surface);

            border:
                1px solid var(--border);

            border-radius: 19px;

            padding: 18px 22px;

            margin-bottom: 24px;

            box-shadow:
                0 8px 25px
                rgba(15, 23, 42, 0.04);
        }}

        .summary-icon {{
            display: flex;

            align-items: center;

            justify-content: center;

            width: 42px;
            height: 42px;

            flex-shrink: 0;

            border-radius: 13px;

            background:
                var(--accent-soft);

            color: var(--accent);

            font-size: 18px;

            font-weight: 800;
        }}

        .summary-content {{
            min-width: 0;
        }}

        .summary-title {{
            font-size: 11px;

            font-weight: 800;

            letter-spacing: 0.1em;

            text-transform: uppercase;

            color: var(--muted);

            margin-bottom: 4px;
        }}

        .summary-text {{
            color: #334155;

            font-size: 14px;

            line-height: 1.55;
        }}

        /* ====================================================
           KPI GRID
           ==================================================== */

        .kpi-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(190px, 1fr)
                );

            gap: 16px;

            margin-bottom: 24px;
        }}

        .kpi-card {{
            background: var(--surface);

            border:
                1px solid var(--border);

            border-radius: 19px;

            padding: 22px;

            box-shadow:
                0 8px 25px
                rgba(15, 23, 42, 0.045);

            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease;
        }}

        .kpi-card:hover {{
            transform:
                translateY(-3px);

            box-shadow:
                0 15px 35px
                rgba(15, 23, 42, 0.09);
        }}

        .kpi-card.primary {{
            border-color:
    rgba(15, 76, 92, 0.22);

background:
    linear-gradient(
        145deg,
        #ffffff,
        #f2f9fa
    );
        }}

        .kpi-top {{
            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 10px;

            margin-bottom: 12px;
        }}

        .kpi-label {{
            font-size: 12px;

            font-weight: 700;

            color: var(--muted);

            text-transform: uppercase;

            letter-spacing: 0.06em;
        }}

        .kpi-number {{
            font-size: 10px;

            font-weight: 700;

            color: var(--muted-light);
        }}

        .kpi-value {{
            font-size: 30px;

            font-weight: 800;

            letter-spacing: -0.03em;

            color: var(--dark);

            word-break: break-word;
        }}

        .kpi-card.primary .kpi-value {{
    color: var(--accent);
}}

        .kpi-subtitle {{
            margin-top: 8px;

            font-size: 12px;

            color: var(--muted-light);
        }}

        /* ====================================================
           CHARTS
           ==================================================== */

        .chart-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap: 20px;

            margin-bottom: 24px;
        }}

        .chart-card,
        .panel {{
            background:
    var(--accent-soft);

            border:
                1px solid var(--border);

            border-radius: 21px;

            padding: 24px;

            box-shadow:
                0 8px 25px
                rgba(15, 23, 42, 0.045);

            margin-bottom: 20px;
        }}

        .chart-grid .chart-card:first-child {{
            grid-column: 1 / -1;
        }}

        .section-header {{
            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 20px;

            margin-bottom: 18px;
        }}

        .section-header h2 {{
            font-size: 20px;

            letter-spacing: -0.02em;

            color: var(--dark);
        }}

        .chart-type {{
            padding: 6px 9px;

            border-radius: 8px;

            background:
                var(--surface-soft);

            color: var(--muted);

            font-size: 10px;

            font-weight: 700;

            text-transform: uppercase;

            letter-spacing: 0.06em;
        }}

        .chart-wrapper {{
            height: 350px;

            position: relative;
        }}

        /* ====================================================
           PERFORMANCE
           ==================================================== */

        .performance-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap: 28px;
        }}

        .performance-grid h3 {{
            display: flex;

            align-items: center;

            gap: 8px;

            font-size: 14px;

            margin-bottom: 12px;

            color: var(--dark);
        }}

        .top-performance h3 {{
            color: var(--success);
        }}

        .bottom-performance h3 {{
            color: var(--danger);
        }}

        .performance-dot {{
            width: 7px;
            height: 7px;

            border-radius: 50%;

            display: inline-block;
        }}

        .top-dot {{
            background: var(--success);
        }}

        .bottom-dot {{
            background: var(--danger);
        }}

        table {{
            width: 100%;

            border-collapse: collapse;
        }}

        th,
        td {{
            padding: 12px 10px;

            text-align: left;

            border-bottom:
                1px solid
                #edf1f6;

            font-size: 13px;
        }}

        th {{
            color: var(--muted);

            font-weight: 700;

            font-size: 11px;

            text-transform: uppercase;

            letter-spacing: 0.05em;
        }}

        td:last-child,
        th:last-child {{
            text-align: right;
        }}

        /* ====================================================
           INSIGHTS / RECOMMENDATIONS
           ==================================================== */

        .list-container {{
            display: flex;

            flex-direction: column;

            gap: 10px;
        }}

        .list-item {{
            display: grid;

            grid-template-columns:
                30px 28px minmax(0, 1fr);

            align-items: start;

            gap: 10px;

            padding: 15px;

            border-radius: 14px;

            background:
                var(--surface-soft);

            line-height: 1.55;

            color: #334155;

            font-size: 14px;

            transition:
                transform 0.15s ease,
                background 0.15s ease;
        }}

        .list-item:hover {{
            transform: translateX(2px);

            background:
                var(--accent-soft);
        }}

        .list-index {{
            color: var(--muted-light);

            font-size: 11px;

            font-weight: 700;

            padding-top: 2px;
        }}

        .list-icon {{
            font-weight: 800;

            color: var(--accent);
        }}

        .list-text {{
            min-width: 0;
        }}

        .analysis-count {{
            display: inline-flex;

            align-items: center;

            justify-content: center;

            min-width: 30px;

            height: 26px;

            padding: 0 8px;

            border-radius: 999px;

            background:
                var(--accent-soft);

            color: var(--accent);

            font-size: 10px;

            font-weight: 800;
        }}

        .muted {{
            color: var(--muted-light);

            line-height: 1.6;
        }}

        .empty-panel {{
            grid-column: 1 / -1;
        }}

        .empty-state {{
            background: var(--surface);

            border:
                1px solid var(--border);

            border-radius: 18px;

            padding: 25px;

            color: var(--muted);
        }}

        /* ====================================================
           FOOTER
           ==================================================== */

        .footer {{
            display: flex;

            align-items: center;

            justify-content: center;

            gap: 8px;

            text-align: center;

            color: var(--muted-light);

            font-size: 12px;

            padding: 18px 10px 8px;
        }}

        .footer-dot {{
            width: 5px;
            height: 5px;

            border-radius: 50%;

            background: var(--accent);
        }}

        /* ====================================================
           RESPONSIVE
           ==================================================== */

        @media (max-width: 900px) {{

            .dashboard {{
                padding: 20px;
            }}

            .chart-grid {{
                grid-template-columns: 1fr;
            }}

            .chart-grid .chart-card:first-child {{
                grid-column: auto;
            }}

            .performance-grid {{
                grid-template-columns: 1fr;
            }}

        }}

        @media (max-width: 600px) {{

            .dashboard {{
                padding: 12px;
            }}

            .hero {{
                padding: 27px 23px;

                border-radius: 20px;
            }}

            .hero-topline {{
                align-items: flex-start;

                flex-direction: column;

                gap: 8px;
            }}

            .hero h1 {{
                font-size: 32px;
            }}

            .chart-card,
            .panel {{
                padding: 18px;

                border-radius: 17px;
            }}

            .chart-wrapper {{
                height: 280px;
            }}

            .kpi-value {{
                font-size: 25px;
            }}

            .list-item {{
                grid-template-columns:
                    24px 20px minmax(0, 1fr);
            }}

            .summary-panel {{
                align-items: flex-start;
            }}

        }}

    </style>

</head>


<body>

    <main class="dashboard">

        <!-- =================================================
             HERO
        ================================================== -->

        <section class="hero">

            <div class="hero-content">

                <div class="hero-topline">

                    <span class="eyebrow">
                        PHASE 3 • DYNAMIC DASHBOARD AGENT
                    </span>

                    <span class="status-badge">
                        <span class="status-dot"></span>
                        Analysis Complete
                    </span>

                </div>

                <h1>
                    {escape_html(domain_label)}
                    Analytics
                </h1>

                <p class="hero-description">
                    This dashboard was generated automatically
                    from the detected dataset structure,
                    domain configuration, and verified
                    analysis results.
                </p>

                <div class="metadata">

                    <span class="badge">
                        Domain:
                        {escape_html(domain_label)}
                    </span>

                    <span class="badge">
                        Primary Metric:
                        {escape_html(
                            format_label(
                                primary_metric
                            )
                            if primary_metric
                            else "N/A"
                        )}
                    </span>

                    <span class="badge">
                        Records:
                        {escape_html(
                            format_metric_value(
                                records
                            )
                        )}
                    </span>

                    <span class="badge">
                        Columns:
                        {escape_html(
                            str(columns)
                        )}
                    </span>

                    <span class="badge">
                        Date:
                        {escape_html(
                            format_label(
                                date_column
                            )
                            if date_column
                            else "Not detected"
                        )}
                    </span>

                    <span class="badge">
                        ID:
                        {escape_html(
                            format_label(
                                id_column
                            )
                            if id_column
                            else "Not detected"
                        )}
                    </span>

                </div>

            </div>

        </section>


        <!-- =================================================
             EXECUTIVE SUMMARY
        ================================================== -->

        <section class="summary-panel">

            <div class="summary-icon">
                ✦
            </div>

            <div class="summary-content">

                <div class="summary-title">
                    Executive Summary
                </div>

                <div class="summary-text">
                    {escape_html(
                        executive_summary
                    )}
                </div>

            </div>

        </section>


        <!-- =================================================
             KPIs
        ================================================== -->

        <section class="kpi-grid">

            {render_kpis(kpis)}

        </section>


        <!-- =================================================
             CHARTS
        ================================================== -->

        <section class="chart-grid">

            {chart_html}

        </section>


        <!-- =================================================
             PERFORMANCE
        ================================================== -->

        {performer_html}


        <!-- =================================================
             INSIGHTS
        ================================================== -->

        {insights_html}


        <!-- =================================================
             RECOMMENDATIONS
        ================================================== -->

        {recommendations_html}


        <!-- =================================================
             FOOTER
        ================================================== -->

        <footer class="footer">

            <span class="footer-dot"></span>

            Generated automatically by the
            Phase 3 Dashboard Agent

        </footer>

    </main>


    <script>

        {chart_js}

    </script>

</body>

</html>
"""


# ============================================================
# MAIN DASHBOARD FUNCTION
# ============================================================

def generate_dashboard(
    analysis_result,
    output_file="generated-dashboard/dashboard.html"
):
    """
    Generate a production-style dashboard from the actual
    Analysis Agent result.

    The function is intentionally deterministic so the LLM
    does not generate arbitrary executable dashboard code.
    """

    print("\n" + "=" * 60)
    print("DASHBOARD AGENT")
    print("=" * 60)

    # --------------------------------------------------------
    # VALIDATE INPUT
    # --------------------------------------------------------

    if not isinstance(
        analysis_result,
        dict
    ):

        error = (
            "Analysis result must be a dictionary."
        )

        print(
            f"\nDASHBOARD ERROR: {error}"
        )

        return {
            "status": "error",
            "output_file": output_file,
            "error": error,
        }

    if analysis_result.get(
        "status"
    ) != "success":

        error = (
            "Analysis result is not successful."
        )

        print(
            f"\nDASHBOARD ERROR: {error}"
        )

        return {
            "status": "error",
            "output_file": output_file,
            "error": error,
        }

    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    try:

        output_path = Path(
            output_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    except Exception as exc:

        print(
            f"\nFailed to prepare output directory: {exc}"
        )

        return {
            "status": "error",
            "output_file": output_file,
            "error": str(exc),
        }

    print(
        f"\nOutput file: {output_path}"
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    print(
        "\n[1] Building KPI cards..."
    )

    kpis = build_kpi_cards(
        analysis_result
    )

    print(
        f"KPI cards generated: {len(kpis)}"
    )

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    print(
        "\n[2] Building charts..."
    )

    charts = build_chart_data(
        analysis_result
    )

    print(
        f"Charts generated: {len(charts)}"
    )

    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    print(
        "\n[3] Building performance sections..."
    )

    performers = build_performer_sections(
        analysis_result
    )

    print(
        f"Performance sections: {len(performers)}"
    )

    # --------------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------------

    print(
        "\n[4] Building insights..."
    )

    insights = build_insight_cards(
        analysis_result
    )

    recommendations = build_recommendations(
        analysis_result
    )

    print(
        f"Insights: {len(insights)}"
    )

    print(
        f"Recommendations: {len(recommendations)}"
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    print(
        "\n[5] Rendering dashboard HTML..."
    )

    dashboard_html = build_dashboard_html(
        analysis_result,
        kpis,
        charts,
        performers,
        insights,
        recommendations
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print(
        "[6] Saving dashboard..."
    )

    try:

        output_path.write_text(
            dashboard_html,
            encoding="utf-8"
        )

    except Exception as exc:

        print(
            f"\nFailed to save dashboard: {exc}"
        )

        return {
            "status": "error",
            "output_file": str(
                output_path
            ),
            "error": str(exc),
        }

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "\nDashboard saved successfully."
    )

    return {
        "status": "success",
        "output_file": str(
            output_path
        ),
        "charts_generated": len(charts),
        "kpis_generated": len(kpis),
        "performance_sections": len(performers),
        "insights_displayed": len(insights),
        "recommendations_displayed": len(
            recommendations
        ),
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    from domain_config_agent import configure_domain
    from analysis_agent import analyze_dataset

    input_file = (
        "test-datasets/"
        "saas_subscriptions.csv"
    )

    cleaned_file = (
        "test-datasets/"
        "cleaned_saas_subscriptions.csv"
    )

    # --------------------------------------------------------
    # DOMAIN CONFIGURATION
    # --------------------------------------------------------

    print(
        "\nRunning Domain Configuration Agent..."
    )

    config = configure_domain(
        input_file
    )

    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

    print(
        "\nRunning Analysis Agent..."
    )

    analysis = analyze_dataset(
        cleaned_file,
        config
    )

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    result = generate_dashboard(
        analysis
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "\nDASHBOARD RESULT:"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )