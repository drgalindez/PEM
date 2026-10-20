"""
run_sensitivity.py
==================

A worked sensitivity test for the production efficiency model, for part 6.4 of
the assignment.

WHAT THIS SCRIPT DOES
---------------------
It runs the model once with the data as given, to get a baseline.  It then runs
it again several times, each time changing ONE driver by plus twenty per cent
and by minus twenty per cent, and records how much the annual NPP changes.  The
result is printed as a table and written to ``output/sensitivity.csv``.

WHAT YOU HAVE TO DO
-------------------
As delivered, this script perturbs THREE of the seven quantities the assignment
asks for:

    1. incoming shortwave radiation        (done for you)
    2. leaf area index                     (done for you)
    3. absorbed fraction of PAR            (done for you)
    4. average temperature                 <-- you add this
    5. minimum temperature                 <-- you add this
    6. vapour pressure deficit             <-- you add this
    7. two look-up table parameters        <-- you add these

Adding the rest is your job, and it is the point of the exercise.  Every place
you need to touch is marked ``TODO``.  Each one is two or three lines, and the
three that are already there are the pattern to copy.

Run it exactly like the main script::

    python run_sensitivity.py

(on macOS, ``python3 run_sensitivity.py``).

A WORD ON WHAT "PERTURB A DRIVER" MEANS
---------------------------------------
The model reads a year of daily weather and monthly vegetation.  To change a
driver by twenty per cent we multiply *every day's value* of that one driver by
1.2 or by 0.8, leave everything else alone, and run the model again.  That is
not a claim about what a warmer or brighter world would look like; it is a way
of asking which of the model's inputs the answer is most sensitive to.

One caution, and it matters for your discussion.  Temperature is measured in
degrees Celsius, so multiplying it by 1.2 is not the same kind of operation as
multiplying radiation by 1.2: a temperature of -10 degrees becomes -12, that is
colder, while a temperature of +10 becomes +12, warmer.  Think about whether a
multiplicative change is the right one for temperature, and say what you did
and why.  An additive change of a fixed number of degrees is a defensible
alternative.  Either is acceptable as long as you state it.

Author: prepared for EE529, Fall 2026.
"""

from __future__ import annotations

import copy
import os

import pem

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUTPUT = os.path.join(HERE, "output")

SITE_FILES = [
    "site_02_evergreen_broadleaf_forest.txt",
    "site_09_open_shrubland.txt",
    "site_11_cropland.txt",
]

#: The size of the perturbation, as a fraction.  0.20 means plus and minus
#: twenty per cent, which is what the assignment asks for.
PERTURBATION = 0.20


# ---------------------------------------------------------------------------
# Helpers for changing one thing at a time
# ---------------------------------------------------------------------------

def scale_driver(site, key, factor):
    """Return a copy of ``site`` with one daily driver multiplied by ``factor``.

    A *copy* is essential.  If we modified the original, the next perturbation
    would start from the already-perturbed data and the results would be
    nonsense.  ``copy.deepcopy`` gives us a completely independent copy.

    Parameters
    ----------
    site : dict
        As returned by :func:`pem.read_site`.
    key : str
        Which daily series to change: ``"swrad"``, ``"lai"``, ``"fpar"``,
        ``"tavg"``, ``"tmin"`` or ``"vpd"``.
    factor : float
        1.2 for plus twenty per cent, 0.8 for minus twenty per cent.

    Returns
    -------
    dict
        A new site dictionary, safe to pass to :func:`pem.run_pem`.
    """
    changed = copy.deepcopy(site)
    changed[key] = [value * factor for value in changed[key]]
    return changed


def offset_driver(site, key, delta):
    """Return a copy of ``site`` with one daily driver shifted by ``delta``.

    Use this instead of :func:`scale_driver` for temperature, if you decide
    that adding a fixed number of degrees is a more sensible perturbation than
    multiplying by a factor.  See the note at the top of this file.

    Parameters
    ----------
    delta : float
        The amount to add, in the units of that driver.  Negative to subtract.
    """
    changed = copy.deepcopy(site)
    changed[key] = [value + delta for value in changed[key]]
    return changed


def scale_parameter(lookup_table, biome_code, parameter, factor):
    """Return a copy of the look-up table with one parameter changed.

    Parameters
    ----------
    lookup_table : dict
        As returned by :func:`pem.read_lookup_table`.
    biome_code : str
        Which biome column to change, for example ``"EBF"``.  Only that biome
        is touched, which is what you want: you are testing the sensitivity of
        one site.
    parameter : str
        The row name, exactly as it appears in the table, for example
        ``"Epsilon_max"`` or ``"sla"`` or ``"froot_leaf_ratio"``.
    factor : float
        1.2 or 0.8.

    Returns
    -------
    dict
        A new look-up table, safe to pass to :func:`pem.run_pem`.
    """
    changed = copy.deepcopy(lookup_table)
    changed[biome_code][parameter] *= factor
    return changed


def percent_change(perturbed, baseline):
    """Percentage change of ``perturbed`` relative to ``baseline``.

    Returns zero if the baseline is zero, to avoid dividing by nothing.
    """
    if baseline == 0:
        return 0.0
    return 100.0 * (perturbed - baseline) / baseline


# ---------------------------------------------------------------------------
# The test itself
# ---------------------------------------------------------------------------

def sensitivity_for_site(site, lookup_table):
    """Run the whole set of perturbations for one site.

    Returns
    -------
    list of tuple
        ``(driver_name, percent_change_when_increased,
           percent_change_when_decreased)``
    """
    up = 1.0 + PERTURBATION      # 1.2
    down = 1.0 - PERTURBATION    # 0.8

    # The unperturbed answer that everything is compared against.
    baseline = pem.run_pem(site, lookup_table)["annual_npp"]

    rows = []

    # ---- 1. incoming shortwave radiation ---------------------------------
    npp_up = pem.run_pem(scale_driver(site, "swrad", up), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(scale_driver(site, "swrad", down), lookup_table)["annual_npp"]
    rows.append(("Shortwave radiation",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    # ---- 2. leaf area index ----------------------------------------------
    npp_up = pem.run_pem(scale_driver(site, "lai", up), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(scale_driver(site, "lai", down), lookup_table)["annual_npp"]
    rows.append(("Leaf area index",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    # ---- 3. absorbed fraction of PAR -------------------------------------
    npp_up = pem.run_pem(scale_driver(site, "fpar", up), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(scale_driver(site, "fpar", down), lookup_table)["annual_npp"]
    rows.append(("Absorbed fraction of PAR",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    # ---- 4. average temperature ------------------------------------------
    # TODO: add the average temperature.  The key in the site dictionary is
    # "tavg".  Copy the three lines above and change the key and the label.
    #
    npp_up = pem.run_pem(offset_driver(site, "tavg", +2.0), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(offset_driver(site, "tavg", -2.0), lookup_table)["annual_npp"]
    rows.append(("Average Temperature",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    # ---- 5. minimum temperature ------------------------------------------
    # TODO: add the minimum temperature.  The key is "tmin".
    npp_up = pem.run_pem(offset_driver(site, "tmin", +2.0), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(offset_driver(site, "tmin", -2.0), lookup_table)["annual_npp"]
    rows.append(("Minimum Temperature",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))
    
    # ---- 6. vapour pressure deficit --------------------------------------
    # TODO: add the vapour pressure deficit.  The key is "vpd".
    npp_up = pem.run_pem(scale_driver(site, "vpd", up), lookup_table)["annual_npp"]
    npp_down = pem.run_pem(scale_driver(site, "vpd", down), lookup_table)["annual_npp"]
    rows.append(("Vapour Pressure Deficit",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))
    
    # ---- 7. two parameters from the look-up table ------------------------
    # TODO: pick two parameters and perturb them, using scale_parameter rather
    # than scale_driver.

    # EBF epsilon max perturbation for the 3 Biomes
    lut_up = scale_parameter(lookup_table, site["biome_code"],
                             "Epsilon_max", up)
    npp_up = pem.run_pem(site, lut_up)["annual_npp"]

    lut_down = scale_parameter(lookup_table, site["biome_code"],
                               "Epsilon_max", down)
    npp_down = pem.run_pem(site, lut_down)["annual_npp"]

    rows.append(("Maximum light-use efficiency",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    # Specific leaf area perturbation for the 3 Biomes 
    lut_up = scale_parameter(lookup_table, site["biome_code"],
                             "sla", up)
    npp_up = pem.run_pem(site, lut_up)["annual_npp"]

    lut_down = scale_parameter(lookup_table, site["biome_code"],
                               "sla", down)
    npp_down = pem.run_pem(site, lut_down)["annual_npp"]

    rows.append(("Specific Leaf Area",
                 percent_change(npp_up, baseline),
                 percent_change(npp_down, baseline)))

    return baseline, rows


def main():
    os.makedirs(OUTPUT, exist_ok=True)
    lookup_table = pem.read_lookup_table(os.path.join(DATA, "lookup_table.tsv"))

    csv_rows = [("site", "driver", "percent_change_npp_increase",
                 "percent_change_npp_decrease")]

    for filename in SITE_FILES:
        site = pem.read_site(os.path.join(DATA, filename))
        baseline, rows = sensitivity_for_site(site, lookup_table)

        print()
        print(f"{site['biome_name']}")
        print(f"Baseline annual NPP: {baseline:.4f} kg C m-2 yr-1")
        print("-" * 62)
        print(f"{'Driver changed by 20 per cent':<32}{'increase':>14}{'decrease':>14}")
        print("-" * 62)
        for name, up_pct, down_pct in rows:
            print(f"{name:<32}{up_pct:>13.1f}%{down_pct:>13.1f}%")
            csv_rows.append((site["biome_code"], name,
                             f"{up_pct:.3f}", f"{down_pct:.3f}"))
        print("-" * 62)
        print("Values are the percentage change in ANNUAL NPP.")

    path = os.path.join(OUTPUT, "sensitivity.csv")
    with open(path, "w") as handle:
        for row in csv_rows:
            handle.write(",".join(str(field) for field in row) + "\n")
    print()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
