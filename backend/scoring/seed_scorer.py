"""
scoring/seed_scorer.py
──────────────────────
Scoring pipeline for seed / batch DataFrames that already carry ML model
output columns:

    text, predicted_label, confidence,
    probability_negative, probability_neutral, probability_positive

Adds three derived columns:
    risk_score      – 0–100 float
    risk_band       – Low / Guarded / Elevated / High
    model_certainty – High / Medium / Low

Supports optional aggregation by: country, country_pair, entity, date.

Usage (standalone):
    python -m scoring.seed_scorer                    # uses built-in demo data
    python -m scoring.seed_scorer --input my.csv     # score an existing CSV

Usage (library):
    from scoring.seed_scorer import score_dataframe, aggregate, export

    df = pd.read_csv("my_predictions.csv")
    scored = score_dataframe(df)
    agg    = aggregate(scored, by="country")
    export(scored, prefix="output/scored")
"""
from __future__ import annotations

import argparse
import logging
import os
from typing import Literal, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

PROB_COLS = ["probability_negative", "probability_neutral", "probability_positive"]

RISK_BAND_BINS   = [0, 25, 50, 75, 101]          # right-exclusive upper bound
RISK_BAND_LABELS = ["Low", "Guarded", "Elevated", "High"]

CERTAINTY_HIGH   = 0.80
CERTAINTY_MEDIUM = 0.55

AggBy = Literal["country", "country_pair", "entity", "date"]


# ── Validation ────────────────────────────────────────────────────────────────

def validate_probabilities(df: pd.DataFrame, tol: float = 1e-3) -> pd.DataFrame:
    """
    Verify that probability_negative + probability_neutral + probability_positive
    sums to ~1.0 for every row.  Rows that fail are flagged in a new column
    `prob_sum_ok` (bool) and a warning is logged — they are NOT dropped so the
    caller can decide what to do with them.

    Returns the DataFrame with the `prob_sum_ok` column added.
    """
    missing = [c for c in PROB_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required probability columns: {missing}")

    prob_sum = df[PROB_COLS].sum(axis=1)
    ok_mask  = (prob_sum - 1.0).abs() <= tol
    df = df.copy()
    df["prob_sum_ok"] = ok_mask

    bad_count = (~ok_mask).sum()
    if bad_count:
        logger.warning(
            f"validate_probabilities: {bad_count} row(s) have probability sums "
            f"outside ±{tol} of 1.0 — check your model output."
        )
    else:
        logger.debug("validate_probabilities: all rows pass (sum ≈ 1.0).")

    return df


# ── Core scoring functions ────────────────────────────────────────────────────

def compute_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    risk_score = 100 × (P_negative + 0.5 × P_neutral)
    Clipped to [0, 100].
    """
    raw = 100.0 * (df["probability_negative"] + 0.5 * df["probability_neutral"])
    return raw.clip(lower=0.0, upper=100.0).round(2)


def assign_risk_band(risk_score: pd.Series) -> pd.Series:
    """
    Map a numeric risk_score series to labelled bands:
        0–24   → Low
        25–49  → Guarded
        50–74  → Elevated
        75–100 → High
    """
    return pd.cut(
        risk_score,
        bins=RISK_BAND_BINS,
        labels=RISK_BAND_LABELS,
        right=False,          # [0,25) [25,50) [50,75) [75,101)
        include_lowest=True,
    ).astype(str)


def assign_model_certainty(confidence: pd.Series) -> pd.Series:
    """
    Map confidence scores to certainty tiers:
        >= 0.80  → High
        >= 0.55  → Medium
        <  0.55  → Low
    """
    conditions = [
        confidence >= CERTAINTY_HIGH,
        confidence >= CERTAINTY_MEDIUM,
    ]
    choices = ["High", "Medium"]
    return pd.Series(
        pd.np.select(conditions, choices, default="Low"),
        index=confidence.index,
        dtype="string",
    ) if hasattr(pd, "np") else _certainty_via_cut(confidence)


def _certainty_via_cut(confidence: pd.Series) -> pd.Series:
    """Fallback for pandas versions without pd.np (pandas ≥ 2.0)."""
    import numpy as np
    result = np.select(
        [confidence >= CERTAINTY_HIGH, confidence >= CERTAINTY_MEDIUM],
        ["High", "Medium"],
        default="Low",
    )
    return pd.Series(result, index=confidence.index, dtype="string")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full scoring pipeline.

    Expects columns: text, predicted_label, confidence,
                     probability_negative, probability_neutral, probability_positive

    Adds columns:    risk_score, risk_band, model_certainty, prob_sum_ok

    Returns a new DataFrame (original is not mutated).
    """
    required = ["confidence"] + PROB_COLS
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"score_dataframe: input DataFrame is missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    out = df.copy()

    # 1. Validate probability sums
    out = validate_probabilities(out)

    # 2. Compute risk_score
    out["risk_score"] = compute_risk_score(out)

    # 3. Assign risk_band
    out["risk_band"] = assign_risk_band(out["risk_score"])

    # 4. Assign model_certainty
    out["model_certainty"] = _certainty_via_cut(out["confidence"])

    logger.info(
        f"score_dataframe: scored {len(out)} rows — "
        f"band distribution:\n{out['risk_band'].value_counts().to_string()}"
    )
    return out


# ── Aggregation ───────────────────────────────────────────────────────────────

_AGG_SPEC = {
    "risk_score":    ["mean", "max", "min", "std", "count"],
    "confidence":    ["mean"],
}


def _optional_agg_col(df: pd.DataFrame, col: str) -> Optional[str]:
    """Return col if it exists in df, else None."""
    return col if col in df.columns else None


def aggregate(df: pd.DataFrame, by: AggBy) -> pd.DataFrame:
    """
    Aggregate scored rows by a grouping dimension.

    Supported values for `by`:
        "country"      – requires column `country`
        "country_pair" – requires column `country_pair`
        "entity"       – requires column `entity`
        "date"         – requires column `date` (any date-like column)

    Returns a summary DataFrame with mean/max/min/std/count of risk_score
    and mean confidence per group.  Raises ValueError if the required column
    is absent.
    """
    col_map: dict[AggBy, str] = {
        "country":      "country",
        "country_pair": "country_pair",
        "entity":       "entity",
        "date":         "date",
    }
    group_col = col_map.get(by)
    if group_col is None:
        raise ValueError(f"aggregate: unknown grouping '{by}'. Choose from {list(col_map)}")
    if group_col not in df.columns:
        raise ValueError(
            f"aggregate(by='{by}'): column '{group_col}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    agg_df = (
        df.groupby(group_col)
          .agg(**{
              "avg_risk_score":  ("risk_score", "mean"),
              "max_risk_score":  ("risk_score", "max"),
              "min_risk_score":  ("risk_score", "min"),
              "std_risk_score":  ("risk_score", "std"),
              "row_count":       ("risk_score", "count"),
              "avg_confidence":  ("confidence", "mean"),
          })
          .round(3)
          .sort_values("avg_risk_score", ascending=False)
          .reset_index()
    )

    # Dominant risk band per group
    if "risk_band" in df.columns:
        dominant_band = (
            df.groupby(group_col)["risk_band"]
              .agg(lambda s: s.value_counts().idxmax())
              .rename("dominant_risk_band")
        )
        agg_df = agg_df.merge(dominant_band, on=group_col, how="left")

    logger.info(f"aggregate(by='{by}'): {len(agg_df)} groups.")
    return agg_df


# ── Export ────────────────────────────────────────────────────────────────────

def export(df: pd.DataFrame, prefix: str = "scored_output") -> dict[str, str]:
    """
    Export the scored DataFrame to CSV and Parquet.

    Parameters
    ----------
    df     : scored DataFrame (output of score_dataframe)
    prefix : file path prefix, e.g. "output/scored" → writes
             output/scored.csv and output/scored.parquet

    Returns a dict with keys "csv" and "parquet" pointing to the written paths.
    """
    os.makedirs(os.path.dirname(prefix) if os.path.dirname(prefix) else ".", exist_ok=True)

    csv_path     = f"{prefix}.csv"
    parquet_path = f"{prefix}.parquet"

    df.to_csv(csv_path, index=False)
    logger.info(f"export: wrote {len(df)} rows → {csv_path}")

    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    logger.info(f"export: wrote {len(df)} rows → {parquet_path}")

    return {"csv": csv_path, "parquet": parquet_path}


# ── Preview ───────────────────────────────────────────────────────────────────

def top_risk_preview(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Return the top-n highest-risk rows, sorted by risk_score descending.
    Selects the most informative columns for quick inspection.
    """
    display_cols = [
        c for c in [
            "text", "country", "country_pair", "entity", "date",
            "predicted_label", "confidence", "model_certainty",
            "probability_negative", "probability_neutral", "probability_positive",
            "risk_score", "risk_band",
        ]
        if c in df.columns
    ]
    return (
        df.sort_values("risk_score", ascending=False)
          .head(n)[display_cols]
          .reset_index(drop=True)
    )


# ── Demo / CLI entry point ────────────────────────────────────────────────────

def _build_demo_df() -> pd.DataFrame:
    """
    Construct a small demo DataFrame that mirrors the seed data structure
    (country pairs, realistic probability distributions).
    """
    import numpy as np

    rng = np.random.default_rng(42)

    pairs = [
        ("CN", "US"), ("IN", "PK"), ("RU", "UA"), ("IL", "IR"),
        ("IN", "CN"), ("KP", "US"), ("KP", "KR"), ("IL", "SA"),
        ("RU", "GB"), ("CN", "TW"), ("TR", "GR"), ("IN", "US"),
    ]

    rows = []
    for a, b in pairs:
        for _ in range(10):          # 10 posts per pair
            p_neg = float(rng.beta(3, 2))          # skewed negative
            p_pos = float(rng.beta(1, 4))
            p_neu = max(0.0, 1.0 - p_neg - p_pos)
            # Renormalise to sum exactly to 1
            total = p_neg + p_neu + p_pos
            p_neg, p_neu, p_pos = p_neg / total, p_neu / total, p_pos / total

            conf = float(rng.uniform(0.45, 0.98))
            label = "negative" if p_neg > p_pos else ("positive" if p_pos > p_neu else "neutral")

            rows.append({
                "text":                 f"Sample post about {a}-{b} relations.",
                "country":              a,
                "country_pair":         f"{a}-{b}",
                "entity":               f"{a}_{b}_entity",
                "date":                 pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 90))),
                "predicted_label":      label,
                "confidence":           round(conf, 4),
                "probability_negative": round(p_neg, 4),
                "probability_neutral":  round(p_neu, 4),
                "probability_positive": round(p_pos, 4),
            })

    return pd.DataFrame(rows)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Score a DataFrame of ML model outputs with risk_score, risk_band, model_certainty."
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Path to input CSV (must have the required probability columns). "
             "If omitted, a built-in demo dataset is used.",
    )
    parser.add_argument(
        "--output", "-o",
        default="output/scored",
        help="Output file prefix (default: output/scored → output/scored.csv + .parquet)",
    )
    parser.add_argument(
        "--aggregate-by",
        choices=["country", "country_pair", "entity", "date"],
        default=None,
        help="Optional: also export an aggregated summary CSV.",
    )
    args = parser.parse_args()

    # ── Load data ─────────────────────────────────────────────────────────────
    if args.input:
        logger.info(f"Loading input from: {args.input}")
        df = pd.read_csv(args.input)
    else:
        logger.info("No --input provided — using built-in demo dataset.")
        df = _build_demo_df()

    logger.info(f"Input shape: {df.shape}")

    # ── Score ─────────────────────────────────────────────────────────────────
    scored = score_dataframe(df)

    # ── Preview ───────────────────────────────────────────────────────────────
    preview = top_risk_preview(scored, n=20)
    print("\n── Top 20 Highest-Risk Rows ──────────────────────────────────────────")
    print(preview.to_string(index=True))
    print()

    # ── Export ────────────────────────────────────────────────────────────────
    paths = export(scored, prefix=args.output)
    print(f"Exported scored data → {paths['csv']}")
    print(f"                     → {paths['parquet']}")

    # ── Optional aggregation ──────────────────────────────────────────────────
    if args.aggregate_by:
        agg = aggregate(scored, by=args.aggregate_by)
        agg_prefix = f"{args.output}_agg_{args.aggregate_by}"
        agg.to_csv(f"{agg_prefix}.csv", index=False)
        print(f"\nAggregation by '{args.aggregate_by}' → {agg_prefix}.csv")
        print(agg.to_string(index=False))

    # ── Band summary ──────────────────────────────────────────────────────────
    print("\n── Risk Band Distribution ────────────────────────────────────────────")
    print(scored["risk_band"].value_counts().sort_index().to_string())
    print("\n── Model Certainty Distribution ──────────────────────────────────────")
    print(scored["model_certainty"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
