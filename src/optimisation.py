import pandas as pd
import pulp

from battery import (
    POWER_MW,
    MIN_SOC_MWH,
    MAX_SOC_MWH,
    INITIAL_SOC_MWH,
    CHARGE_EFFICIENCY,
    DISCHARGE_EFFICIENCY,
    INTERVAL_HOURS,
)


def optimise_battery(prices: pd.DataFrame) -> pd.DataFrame:

    df = prices.reset_index(drop=True).copy()
    n = len(df)

    model = pulp.LpProblem(
        "BESS_Energy_Arbitrage",
        pulp.LpMaximize,
    )

    # Decision variables
    charge = pulp.LpVariable.dicts(
        "charge_mw",
        range(n),
        lowBound=0,
        upBound=POWER_MW,
    )

    discharge = pulp.LpVariable.dicts(
        "discharge_mw",
        range(n),
        lowBound=0,
        upBound=POWER_MW,
    )

    soc = pulp.LpVariable.dicts(
        "soc_mwh",
        range(n + 1),
        lowBound=MIN_SOC_MWH,
        upBound=MAX_SOC_MWH,
    )

    # Initial SOC
    model += soc[0] == INITIAL_SOC_MWH

    # SOC balance
    for t in range(n):

        model += (
            soc[t + 1]
            == soc[t]
            + charge[t] * INTERVAL_HOURS * CHARGE_EFFICIENCY
            - discharge[t] * INTERVAL_HOURS / DISCHARGE_EFFICIENCY
        )

    # Finish month at same SOC as we started
    model += soc[n] == INITIAL_SOC_MWH

    # Objective: maximise energy market revenue
    model += pulp.lpSum(
        df.loc[t, "RRP"]
        * INTERVAL_HOURS
        * (discharge[t] - charge[t])
        for t in range(n)
    )

    solver = pulp.HiGHS(msg=False)

    model.solve(solver)

    print("Solver status:", pulp.LpStatus[model.status])

    results = []

    for t in range(n):

        charge_mw = pulp.value(charge[t])
        discharge_mw = pulp.value(discharge[t])
        soc_mwh = pulp.value(soc[t + 1])

        revenue = (
            discharge_mw - charge_mw
        ) * INTERVAL_HOURS * df.loc[t, "RRP"]

        results.append(
            {
                "SETTLEMENTDATE": df.loc[t, "SETTLEMENTDATE"],
                "RRP": df.loc[t, "RRP"],
                "charge_mw": charge_mw,
                "discharge_mw": discharge_mw,
                "soc_mwh": soc_mwh,
                "revenue": revenue,
            }
        )

    return pd.DataFrame(results)


def optimise_battery_milp(prices: pd.DataFrame) -> pd.DataFrame:

    df = prices.reset_index(drop=True).copy()
    n = len(df)

    model = pulp.LpProblem(
        "BESS_Energy_Arbitrage_MILP",
        pulp.LpMaximize,
    )

    # Continuous decision variables
    charge = pulp.LpVariable.dicts(
        "charge_mw",
        range(n),
        lowBound=0,
        upBound=POWER_MW,
    )

    discharge = pulp.LpVariable.dicts(
        "discharge_mw",
        range(n),
        lowBound=0,
        upBound=POWER_MW,
    )

    soc = pulp.LpVariable.dicts(
        "soc_mwh",
        range(n + 1),
        lowBound=MIN_SOC_MWH,
        upBound=MAX_SOC_MWH,
    )

    # Binary operating mode
    # 1 = charging allowed
    # 0 = discharging allowed
    charge_mode = pulp.LpVariable.dicts(
        "charge_mode",
        range(n),
        cat="Binary",
    )

    # Initial SOC
    model += soc[0] == INITIAL_SOC_MWH

    # Battery constraints
    for t in range(n):

        # Prevent simultaneous charging and discharging
        model += charge[t] <= POWER_MW * charge_mode[t]

        model += discharge[t] <= POWER_MW * (1 - charge_mode[t])

        # SOC transition
        model += (
            soc[t + 1]
            == soc[t]
            + charge[t] * INTERVAL_HOURS * CHARGE_EFFICIENCY
            - discharge[t] * INTERVAL_HOURS / DISCHARGE_EFFICIENCY
        )

    # End month at same SOC as start
    model += soc[n] == INITIAL_SOC_MWH

    # Maximise energy arbitrage revenue
    model += pulp.lpSum(
        df.loc[t, "RRP"]
        * INTERVAL_HOURS
        * (discharge[t] - charge[t])
        for t in range(n)
    )

    solver = pulp.HiGHS(msg=False)

    model.solve(solver)

    print("Solver status:", pulp.LpStatus[model.status])

    results = []

    for t in range(n):

        charge_mw = pulp.value(charge[t])
        discharge_mw = pulp.value(discharge[t])
        soc_mwh = pulp.value(soc[t + 1])

        revenue = (
            discharge_mw - charge_mw
        ) * INTERVAL_HOURS * df.loc[t, "RRP"]

        results.append(
            {
                "SETTLEMENTDATE": df.loc[t, "SETTLEMENTDATE"],
                "RRP": df.loc[t, "RRP"],
                "charge_mw": charge_mw,
                "discharge_mw": discharge_mw,
                "soc_mwh": soc_mwh,
                "revenue": revenue,
            }
        )

    return pd.DataFrame(results)