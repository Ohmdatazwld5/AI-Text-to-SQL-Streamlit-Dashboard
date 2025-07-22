"""
graph_utils.py

Chart selection & rendering utilities for the Text-to-SQL Streamlit app.
- decide_chart_type(): infer chart type from user query keywords and/or dataframe structure.
- plot_chart(): render matplotlib chart -> base64 image string suitable for st.image().
"""

import io
import base64
import matplotlib.pyplot as plt
import pandas as pd


# ------------------------------------------------------------------ #
# Chart type selection
# ------------------------------------------------------------------ #
def decide_chart_type(user_query: str, df: pd.DataFrame | None = None) -> str | None:
    """
    Decide which chart to render.

    Priority:
      1. Keyword signals in user query.
      2. Data-driven heuristics (df inspection).

    Returns: 'bar' | 'line' | 'pie' | None
    """
    q = user_query.lower()

    # Keyword-driven
    if any(k in q for k in ("trend", "over time", "line chart", "month", "year")):
        return "line"
    if any(k in q for k in ("percentage", "distribution", "share", "pie")):
        return "pie"
    if any(k in q for k in ("top", "compare", "vs", "bar")):
        return "bar"

    # Data-driven fallback
    if df is not None and df.shape[1] >= 2:
        x_dtype = df.iloc[:, 0].dtype
        y_dtype = df.iloc[:, 1].dtype

        # numeric y + categorical x -> bar
        if y_dtype.kind in "iufc" and x_dtype.kind not in "iufc":
            return "bar"
        # numeric y + numeric x -> line
        if y_dtype.kind in "iufc" and x_dtype.kind in "iufc":
            return "line"
        # small set of rows -> pie
        if len(df) <= 6:
            return "pie"

    return None


# ------------------------------------------------------------------ #
# Helpers for pie chart (legend mode & "Other" grouping)
# ------------------------------------------------------------------ #
def _group_small_slices(labels, values, min_frac=0.02):
    """
    Group slices contributing less than `min_frac` of total into a single 'Other' slice.
    Returns (new_labels, new_values).
    """
    total = float(sum(values)) or 1.0
    keep_labels = []
    keep_vals = []
    other_val = 0.0

    for lbl, val in zip(labels, values):
        if (val / total) < min_frac:
            other_val += val
        else:
            keep_labels.append(lbl)
            keep_vals.append(val)

    if other_val > 0:
        keep_labels.append("Other")
        keep_vals.append(other_val)

    return keep_labels, keep_vals


# ------------------------------------------------------------------ #
# Chart rendering
# ------------------------------------------------------------------ #
def plot_chart(
    df: pd.DataFrame,
    chart_type: str,
    user_query: str = "",
    *,
    top_n_barline: int = 10,
    pie_legend_threshold: int = 8,
    pie_other_min_frac: float = 0.02,
) -> str | None:
    """
    Render a chart from the first two columns of df.

    Parameters
    ----------
    df : DataFrame
        Result set (at least 2 columns).
    chart_type : str
        'bar' | 'line' | 'pie'.
    user_query : str
        Used for dynamic title.
    top_n_barline : int
        Max rows to display for bar/line charts (largest by 2nd column).
    pie_legend_threshold : int
        If #slices > this, switch to legend mode (labels in legend, not wedges).
    pie_other_min_frac : float
        Fractional cutoff for grouping tiny slices into 'Other' (legend mode only).

    Returns
    -------
    data_uri : str | None
        Base64-encoded PNG image, or None if invalid input.
    """
    if df is None or df.shape[1] < 2:
        return None

    # Defensive copy
    work_df = df.copy()

    # Coerce to simple Series for plotting
    x_col = work_df.columns[0]
    y_col = work_df.columns[1]

    # For bar/line readability: show top N by y
    if chart_type in ("bar", "line") and len(work_df) > top_n_barline:
        # sort descending by numeric value if possible
        try:
            work_df = work_df.sort_values(by=y_col, ascending=False).head(top_n_barline)
        except Exception:
            work_df = work_df.head(top_n_barline)

    x = work_df.iloc[:, 0]
    y = work_df.iloc[:, 1]

    fig, ax = plt.subplots(figsize=(7, 4))

    if chart_type == "bar":
        ax.bar(x, y)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.tick_params(axis='x', labelrotation=45)

    elif chart_type == "line":
        ax.plot(x, y, marker='o')
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.tick_params(axis='x', labelrotation=45)

    elif chart_type == "pie":
        values = list(y)
        labels = list(x.astype(str))

        # PIE MODE A: small slice count -> label wedges directly
        if len(values) <= pie_legend_threshold:
            max_val = max(values) if values else 0
            explode = [0.05 if v == max_val else 0 for v in values]

            ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                pctdistance=0.8,     # % text closer to center
                labeldistance=1.1,   # labels pushed out a bit
                startangle=90,
                counterclock=False,
                explode=explode,
            )

        # PIE MODE B: many slices -> group tiny + legend
        else:
            # Group tiny slices
            labels, values = _group_small_slices(labels, values, min_frac=pie_other_min_frac)

            wedges, _texts = ax.pie(
                values,
                startangle=90,
                counterclock=False,
                autopct=None,  # no % on wedges; legend instead
            )
            ax.legend(
                wedges,
                labels,
                title=x_col,
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
            )

        ax.axis('equal')  # keep circle

    # Dynamic title (trimmed)
    if user_query:
        ax.set_title(f"{user_query[:60]}{'...' if len(user_query) > 60 else ''}")

    fig.tight_layout()

    # Encode to base64 for Streamlit
    buf = io.BytesIO()
    # bbox_inches='tight' ensures legend is included when present
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return f"data:image/png;base64,{encoded}"




