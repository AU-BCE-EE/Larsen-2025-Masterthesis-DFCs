import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
 
output_folder_figures = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Report Graphs")
output_name_figure = Path("graph-PHD-PLD-F.comparison.pdf")
output_path_figures = output_folder_figures / output_name_figure
 
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})
 
HD = [26.655, 23.287, 22.568, 21.741, 20.797, 20.789]
LD = [20.331, 18.672, 17.681, 15.567, 10.155, 8.697]
F  = [32.826, 32.469, 22.805, 22.554, 13.138, 11.622]
 
fig, ax = plt.subplots(figsize=(7, 5))
 
rng = np.random.default_rng(42)
 
def jitter(n, width=0.06):
    return rng.uniform(-width, width, n)
 
ax.scatter(np.ones(len(HD)) + jitter(len(HD)), HD,
           color='olive', s=80, zorder=3, label='Cattle PHD')
ax.scatter(np.ones(len(LD)) * 2 + jitter(len(LD)), LD,
           color='lightcoral', s=80, zorder=3, label='Cattle PLD')
ax.scatter(np.ones(len(F)) * 3 + jitter(len(F)), F,
           color='darkcyan', s=80, zorder=3, label='Cattle F')
 
# Mean lines
ax.hlines(np.mean(HD), 0.75, 1.25, colors='olive',
          linewidths=1.5, linestyles='--', zorder=2)
ax.hlines(np.mean(LD), 1.75, 2.25, colors='lightcoral',
          linewidths=1.5, linestyles='--', zorder=2)
ax.hlines(np.mean(F),  2.75, 3.25, colors='darkcyan',
          linewidths=1.5, linestyles='--', zorder=2)
 
ax.set_xticks([1, 2, 3])
ax.set_xticklabels(['Cattle PHD', 'Cattle PLD', 'Cattle F'])
ax.set_ylabel('Accumulated Emissions (% TAN)')
ax.set_xlim(0.5, 3.5)
ax.set_ylim(5, 37)
 
ax.set_axisbelow(True)
ax.spines[['top', 'right']].set_visible(False)
 
plt.tight_layout()
plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
plt.show()
plt.close()