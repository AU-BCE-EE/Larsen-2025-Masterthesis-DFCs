# Packages
import matplotlib.pyplot as plt # plotting
import numpy as np # quick calculations for arrays
from pathlib import Path # handles folder and file calls

# output folder
output_folder_figures = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Report Graphs")
output_name_figure = Path("2026-06-06-graph-AcEmis-FieldPig.png")
output_path_figures = output_folder_figures / output_name_figure

# uniform axis aestetics
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})

# Data - relative reductions
Raw = [5.187, 2.700, 5.655]
AA = [3.026, 3.272, 1.859]
SA = [3.518, 1.841, 2.377]
TH = [3.227, 5.044, 6.141]
OSI = [-0.400, -0.743, 1.054]
#PSA = [75.20, 28.33, 28.83]

# Data info
treatments = [Raw, AA, SA, TH, OSI]
labels = ['None', 'AA', 'SA', 'TH', 'OSI']
colors = ['darkorange', 'blue', 'darkgreen', 'purple', 'red',]              


x_positions = [1, 2, 3, 4, 5]  # one position per treatment

# Means and stdev
means = [np.mean(t) for t in treatments]
stdevs = [np.std(t, ddof=1) for t in treatments]

# prepare the figure
fig, ax = plt.subplots(figsize=(10, 5))  # wider figure for 6 groups

# actual plot function
# ax.bar() draws the bars; yerr adds the ±stdev whiskers
# capsize controls the width of the horizontal cap on the error bar
# zorder controls which objects is on top - higher is on top
ax.bar(x_positions, means, yerr=stdevs, color=colors, width=0.5, capsize=5, error_kw={'linewidth': 1.5, 'ecolor': 'black'}, zorder=3)

# overlay individual datapoints
for x, data in zip(x_positions, treatments): 
    ax.scatter(np.full(len(data), x), data, color='black', s=10, zorder=4)  # zorder=4 puts dots on top of bars
# s is the size of the 

# ticks and labels for each treatment on the x-axis
ax.set_xticks(x_positions)
ax.set_xticklabels(labels, rotation=20, ha='right')  # rotated so labels don't overlap
ax.set_ylabel('Accumulated Emissions (%)')

# y-axis
ax.set_xlim(0.5, 5.5)
ax.set_ylim(-1, 7)  # adjust to your data range
ax.set_axisbelow(True)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close()
