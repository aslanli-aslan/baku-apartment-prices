import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import contextily as cx


def distribution(x: pd.Series):

    sns.set_theme(style="white", palette="pastel")

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

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


def mapplot(df):

    # for coloring
    log_price = np.log(df["price"])

    sns.set_theme(style="white", palette="pastel")

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    sns.scatterplot(
        data=df,
        x="lng",
        y="lat",
        hue=log_price,
        size=df.groupby(["lng", "lat"])["lng"].transform("count"),
        sizes=(20,200),
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