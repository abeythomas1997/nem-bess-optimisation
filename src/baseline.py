import pandas as pd

from battery import (
    POWER_MW,
    MIN_SOC_MWH,
    MAX_SOC_MWH,
    INITIAL_SOC_MWH,
    CHARGE_EFFICIENCY,
    DISCHARGE_EFFICIENCY,
    INTERVAL_HOURS,
)


def run_baseline(
    prices: pd.DataFrame,
    charge_threshold: float,
    discharge_threshold: float,
) -> pd.DataFrame:

    soc = INITIAL_SOC_MWH
    results = []

    for _, row in prices.iterrows():
        price = row["RRP"]

        charge_mw = 0.0
        discharge_mw = 0.0

        if price <= charge_threshold:
            available_capacity = MAX_SOC_MWH - soc

            max_charge_mw_from_soc = (
                available_capacity
                / (INTERVAL_HOURS * CHARGE_EFFICIENCY)
            )

            charge_mw = min(
                POWER_MW,
                max_charge_mw_from_soc,
            )

        elif price >= discharge_threshold:
            available_energy = soc - MIN_SOC_MWH

            max_discharge_mw_from_soc = (
                available_energy
                * DISCHARGE_EFFICIENCY
                / INTERVAL_HOURS
            )

            discharge_mw = min(
                POWER_MW,
                max_discharge_mw_from_soc,
            )

        soc += (
            charge_mw
            * INTERVAL_HOURS
            * CHARGE_EFFICIENCY
        )

        soc -= (
            discharge_mw
            * INTERVAL_HOURS
            / DISCHARGE_EFFICIENCY
        )

        revenue = (
            discharge_mw - charge_mw
        ) * INTERVAL_HOURS * price

        results.append(
            {
                "SETTLEMENTDATE": row["SETTLEMENTDATE"],
                "RRP": price,
                "charge_mw": charge_mw,
                "discharge_mw": discharge_mw,
                "soc_mwh": soc,
                "revenue": revenue,
            }
        )

    return pd.DataFrame(results)