"""Draw diagrams from the project's actual training and analysis pipeline."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
out=Path(__file__).resolve().parents[2]/'figures/comparison'; out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
fig,ax=plt.subplots(figsize=(12,2.3)); ax.set(xlim=(0,12),ylim=(0,2)); ax.axis('off')
labels=['CIFAR-10','Distributed\nsampler','1 process /\n2-process DDP','Normal / delayed\nsynchronization','Training metrics /\nsynthetic profiler','Statistics / plots','Report']
for i,label in enumerate(labels):
 x=.12+i*1.7; ax.add_patch(FancyBboxPatch((x,.65),1.45,.7,boxstyle='round,pad=.07',facecolor='#e8f1f7',edgecolor='#235789')); ax.text(x+.725,1,label,ha='center',va='center')
 if i<6: ax.annotate('',xy=(x+1.67,1),xytext=(x+1.48,1),arrowprops={'arrowstyle':'->','color':'#235789'})
fig.tight_layout(); fig.savefig(out/'architecture.png',dpi=200,bbox_inches='tight'); plt.close(fig)
fig,ax=plt.subplots(figsize=(12,3)); ax.set(xlim=(0,12),ylim=(0,3)); ax.axis('off')
for row,strategy in enumerate(('Normal sync','Delayed sync')):
 y=2.15-row*1.35; ax.text(.15,y+.3,strategy,va='center',weight='bold')
 for i in range(4):
  x=1.65+i*2.12; sync=(row==0 or i==3); label=f'Microbatch {i+1}\nforward + backward\n'+('synchronize' if sync else 'no_sync: local accumulation')
  ax.add_patch(FancyBboxPatch((x,y),1.9,.68,boxstyle='round,pad=.04',facecolor='#dcecf6' if sync else '#e9f3e5',edgecolor='#456')); ax.text(x+.95,y+.34,label,ha='center',va='center',fontsize=8)
  ax.annotate('',xy=(x+2.11,y+.34),xytext=(x+1.94,y+.34),arrowprops={'arrowstyle':'->'})
 ax.text(10.25,y+.34,'Optimizer\nstep',ha='center',va='center',bbox={'boxstyle':'round','facecolor':'#fce8cd','edgecolor':'#a76'})
fig.tight_layout(); fig.savefig(out/'sync_flow.png',dpi=200,bbox_inches='tight'); plt.close(fig)
