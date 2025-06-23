from .base import ChartGenerator
from ..reporting_config import ReportingConfig


class MacroRatioChartGenerator(ChartGenerator):
    """Generates HTML/CSS visualization for macronutrient ratios."""

    def generate_html(
        self, protein_pct: float, carbs_pct: float, fat_pct: float
    ) -> str:
        """
        Generate HTML for macronutrient ratio visualization.

        Args:
            protein_pct: Protein percentage (0-100)
            carbs_pct: Carbohydrate percentage (0-100)
            fat_pct: Fat percentage (0-100)

        Returns:
            HTML string for the visualization
        """
        # Visual progress bar with text inside bars
        html = ["<div class='progress-container'>"]

        # Round values to 1 decimal place for consistency
        protein_pct_rounded = round(protein_pct, 1)
        carbs_pct_rounded = round(carbs_pct, 1)
        fat_pct_rounded = round(fat_pct, 1)

        # Add text inside each bar section with macro names on same line as percentage
        html.append(
            f"  <div class='progress-protein' style='width: {protein_pct_rounded}%'>"
            + (
                f"<span class='macro-text'>Protein {protein_pct_rounded}%</span>"
                if protein_pct >= ReportingConfig.THRESHOLDS["macro_label_full"]
                else (
                    f"<span class='macro-text'>{protein_pct_rounded}%</span>"
                    if protein_pct >= ReportingConfig.THRESHOLDS["macro_label_percent"]
                    else ""
                )
            )
            + "</div>"
            + f"<div class='progress-carbs' style='width: {carbs_pct_rounded}%'>"
            + (
                f"<span class='macro-text'>Carbs {carbs_pct_rounded}%</span>"
                if carbs_pct >= ReportingConfig.THRESHOLDS["macro_label_full"]
                else (
                    f"<span class='macro-text'>{carbs_pct_rounded}%</span>"
                    if carbs_pct >= ReportingConfig.THRESHOLDS["macro_label_percent"]
                    else ""
                )
            )
            + "</div>"
            + f"<div class='progress-fat' style='width: {fat_pct_rounded}%'>"
            + (
                f"<span class='macro-text'>Fat {fat_pct_rounded}%</span>"
                if fat_pct >= ReportingConfig.THRESHOLDS["macro_label_full"]
                else (
                    f"<span class='macro-text'>{fat_pct_rounded}%</span>"
                    if fat_pct >= ReportingConfig.THRESHOLDS["macro_label_percent"]
                    else ""
                )
            )
            + "</div>"
        )

        html.append("</div>")

        return "\n".join(html)
