"""
pem.py
======

A Production Efficiency Model (PEM) for terrestrial gross and net primary
production, written for EE529, Modeling and Monitoring Terrestrial Ecosystem
Processes, Boston University.

WHAT THIS MODEL DOES
--------------------
It takes, for one location and one year:

  * daily weather        (shortwave radiation, average and minimum temperature,
                          vapour pressure deficit),
  * satellite vegetation (monthly leaf area index and the fraction of
                          photosynthetically active radiation absorbed),
  * a biome type         (which selects one column of a look-up table of
                          parameters),

and returns daily and annual gross primary production (GPP), autotrophic
respiration, and net primary production (NPP), all in kilograms of carbon per
square metre.

This is the same algorithm that produces the operational MODIS NPP product
(MOD17).  The equations below follow the MOD17 User's Guide (Heinsch et al.,
2003) and Lecture 09 of the course.

THE CHAIN OF CALCULATION
------------------------
Everything the model does is a chain of five steps.  If you understand these
five lines you understand the model:

  1. Absorbed light        APAR   = 0.45 * SWRAD * FPAR
  2. Light use efficiency  epsilon = epsilon_max * f(Tmin) * f(VPD)
  3. Photosynthesis        GPP    = epsilon * APAR
  4. Respiration           Ra     = maintenance + growth
  5. Net production        NPP    = GPP - Ra

Steps 1 to 3 are done every day.  Step 4 is partly daily (leaves, fine roots)
and partly annual (live wood, and all growth respiration).  Step 5 is done both
ways: a daily NPP for plotting, and an annual NPP for the totals.

UNITS  --  read this before you trust any number
------------------------------------------------
  SWRAD   W m-2                     (joules per second per square metre)
  IPAR    MJ m-2 day-1              (incident photosynthetically active rad.)
  APAR    MJ m-2 day-1              (absorbed PAR)
  epsilon kg C MJ-1                 (light use efficiency)
  GPP     kg C m-2 day-1  or  yr-1
  Tavg    degrees Celsius
  Tmin    degrees Celsius
  VPD     Pa                        (pascals, NOT kPa)
  LAI     m2 leaf m-2 ground        (dimensionless)
  FPAR    fraction between 0 and 1  (the data file stores it as a percentage)
  SLA     m2 leaf (kg C)-1          (specific leaf area)

A note on the two scale factors in the data files.  Satellite products are
stored as small integers to save space, and are turned back into physical
values by multiplying by a scale factor.  In these files:

  FPAR is stored as a percentage        ->  divide by 100 to get a fraction
  LAI  is stored multiplied by ten      ->  divide by 10  to get m2/m2

Forgetting either of these is the single commonest mistake in this assignment.
The reader function below does both conversions for you, once, in one place.

HOW TO USE THIS FILE
--------------------
You do not run this file directly.  Run ``run_pem.py`` instead, which imports
the functions defined here.  If you want to experiment, open a Python prompt
and do:

    >>> import pem
    >>> site = pem.read_site("data/site_02_evergreen_broadleaf_forest.txt")
    >>> lut  = pem.read_lookup_table("data/lookup_table.tsv")
    >>> out  = pem.run_pem(site, lut)
    >>> out["annual_gpp"], out["annual_npp"]

Author: prepared for EE529, Fall 2026.
"""

from __future__ import annotations

import csv
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Fraction of incoming shortwave radiation that is photosynthetically active.
#: Photosynthesis uses light between 400 and 700 nm, which is roughly 45 per
#: cent of the energy in the full solar spectrum reaching the surface.
PAR_FRACTION = 0.45

#: Seconds in a day.  Used to convert a radiation *rate* (W m-2, i.e. joules
#: per second) into a daily radiation *total* (J m-2 day-1).
SECONDS_PER_DAY = 24 * 60 * 60

#: Joules in a megajoule.  Used to get from J m-2 day-1 to MJ m-2 day-1.
JOULES_PER_MJ = 1.0e6

#: Days in each month of a non-leap year.  The satellite vegetation data are
#: monthly; the weather is daily.  We repeat each monthly value across the days
#: of its month so that everything is on the same daily time step.
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

#: Number of days in the model year.  These files contain 365 days.
DAYS_IN_YEAR = 365

#: The eleven biome classes, in the order in which they appear as columns of
#: the look-up table.  The integer biome code in a site file is a 1-based index
#: into this list, so code 2 is EBF, code 9 is OSL, code 11 is CL.
BIOME_CODES = [
    "ENF",  # 1  evergreen needleleaf forest
    "EBF",  # 2  evergreen broadleaf forest
    "DNF",  # 3  deciduous needleleaf forest
    "DBF",  # 4  deciduous broadleaf forest
    "MF",   # 5  mixed forest
    "WL",   # 6  woodland
    "WGL",  # 7  wooded grassland
    "CSL",  # 8  closed shrubland
    "OSL",  # 9  open shrubland
    "GL",   # 10 grassland
    "CL",   # 11 cropland
]

#: Long names, used only when printing results so the output is readable.
BIOME_NAMES = {
    "ENF": "Evergreen needleleaf forest",
    "EBF": "Evergreen broadleaf forest",
    "DNF": "Deciduous needleleaf forest",
    "DBF": "Deciduous broadleaf forest",
    "MF": "Mixed forest",
    "WL": "Woodland",
    "WGL": "Wooded grassland",
    "CSL": "Closed shrubland",
    "OSL": "Open shrubland",
    "GL": "Grassland",
    "CL": "Cropland",
}


# ---------------------------------------------------------------------------
# Reading the input files
# ---------------------------------------------------------------------------

def read_lookup_table(path):
    """Read the biome parameter look-up table.

    The file is a tab-separated table.  The first row is a header naming the
    eleven biome classes.  Every other row is one parameter, with one value per
    biome.  So the table is read as::

        lut["EBF"]["Epsilon_max"]  ->  0.0011

    Parameters
    ----------
    path : str
        Path to ``lookup_table.tsv``.

    Returns
    -------
    dict
        ``lut[biome_code][parameter_name] = float value``

    Notes
    -----
    Every number in this table is a *parameter*, not an observation.  There is
    no equation left in the model once this table is fixed; there is only
    arithmetic.  Most of the disagreement between different production
    efficiency models is disagreement about these numbers.
    """
    lut = {code: {} for code in BIOME_CODES}

    with open(path, "r") as handle:
        rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]

    header = [field.strip() for field in rows[0]]
    # header[0] is the word "Parameter"; header[1:] are the biome codes.
    codes_in_file = header[1:]

    for row in rows[1:]:
        name = row[0].strip()
        for code, value in zip(codes_in_file, row[1:]):
            lut[code][name] = float(value.strip())

    return lut


def read_site(path):
    """Read one site's weather and vegetation file.

    File layout
    -----------
    The file is tab separated with a one-line header::

        Biome   SWRad   Tavg    Tmin    VPD     Fpar    LAI

    and then 365 data rows, one per day of the year.  Two oddities that you
    must handle, and that this function handles for you:

    1. The **biome code** appears only once, on the first data row.  Every
       later row leaves that field blank.
    2. The **Fpar and LAI columns are monthly, not daily**.  Only the first
       twelve rows carry values; they are the twelve monthly means, January to
       December.  Every later row leaves those two fields blank.  This function
       repeats each monthly value across the days of its month.

    Unit conversions applied here, once, so that nothing downstream has to
    remember them:

    * ``Fpar`` is divided by 100, turning a percentage into a fraction.
    * ``LAI`` is divided by 10, undoing the satellite product's scale factor.

    Parameters
    ----------
    path : str
        Path to a site file, for example
        ``data/site_02_evergreen_broadleaf_forest.txt``.

    Returns
    -------
    dict
        With keys ``biome_code`` (str, e.g. ``"EBF"``), ``biome_number`` (int),
        and the daily arrays ``swrad``, ``tavg``, ``tmin``, ``vpd``, ``fpar``,
        ``lai``, each a list of 365 floats.
    """
    with open(path, "r") as handle:
        rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]

    # rows[0] is the header line; the data start at rows[1].
    data_rows = rows[1:]

    # ---- the biome code, from the first data row only --------------------
    biome_number = int(float(data_rows[0][0].strip()))
    biome_code = BIOME_CODES[biome_number - 1]

    # ---- the daily weather, present on every row -------------------------
    swrad, tavg, tmin, vpd = [], [], [], []
    for row in data_rows:
        swrad.append(float(row[1]))
        tavg.append(float(row[2]))
        tmin.append(float(row[3]))
        vpd.append(float(row[4]))

    # ---- the monthly vegetation, present on the first twelve rows only ----
    monthly_fpar, monthly_lai = [], []
    for row in data_rows[:12]:
        # Divide by 100: the file stores FPAR as a percentage (74 means 0.74).
        monthly_fpar.append(float(row[5]) / 100.0)
        # Divide by 10: the file stores LAI with a scale factor of 10
        # (45 means an LAI of 4.5).
        monthly_lai.append(float(row[6]) / 10.0)

    # ---- repeat each monthly value across the days of its month ----------
    fpar, lai = [], []
    for month_index, n_days in enumerate(DAYS_IN_MONTH):
        fpar.extend([monthly_fpar[month_index]] * n_days)
        lai.extend([monthly_lai[month_index]] * n_days)

    # Sanity checks.  If one of these fails, the input file is not what we
    # think it is, and it is far better to stop here than to produce a number
    # that looks plausible and is wrong.
    assert len(swrad) == DAYS_IN_YEAR, f"expected 365 days, found {len(swrad)}"
    assert len(fpar) == DAYS_IN_YEAR, "monthly vegetation did not expand to 365 days"

    return {
        "name": os.path.basename(path),
        "biome_number": biome_number,
        "biome_code": biome_code,
        "biome_name": BIOME_NAMES[biome_code],
        "swrad": swrad,
        "tavg": tavg,
        "tmin": tmin,
        "vpd": vpd,
        "fpar": fpar,
        "lai": lai,
    }


# ---------------------------------------------------------------------------
# Step 1 and 2:  light, and the efficiency with which it is used
# ---------------------------------------------------------------------------

def incident_par(swrad_w_m2):
    """Convert incoming shortwave radiation to incident PAR.

    .. math::  IPAR = 0.45 \\times SWRAD \\times 86400 / 10^6

    The three factors, in order:

    * ``0.45``   the share of the solar spectrum that plants can use;
    * ``86400``  seconds per day, turning a rate (W m-2) into a daily total;
    * ``1e6``    joules per megajoule, because efficiency is quoted per MJ.

    Parameters
    ----------
    swrad_w_m2 : float
        Daily average incoming shortwave radiation, W m-2.

    Returns
    -------
    float
        Incident photosynthetically active radiation, MJ m-2 day-1.
    """
    return PAR_FRACTION * swrad_w_m2 * SECONDS_PER_DAY / JOULES_PER_MJ


def absorbed_par(ipar_mj, fpar_fraction):
    """Absorbed PAR is incident PAR times the fraction the canopy absorbs.

    .. math::  APAR = IPAR \\times FPAR

    ``fpar_fraction`` must already be a fraction between 0 and 1.  The reader
    function :func:`read_site` has divided the file's percentage by 100.
    """
    return ipar_mj * fpar_fraction


def temperature_scalar(tmin, tmin_stop, tmin_start):
    """Attenuation of light use efficiency by low temperature.

    A simple ramp between two thresholds:

    * at or below ``tmin_stop``  the scalar is 0  (too cold to photosynthesise)
    * at or above ``tmin_start`` the scalar is 1  (temperature is not limiting)
    * between them it rises linearly.

    Note the names.  In the look-up table the column called ``Tmin_stop`` holds
    the *lower* threshold, where photosynthesis stops, and ``Tmin_start`` holds
    the *upper* one, where it is no longer limited.  This is confusing and has
    caught many people out, so the arguments here are named for what they do.

    Parameters
    ----------
    tmin : float
        Daily minimum temperature, degrees Celsius.
    tmin_stop : float
        Temperature at or below which efficiency is zero.
    tmin_start : float
        Temperature at or above which efficiency is unattenuated.

    Returns
    -------
    float
        A number between 0 and 1.
    """
    if tmin <= tmin_stop:
        return 0.0
    if tmin >= tmin_start:
        return 1.0
    return (tmin - tmin_stop) / (tmin_start - tmin_stop)


def vpd_scalar(vpd, vpd_stop, vpd_start):
    """Attenuation of light use efficiency by dry air.

    Vapour pressure deficit is how far the air is from saturation.  When it is
    large the plant closes its stomata to avoid losing water, and in closing
    them it also shuts out carbon dioxide.  So this ramp runs the other way
    from the temperature one:

    * at or below ``vpd_stop``  the scalar is 1  (air moist enough, no limit)
    * at or above ``vpd_start`` the scalar is 0  (stomata closed)
    * between them it falls linearly.

    Again the look-up table names are the opposite way round from what you
    might expect: ``VPD_stop`` is the *lower* threshold and ``VPD_start`` the
    *upper* one.

    Parameters
    ----------
    vpd : float
        Daylight average vapour pressure deficit, Pa.
    vpd_stop : float
        Deficit at or below which there is no limitation.
    vpd_start : float
        Deficit at or above which efficiency is zero.

    Returns
    -------
    float
        A number between 0 and 1.
    """
    if vpd >= vpd_start:
        return 0.0
    if vpd <= vpd_stop:
        return 1.0
    return (vpd_start - vpd) / (vpd_start - vpd_stop)


def light_use_efficiency(params, tmin, vpd):
    """The efficiency with which absorbed light is converted to fixed carbon.

    .. math::  \\varepsilon = \\varepsilon_{max} \\times f(T_{min}) \\times f(VPD)

    A biome-dependent maximum, read from the look-up table, reduced by two
    scalars.  Neither scalar can ever raise the efficiency; they only lower it.

    Returns
    -------
    float
        Light use efficiency, kg C MJ-1.
    """
    return (
        params["Epsilon_max"]
        * temperature_scalar(tmin, params["Tmin_stop"], params["Tmin_start"])
        * vpd_scalar(vpd, params["VPD_stop"], params["VPD_start"])
    )


# ---------------------------------------------------------------------------
# Step 4:  autotrophic respiration
# ---------------------------------------------------------------------------
#
# The model separates two kinds of respiration, because they scale with
# different things:
#
#   MAINTENANCE respiration  keeps existing tissue alive.  It scales with how
#                            much tissue there is and how warm it is.
#   GROWTH respiration       is the cost of building new tissue.  It scales
#                            with how much new tissue is built in the year.
#
# and four components of the plant:
#
#                    maintenance      growth
#   leaves           daily            annual
#   fine roots       daily            annual
#   live wood        annual           annual
#   dead wood        none             annual
#
# Dead wood has no maintenance cost because it is dead; it still had to be
# built, so it has a growth cost.
# ---------------------------------------------------------------------------

def q10_factor(tavg, q10):
    """Temperature response of respiration.

    .. math::  Q_{10}^{(T_{avg} - 20)/10}

    A Q10 of 2 means respiration doubles for every ten degrees of warming.  The
    reference temperature is 20 degrees Celsius, which is where the base rates
    in the look-up table are defined.
    """
    return q10 ** ((tavg - 20.0) / 10.0)


def leaf_mass(lai, sla):
    """Leaf carbon mass per unit ground area, kg C m-2.

    .. math::  Leaf\\_Mass = LAI / SLA

    Specific leaf area (SLA) is the leaf area produced per kilogram of leaf
    carbon, so dividing area by SLA gives mass.  ``lai`` must already be a
    physical leaf area index; :func:`read_site` has removed the scale factor.
    """
    return lai / sla


def daily_leaf_maintenance_respiration(params, lai, tavg):
    """Daily leaf maintenance respiration, kg C m-2 day-1.

    .. math::

        Leaf\\_MR = Leaf\\_Mass \\times leaf\\_mr\\_base
                    \\times Q_{10}^{(T_{avg}-20)/10}
    """
    mass = leaf_mass(lai, params["sla"])
    return mass * params["leaf_mr_base"] * q10_factor(tavg, params["q10_mr"])


def daily_fine_root_maintenance_respiration(params, lai, tavg):
    """Daily fine root maintenance respiration, kg C m-2 day-1.

    Fine root mass is never observed from space.  The model assumes it is a
    fixed multiple of leaf mass, the ratio coming from the look-up table:

    .. math::

        Froot\\_Mass = Leaf\\_Mass \\times froot\\_leaf\\_ratio

        Froot\\_MR   = Froot\\_Mass \\times froot\\_mr\\_base
                       \\times Q_{10}^{(T_{avg}-20)/10}

    This is the least constrained term in the whole model, and it is not small:
    for most biomes the fine root ratio is greater than one, so fine roots
    respire more than leaves do.
    """
    mass = leaf_mass(lai, params["sla"]) * params["froot_leaf_ratio"]
    return mass * params["froot_mr_base"] * q10_factor(tavg, params["q10_mr"])


def annual_live_wood_maintenance_respiration(params, lai_series, tavg_series):
    """Annual live wood maintenance respiration, kg C m-2 yr-1.

    Live wood mass is scaled from the *annual maximum* leaf mass, not from the
    daily value, because wood does not come and go with the leaves:

    .. math::

        Livewood\\_Mass = \\max(Leaf\\_Mass) \\times livewood\\_leaf\\_ratio

    and the temperature response is summed over the whole year rather than
    applied day by day:

    .. math::

        Livewood\\_MR = Livewood\\_Mass \\times livewood\\_mr\\_base
                        \\times \\sum_{day} Q_{10}^{(T_{avg}-20)/10}

    Grasslands and croplands have no live wood, so the look-up table gives them
    a ratio of zero and this term vanishes.
    """
    max_leaf_mass = max(leaf_mass(lai, params["sla"]) for lai in lai_series)
    mass = max_leaf_mass * params["livewood_leaf_ratio"]
    annual_q10_sum = sum(q10_factor(t, params["q10_mr"]) for t in tavg_series)
    return mass * params["livewood_mr_base"] * annual_q10_sum


def annual_growth_respiration(params, lai_series):
    """Annual growth respiration of all four components, kg C m-2 yr-1.

    The leaf term is the anchor:

    .. math::

        Leaf\\_GR = \\max(Leaf\\_Mass) \\times ann\\_turnover\\_fraction
                    \\times leaf\\_gr\\_base

    ``ann_turnover_fraction`` is the proportion of the leaf population that is
    newly grown in the year: 1 for a deciduous forest or a crop, which grows a
    whole new canopy every year, and less for an evergreen, which does not.

    The other three components are then fixed multiples of the leaf term:

    .. math::

        Annual\\_GR = Leaf\\_GR \\times
                      (1 + r_{froot} + r_{livewood} + r_{deadwood})

    Those three ratios are among the least defensible numbers in the model and
    among the most influential on the answer.  They are a good place to start
    a sensitivity test.

    Returns
    -------
    dict
        The four components and their total, so that you can report them
        separately if you wish.
    """
    max_leaf_mass = max(leaf_mass(lai, params["sla"]) for lai in lai_series)

    leaf_gr = (
        max_leaf_mass
        * params["ann_turnover_fraction"]
        * params["leaf_gr_base"]
    )
    froot_gr = leaf_gr * params["froot_leaf_gr_ratio"]
    livewood_gr = leaf_gr * params["livewood_leaf_gr_ratio"]
    deadwood_gr = leaf_gr * params["deadwood_leaf_gr_ratio"]

    return {
        "leaf_gr": leaf_gr,
        "froot_gr": froot_gr,
        "livewood_gr": livewood_gr,
        "deadwood_gr": deadwood_gr,
        "total": leaf_gr + froot_gr + livewood_gr + deadwood_gr,
    }


# ---------------------------------------------------------------------------
# Putting it together
# ---------------------------------------------------------------------------

def run_pem(site, lookup_table):
    """Run the production efficiency model for one site for one year.

    Parameters
    ----------
    site : dict
        As returned by :func:`read_site`.
    lookup_table : dict
        As returned by :func:`read_lookup_table`.

    Returns
    -------
    dict
        Daily series (lists of 365 floats) and annual totals (floats).  Keys:

        ``daily_gpp``, ``daily_mr``, ``daily_npp``, ``epsilon``, ``apar``
            daily series, kg C m-2 day-1 (``epsilon`` in kg C MJ-1,
            ``apar`` in MJ m-2 day-1)
        ``annual_gpp``, ``annual_mr``, ``annual_gr``, ``annual_ra``,
        ``annual_npp``
            annual totals, kg C m-2 yr-1
        ``growth_components``
            the four growth respiration terms, kg C m-2 yr-1

    The calculation, in order
    ------------------------
    1. daily light use efficiency from temperature and humidity;
    2. daily absorbed PAR from radiation and the satellite absorbed fraction;
    3. daily GPP as the product of the two, summed to an annual GPP;
    4. daily maintenance respiration for leaves and fine roots, plus one
       annual number for live wood;
    5. annual growth respiration for all four components;
    6. NPP as GPP minus the two respiration terms.

    Note on daily NPP
    -----------------
    Live wood maintenance and all growth respiration are annual quantities.  To
    plot a daily NPP we spread them evenly across the 365 days.  That is a
    presentational choice, not a statement about when the plant actually pays
    those costs.  The annual total is unaffected by it.
    """
    params = lookup_table[site["biome_code"]]

    epsilon = []
    apar = []
    daily_gpp = []

    # ---- steps 1 to 3: daily photosynthesis ------------------------------
    for day in range(DAYS_IN_YEAR):
        eps = light_use_efficiency(params, site["tmin"][day], site["vpd"][day])
        ipar = incident_par(site["swrad"][day])
        a = absorbed_par(ipar, site["fpar"][day])

        epsilon.append(eps)
        apar.append(a)
        daily_gpp.append(eps * a)

    annual_gpp = sum(daily_gpp)

    # ---- step 4a: maintenance respiration --------------------------------
    daily_leaf_mr = [
        daily_leaf_maintenance_respiration(params, site["lai"][d], site["tavg"][d])
        for d in range(DAYS_IN_YEAR)
    ]
    daily_froot_mr = [
        daily_fine_root_maintenance_respiration(params, site["lai"][d], site["tavg"][d])
        for d in range(DAYS_IN_YEAR)
    ]
    annual_livewood_mr = annual_live_wood_maintenance_respiration(
        params, site["lai"], site["tavg"]
    )

    # Spread the one annual live wood number evenly over the days, so that a
    # daily maintenance respiration can be plotted.
    daily_mr = [
        daily_leaf_mr[d] + daily_froot_mr[d] + annual_livewood_mr / DAYS_IN_YEAR
        for d in range(DAYS_IN_YEAR)
    ]
    annual_mr = sum(daily_leaf_mr) + sum(daily_froot_mr) + annual_livewood_mr

    # ---- step 4b: growth respiration -------------------------------------
    growth = annual_growth_respiration(params, site["lai"])
    annual_gr = growth["total"]

    # ---- step 5: net primary production ----------------------------------
    # NPP = GPP - (maintenance + growth).  Both respiration terms are
    # SUBTRACTED.  If your annual NPP comes out larger than your annual GPP,
    # you have added one of them by mistake.
    daily_npp = [
        daily_gpp[d] - daily_mr[d] - annual_gr / DAYS_IN_YEAR
        for d in range(DAYS_IN_YEAR)
    ]
    annual_ra = annual_mr + annual_gr
    annual_npp = annual_gpp - annual_ra

    return {
        "site": site,
        "params": params,
        "epsilon": epsilon,
        "apar": apar,
        "daily_gpp": daily_gpp,
        "daily_leaf_mr": daily_leaf_mr,
        "daily_froot_mr": daily_froot_mr,
        "daily_mr": daily_mr,
        "daily_npp": daily_npp,
        "annual_gpp": annual_gpp,
        "annual_mr": annual_mr,
        "annual_gr": annual_gr,
        "annual_ra": annual_ra,
        "annual_npp": annual_npp,
        "annual_livewood_mr": annual_livewood_mr,
        "growth_components": growth,
    }


def write_daily_csv(result, path):
    """Write the daily model output to a CSV file, one row per day.

    Open the file in Excel, or read it back into Python, to make your own
    plots.  Columns are day of year, the drivers, and the model output.
    """
    site = result["site"]
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "day_of_year",
            "swrad_W_m2", "tavg_C", "tmin_C", "vpd_Pa", "fpar_fraction", "lai",
            "epsilon_kgC_per_MJ", "apar_MJ_m2_day",
            "gpp_kgC_m2_day", "maintenance_resp_kgC_m2_day", "npp_kgC_m2_day",
        ])
        for d in range(DAYS_IN_YEAR):
            writer.writerow([
                d + 1,
                site["swrad"][d], site["tavg"][d], site["tmin"][d],
                site["vpd"][d], site["fpar"][d], site["lai"][d],
                result["epsilon"][d], result["apar"][d],
                result["daily_gpp"][d], result["daily_mr"][d],
                result["daily_npp"][d],
            ])
