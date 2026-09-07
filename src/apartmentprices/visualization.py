from typing import Literal

import contextily as cx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def distribution(x: pd.Series):

    sns.set_theme(style="white", palette="pastel")

    _fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    sns.histplot(
        data=x,
        kde=True,
        bins=50,
        color="#2B5C8F",
        edgecolor="white",
        linewidth=1.2,
        alpha=0.6,
        ax=ax,
    )

    line = ax.lines[0]
    line.set_color("#1A365D")
    line.set_linewidth(2.5)

    ax.set_title(f"Distribution of {x.name}", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel(f"{x.name}", fontsize=15, labelpad=8)
    ax.set_ylabel("Count", fontsize=11, labelpad=8)

    sns.despine(top=True, right=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()


def barplot(x: pd.Series):

    sns.set_theme(style="white", palette="pastel")

    _fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    sns.countplot(
        x=x,
        color="#2B5C8F",
        edgecolor="white",
        linewidth=1.2,
        alpha=0.6,
        ax=ax,
    )

    ax.set_title(f"Distribution of {x.name}", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel(f"{x.name}", fontsize=15, labelpad=8)
    ax.set_ylabel("Count", fontsize=11, labelpad=8)

    ax.tick_params(axis="x", rotation=45)

    sns.despine(top=True, right=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()


def scatterplot(x: pd.Series, y: pd.Series):

    sns.set_theme(style="white", palette="pastel")

    _fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    sns.scatterplot(
        x=x,
        y=y,
        color="#2B5C8F",
        edgecolor="white",
        linewidth=0.8,
        alpha=0.6,
        s=60,
        ax=ax,
    )

    ax.set_title(f"{y.name} vs {x.name}", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel(f"{x.name}", fontsize=15, labelpad=8)
    ax.set_ylabel(f"{y.name}", fontsize=11, labelpad=8)

    sns.despine(top=True, right=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()


def boxplot(
    x: pd.Series,
    y: pd.Series,
    orientation: Literal["vertical", "horizontal"] = "vertical",
    show_fliers: bool = False,
):
    sns.set_theme(style="white", palette="pastel")

    is_vertical = orientation == "vertical"
    n_categories = x.nunique() if is_vertical else y.nunique()

    if is_vertical:
        width = min(max(9, n_categories * 0.5), 30)
        figsize = (width, 5)
    else:
        height = min(max(5, n_categories * 0.28), 20)
        figsize = (9, height)

    _fig, ax = plt.subplots(figsize=figsize, dpi=150)

    plot_x, plot_y = (x, y) if is_vertical else (y, x)

    sns.boxplot(
        x=plot_x,
        y=plot_y,
        color="#2B5C8F",
        linewidth=1.2,
        showfliers=show_fliers,
        boxprops={"alpha": 0.6, "edgecolor": "white"},
        medianprops={"color": "#1A365D", "linewidth": 2.5},
        whiskerprops={"color": "#1A365D"},
        capprops={"color": "#1A365D"},
        flierprops={
            "markerfacecolor": "#2B5C8F",
            "markeredgecolor": "white",
            "alpha": 0.6,
        },
        ax=ax,
    )

    ax.set_title(f"{y.name} by {x.name}", fontsize=14, weight="bold", pad=15)
    ax.set_xlabel(f"{plot_x.name}", fontsize=12, labelpad=8)
    ax.set_ylabel(f"{plot_y.name}", fontsize=11, labelpad=8)

    if is_vertical:
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
    else:
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", linestyle="--", alpha=0.5)

    sns.despine(top=True, right=True)
    plt.tight_layout()


def heatmap(data: pd.DataFrame, annot: bool = True, mask_upper: bool = True):
    corr = data.select_dtypes(include="number").corr()

    sns.set_theme(style="white", palette="pastel")
    _fig, ax = plt.subplots(figsize=(9, 7), dpi=150)

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1) if mask_upper else None
    cmap = sns.light_palette("#2B5C8F", as_cmap=True)

    sns.heatmap(
        corr,
        annot=annot,
        fmt=".2f",
        cmap=cmap,
        mask=mask,
        linewidths=1.2,
        linecolor="white",
        cbar_kws={"shrink": 0.8},
        annot_kws={"color": "#1A365D"},
        ax=ax,
    )

    ax.set_title("Correlation Heatmap", fontsize=14, weight="bold", pad=15)
    plt.tight_layout()


def mapplot(df):

    # for coloring
    log_price = np.log(df["price"])

    sns.set_theme(style="white", palette="pastel")

    _fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    sns.scatterplot(
        data=df,
        x="lng",
        y="lat",
        hue=log_price,
        size=df.groupby(["lng", "lat"])["lng"].transform("count"),
        sizes=(20, 200),
        alpha=0.6,
        legend=False,
        ax=ax,
    )

    cx.add_basemap(
        ax,
        crs="EPSG:4326",
        source=cx.providers.OpenStreetMap.Mapnik,
        headers={"User-Agent": "BakuApartmentPrices/1.0 (aslanliaslan450@gmail.com)"},
    )

    ax.axis("off")

    plt.tight_layout()
