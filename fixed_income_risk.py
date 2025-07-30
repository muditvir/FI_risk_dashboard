import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs("data", exist_ok=True)
os.makedirs("dashboards", exist_ok=True)

yield_data = pd.read_csv("data/treasury_yields.csv", parse_dates=["Date"])
yield_changes = pd.read_csv("data/yield_changes.csv", parse_dates=["Date"])

yield_data.set_index("Date", inplace=True)
yield_changes.set_index("Date", inplace=True)

# Portfolio exposures
exposures = {
    "2Y": 25_000_000,
    "5Y": 50_000_000,
    "10Y": 75_000_000,
    "30Y": 100_000_000
}

# Calculate DV01 (1 basis point = 0.0001)
dv01s = {tenor: notional * 0.0001 for tenor, notional in exposures.items()}
total_dv01 = sum(dv01s.values())

# DV01 dataframe
dv01_df = pd.DataFrame({
    'Tenor': list(dv01s.keys()),
    'Exposure ($)': list(exposures.values()),
    'DV01 ($)': list(dv01s.values())
})

# PnL
pnl_df = pd.DataFrame(index=yield_changes.index)
for tenor in exposures.keys():
    pnl_df[f"PnL_{tenor}"] = -yield_changes[tenor] * dv01s[tenor]
pnl_df["Total_PnL"] = pnl_df.sum(axis=1)

# Historical 95% VaR
var_95 = np.percentile(pnl_df["Total_PnL"], 5)

with pd.ExcelWriter("dashboards/dashboard_output.xlsx", engine='xlsxwriter') as writer:
    dv01_df.to_excel(writer, sheet_name="DV01 Exposure", index=False)
    pnl_df.to_excel(writer, sheet_name="PnL Attribution")
    yield_data.to_excel(writer, sheet_name="Yield Curves")

pnl_df.reset_index().to_excel("dashboards/powerbi_dashboard_data.xlsx", index=False)
dv01_df.to_excel("dashboards/powerbi_dv01_data.xlsx", index=False)

# Plot 1: Yield curve evolution
plt.figure(figsize=(12, 6))
for tenor in yield_data.columns:
    plt.plot(yield_data.index, yield_data[tenor], label=tenor)
plt.title("Treasury Yield Curve Evolution")
plt.ylabel("Yield (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("data/yield_curve_plot.png")
plt.close()

# Plot 2: Daily PnL
plt.figure(figsize=(12, 6))
for tenor in exposures:
    plt.plot(pnl_df.index, pnl_df[f"PnL_{tenor}"], label=f"{tenor}")
plt.plot(pnl_df.index, pnl_df["Total_PnL"], color='black', label="Total", linewidth=2)
plt.title("Daily PnL by Tenor")
plt.ylabel("PnL ($)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("dashboards/daily_pnl_breakdown.png")
plt.close()

# Plot 3: PnL Distribution and VaR
plt.figure(figsize=(10, 5))
sns.histplot(pnl_df["Total_PnL"], bins=40, kde=True)
plt.axvline(var_95, color='red', linestyle='--', label=f"95% VaR = ${var_95:,.0f}")
plt.title("Distribution of Daily Portfolio PnL")
plt.xlabel("Total Daily PnL ($)")
plt.legend()
plt.tight_layout()
plt.savefig("dashboards/pnl_distribution.png")
plt.close()

# Console output summary
print("\n✅ DV01 Exposure:")
print(dv01_df.to_string(index=False))

print(f"\n📉 1-Day 95% Historical VaR: ${var_95:,.2f}")

print("\n📁 Files saved in 'dashboards/' and 'data/' folders.")
