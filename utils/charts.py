"""
utils/charts.py
===============
Factory functions that produce fully-styled Plotly figures.

Rules:
  • Every function returns a plotly.graph_objects.Figure — never renders it.
    The page module calls st.plotly_chart(fig, use_container_width=True).
  • All colour constants are imported from config/settings.py so the palette
    stays in sync with the CSS variables in config/styles.py.
  • No Streamlit imports here — these are pure Plotly helpers.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import (
    COLOR_GREEN_DEEP, COLOR_GREEN_MID, COLOR_GREEN_LIGHT, COLOR_GREEN_PALE,
    COLOR_GOLD, COLOR_GOLD_LIGHT, COLOR_EARTH, COLOR_CREAM,
    PLOTLY_GREEN_SCALE, DEFAULT_CHART_HEIGHT,
)

# ── shared layout defaults applied to every figure ───────────────────────────
_BASE_LAYOUT = dict(
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    margin        = dict(l=0, r=0, t=10, b=0),
    font          = dict(family="DM Sans", color=COLOR_GREEN_DEEP),
)


def _apply(fig: go.Figure, height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    """Apply base layout + height to any figure and return it."""
    fig.update_layout(**_BASE_LAYOUT, height=height)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Horizontal bar — e.g. total harvest by region
# ─────────────────────────────────────────────────────────────────────────────
def bar_horizontal(df: pd.DataFrame,
                   x: str, y: str,
                   color_col: str | None = None,
                   height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    fig = px.bar(
        df, x=x, y=y, orientation="h",
        color=color_col if color_col else x,
        color_continuous_scale=PLOTLY_GREEN_SCALE,
    )
    fig.update_layout(coloraxis_showscale=False, yaxis=dict(tickfont=dict(size=11)))
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Vertical bar — e.g. average water volume per crop
# ─────────────────────────────────────────────────────────────────────────────
def bar_vertical(df: pd.DataFrame,
                 x: str, y: str,
                 color_col: str | None = None,
                 color_scale=None,
                 height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    scale = color_scale or PLOTLY_GREEN_SCALE
    fig = px.bar(
        df, x=x, y=y,
        color=color_col if color_col else y,
        color_continuous_scale=scale,
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-30)
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Grouped bar — e.g. yield per variety grouped by region
# ─────────────────────────────────────────────────────────────────────────────
def bar_grouped(df: pd.DataFrame,
                x: str, y: str, color: str,
                height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    fig = px.bar(
        df, x=x, y=y, color=color, barmode="group",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(xaxis_tickangle=-30)
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Pie / donut — e.g. crop breakdown by season
# ─────────────────────────────────────────────────────────────────────────────
def pie_donut(df: pd.DataFrame,
              values: str, names: str,
              height: int = 280) -> go.Figure:
    fig = px.pie(
        df, values=values, names=names,
        color_discrete_sequence=[COLOR_GREEN_MID, COLOR_GOLD,
                                  COLOR_GREEN_LIGHT, COLOR_EARTH,
                                  COLOR_GREEN_PALE, COLOR_GOLD_LIGHT],
        hole=0.55,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(showlegend=False)
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Scatter — e.g. growth cycle vs. avg yield
# ─────────────────────────────────────────────────────────────────────────────
def scatter(df: pd.DataFrame,
            x: str, y: str,
            color: str | None = None,
            hover_name: str | None = None,
            height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    fig = px.scatter(
        df, x=x, y=y,
        color=color,
        hover_name=hover_name,
        color_discrete_sequence=px.colors.qualitative.Dark24,
        size_max=12,
    )
    fig.update_layout(legend=dict(font=dict(size=10)))
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Histogram — e.g. growth cycle distribution
# ─────────────────────────────────────────────────────────────────────────────
def histogram(df: pd.DataFrame,
              x: str,
              color: str | None = None,
              nbins: int = 15,
              height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    fig = px.histogram(
        df, x=x, color=color, nbins=nbins, barmode="overlay",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Funnel — top N varieties by avg yield
# ─────────────────────────────────────────────────────────────────────────────
def funnel(df: pd.DataFrame,
           x: str, y: str,
           top_n: int = 10,
           height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    fig = px.funnel(
        df.head(top_n), x=x, y=y,
        color_discrete_sequence=[COLOR_GREEN_MID],
    )
    return _apply(fig, height)


# ─────────────────────────────────────────────────────────────────────────────
# Treemap — hierarchical breakdown
# ─────────────────────────────────────────────────────────────────────────────
def treemap(df: pd.DataFrame,
            path: list,
            color: str,
            hover_data: list | None = None,
            height: int = 400) -> go.Figure:
    fig = px.treemap(
        df, path=path,
        color=color,
        color_continuous_scale=PLOTLY_GREEN_SCALE,
        hover_data=hover_data,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                      font=dict(family="DM Sans"),
                      height=height)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Bar with reference line — e.g. germination vs. threshold
# ─────────────────────────────────────────────────────────────────────────────
def bar_with_threshold(df: pd.DataFrame,
                       x: str, y: str,
                       threshold: float,
                       color_scale=None,
                       color_range: list | None = None,
                       height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    scale = color_scale or [COLOR_GOLD, COLOR_GOLD_LIGHT]
    fig = px.bar(
        df, x=x, y=y,
        color=y,
        color_continuous_scale=scale,
        range_color=color_range,
    )
    fig.add_hline(
        y=threshold, line_dash="dash",
        line_color=COLOR_EARTH,
        annotation_text=f"Threshold: {threshold}",
        annotation_font_color=COLOR_EARTH,
    )
    fig.update_layout(coloraxis_showscale=False)
    return _apply(fig, height)
