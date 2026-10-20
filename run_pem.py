"""
run_pem.py
==========

Run the production efficiency model for the three example sites, print a table
of annual totals, write the daily output to CSV files, and draw four figures.

This is the file you run.  From a terminal, in this folder::

    python run_pem.py

Everything it produces is written into the ``output`` folder.

If matplotlib is not installed the script still runs; it prints the table and
writes the CSV files, and simply skips the figures.  That is deliberate, so
that the assignment does not depend on getting a plotting library installed.

Author: prepared for EE529, Fall 2026.
"""

from __future__ import annotations

import os

import pem

# ---------------------------------------------------------------------------
# Where things live.  These paths are relative to this file, so the script
# works no matter which folder you launch it from.
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUTPUT = os.path.join(HERE, "output")

#: The three example sites.  Each is one pixel of a global grid, for one year.
#: The number in the file name is the biome code, which the model reads from
#: the file itself; it is repeated in the name only to make the folder legible.
SITE_FILES = [
    "site_02_evergreen_broadleaf_forest.txt",
    "site_09_open_shrubland.txt",
    "site_11_cropland.txt",
]

MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    os.makedirs(OUTPUT, exist_ok=True)

    # ---- read the parameter table once -----------------------------------
    lookup_table = pem.read_lookup_table(os.path.join(DATA, "lookup_table.tsv"))

    # ---- run every site ---------------------------------------------------
    results = []
    for filename in SITE_FILES:
        site = pem.read_site(os.path.join(DATA, filename))
        result = pem.run_pem(site, lookup_table)
        results.append(result)

        # one CSV of daily values per site, for your own plotting
        stem = os.path.splitext(filename)[0]
        pem.write_daily_csv(result, os.path.join(OUTPUT, stem + "_daily.csv"))

    # ---- print the annual totals -----------------------------------------
    print()
    print("Annual totals, kilograms of carbon per square metre per year")
    print("=" * 78)
    header = (f"{'Biome':<30}{'GPP':>10}{'Maint.':>10}"
              f"{'Growth':>10}{'NPP':>10}{'NPP/GPP':>9}")
    print(header)
    print("-" * 78)
    for r in results:
        ratio = r["annual_npp"] / r["annual_gpp"] if r["annual_gpp"] > 0 else 0.0
        print(f"{r['site']['biome_name']:<30}"
              f"{r['annual_gpp']:>10.4f}"
              f"{r['annual_mr']:>10.4f}"
              f"{r['annual_gr']:>10.4f}"
              f"{r['annual_npp']:>10.4f}"
              f"{ratio:>9.2f}")
    print("=" * 78)
    print()
    print("Maint. is maintenance respiration, Growth is growth respiration.")
    print("NPP = GPP - (maintenance + growth).")
    print()

    # ---- write the same table to a CSV -----------------------------------
    summary_path = os.path.join(OUTPUT, "annual_summary.csv")
    with open(summary_path, "w") as handle:
        handle.write("biome_code,biome_name,annual_gpp,annual_maintenance_resp,"
                     "annual_growth_resp,annual_npp,npp_over_gpp\n")
        for r in results:
            ratio = r["annual_npp"] / r["annual_gpp"] if r["annual_gpp"] > 0 else 0.0
            handle.write(f"{r['site']['biome_code']},"
                         f"\"{r['site']['biome_name']}\","
                         f"{r['annual_gpp']:.6f},{r['annual_mr']:.6f},"
                         f"{r['annual_gr']:.6f},{r['annual_npp']:.6f},"
                         f"{ratio:.4f}\n")
    print(f"Wrote {summary_path}")
    for filename in SITE_FILES:
        stem = os.path.splitext(filename)[0]
        print(f"Wrote {os.path.join(OUTPUT, stem + '_daily.csv')}")

    # ---- figures ----------------------------------------------------------
    try:
        make_figures(results)
    except ImportError:
        print()
        print("matplotlib is not installed, so no figures were drawn.")
        print("The CSV files above contain everything needed to plot by hand.")
        print("To install it, run:   python -m pip install matplotlib")


def make_figures(results):
    """Draw four figures into the output folder.

    Raises
    ------
    ImportError
        If matplotlib is not available.  ``main`` catches this and carries on.
    """
    import matplotlib
    matplotlib.use("Agg")          # write files, do not open a window
    import matplotlib.pyplot as plt

    colours = ["#1B7837", "#B35806", "#2166AC"]
    days = list(range(1, pem.DAYS_IN_YEAR + 1))

    def style(ax, ylabel):
        ax.set_xticks(MONTH_STARTS)
        ax.set_xticklabels(MONTH_LABELS)
        ax.set_xlim(1, 365)
        ax.set_ylabel(ylabel)
        ax.grid(color="#EEEEEE", lw=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(frameon=False)

    # --- figure 1: daily GPP ----------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for r, c in zip(results, colours):
        ax.plot(days, r["daily_gpp"], color=c, lw=1.6,
                label=r["site"]["biome_name"])
    ax.set_title("Daily gross primary production")
    style(ax, "GPP (kg C m$^{-2}$ day$^{-1}$)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT, "fig1_daily_gpp.png"), dpi=150)
    plt.close(fig)

    # --- figure 2: daily NPP ----------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for r, c in zip(results, colours):
        ax.plot(days, r["daily_npp"], color=c, lw=1.6,
                label=r["site"]["biome_name"])
    ax.axhline(0, color="#666666", lw=1.0)
    ax.set_title("Daily net primary production")
    style(ax, "NPP (kg C m$^{-2}$ day$^{-1}$)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT, "fig2_daily_npp.png"), dpi=150)
    plt.close(fig)

    # --- figure 3: the efficiency and its two scalars, one site ------------
    # The evergreen broadleaf site is first in the list.
    r = results[0]
    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(days, r["site"]["tmin"], color="#2166AC", lw=1.2)
    axes[0].set_ylabel("Tmin ($^\\circ$C)")
    axes[1].plot(days, r["site"]["vpd"], color="#B35806", lw=1.2)
    axes[1].set_ylabel("VPD (Pa)")
    axes[2].plot(days, r["epsilon"], color="#1B7837", lw=1.4)
    axes[2].set_ylabel("$\\varepsilon$ (kg C MJ$^{-1}$)")
    axes[2].set_xticks(MONTH_STARTS)
    axes[2].set_xticklabels(MONTH_LABELS)
    axes[2].set_xlim(1, 365)
    for ax in axes:
        ax.grid(color="#EEEEEE", lw=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_title(f"What sets the efficiency: {r['site']['biome_name']}")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT, "fig3_efficiency_drivers.png"), dpi=150)
    plt.close(fig)

    # --- figure 4: the annual carbon balance, as bars ----------------------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = [r["site"]["biome_code"] for r in results]
    x = range(len(results))
    gpp = [r["annual_gpp"] for r in results]
    mr = [r["annual_mr"] for r in results]
    gr = [r["annual_gr"] for r in results]
    npp = [r["annual_npp"] for r in results]

    width = 0.2
    ax.bar([i - 1.5 * width for i in x], gpp, width, label="GPP", color="#1B7837")
    ax.bar([i - 0.5 * width for i in x], mr, width, label="Maintenance", color="#B35806")
    ax.bar([i + 0.5 * width for i in x], gr, width, label="Growth", color="#D6A55B")
    ax.bar([i + 1.5 * width for i in x], npp, width, label="NPP", color="#2166AC")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("kg C m$^{-2}$ yr$^{-1}$")
    ax.set_title("Annual carbon balance")
    ax.axhline(0, color="#666666", lw=1.0)
    ax.grid(axis="y", color="#EEEEEE", lw=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT, "fig4_annual_balance.png"), dpi=150)
    plt.close(fig)

    print()
    print("Wrote four figures into the output folder:")
    for name in ["fig1_daily_gpp.png", "fig2_daily_npp.png",
                 "fig3_efficiency_drivers.png", "fig4_annual_balance.png"]:
        print("  " + os.path.join(OUTPUT, name))


if __name__ == "__main__":
    main()
