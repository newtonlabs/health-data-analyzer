import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from ..reporting_config import ReportingConfig


class ChartGenerator:
    """Base class for chart generators."""

    def __init__(self, charts_dir: Optional[str] = None):
        """Initialize chart generator with output directory."""
        self.charts_dir = charts_dir or os.path.join("data", "charts")
        os.makedirs(self.charts_dir, exist_ok=True)

    def _setup_chart_figure(
        self, figsize: tuple[float, float]
    ) -> tuple[plt.Figure, plt.Axes]:
        """Initializes a Matplotlib figure and axes with a white background."""
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        return fig, ax

    def _style_axes(
        self,
        ax: plt.Axes,
        x_labels: Optional[list[str]] = None,
        y_label: Optional[str] = None,
        x_label: Optional[str] = None,
        x_ticks: Optional[np.ndarray] = None,
        y_lim: Optional[tuple[float, float]] = None,
        y_ticks: Optional[list[float]] = None,
        secondary_ax: Optional[plt.Axes] = None,
        grid_axis: Optional[str] = "both",
        grid_color: str = ReportingConfig.COLORS["grid"],
        spines_to_hide: Optional[list[str]] = None,
        spines_to_color: Optional[dict[str, str]] = None,
        tick_label_color: str = ReportingConfig.COLORS["text"],
        axis_label_color: str = ReportingConfig.COLORS["text"],
        font_size: int = ReportingConfig.STYLING["default_font_size"],
        tick_font_size: int = ReportingConfig.STYLING["tick_font_size"],
        grid_line_width: float = ReportingConfig.STYLING["grid_line_width"],
        grid_opacity: float = ReportingConfig.STYLING["grid_opacity"],
    ):
        """Applies common styling to Matplotlib axes."""
        if y_lim:
            ax.set_ylim(y_lim)
        if x_ticks is not None:
            ax.set_xticks(x_ticks)
        if x_labels:
            ax.set_xticklabels(
                x_labels, color=tick_label_color, fontsize=tick_font_size
            )
        if y_ticks:
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_ticks, color=tick_label_color, fontsize=tick_font_size)

        ax.set_xlabel(
            x_label if x_label is not None else "",
            color=axis_label_color,
            fontsize=font_size,
        )
        ax.set_ylabel(
            y_label if y_label is not None else "",
            color=axis_label_color,
            fontsize=font_size,
        )
        ax.tick_params(axis="both", colors=tick_label_color, labelsize=tick_font_size)

        ax.grid(
            True,
            linestyle=":",
            linewidth=grid_line_width,
            alpha=grid_opacity,
            color=grid_color,
            axis=grid_axis,
        )

        # Configure spines
        default_spines_to_hide = ["top", "right"]
        spines_to_hide = (
            spines_to_hide if spines_to_hide is not None else default_spines_to_hide
        )
        for spine in spines_to_hide:
            ax.spines[spine].set_visible(False)

        for spine_name in ["top", "bottom", "left", "right"]:
            if spine_name not in spines_to_hide:
                ax.spines[spine_name].set_visible(True)
                ax.spines[spine_name].set_color(
                    spines_to_color.get(spine_name, ReportingConfig.COLORS["grid"])
                    if spines_to_color
                    else ReportingConfig.COLORS["grid"]
                )

        if secondary_ax:
            secondary_ax.tick_params(
                axis="y", colors=tick_label_color, labelsize=tick_font_size
            )
            for spine_name in ["top", "bottom", "left", "right"]:
                if spine_name not in spines_to_hide:
                    secondary_ax.spines[spine_name].set_visible(True)
                    secondary_ax.spines[spine_name].set_color(
                        spines_to_color.get(spine_name, ReportingConfig.COLORS["grid"])
                        if spines_to_color
                        else ReportingConfig.COLORS["grid"]
                    )

    def _save_chart(
        self, fig: plt.Figure, filename: str, extra_artists: Optional[tuple] = None
    ) -> str:
        """Saves the chart to a file and closes the figure."""
        plt.tight_layout()
        output_path = os.path.join(self.charts_dir, filename)
        if extra_artists:
            plt.savefig(
                output_path,
                dpi=300,
                bbox_inches="tight",
                bbox_extra_artists=extra_artists,
            )
        else:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path
