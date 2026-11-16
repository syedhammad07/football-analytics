import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
BG,FG,MUTED,BLUE,GREY='#0A1628','#EAF1FB','#8FA3BF','#5AB0FF','#4C6A94'
fig,axs=plt.subplots(1,2,figsize=(10,4.9),dpi=200,facecolor=BG)
def bridge(ax,title,base,mid,end,fmt,unit):
    vals=[base,mid-base,end-mid,end]
    labels=['2025/26\nBrighton','Who plays,\nincl. new\nsignings','Returning\nplayers doing\nmore per 90','2026/27\nso far']
    bottoms=[0,base,mid,0]; heights=[base,mid-base,end-mid,end]
    cols=[GREY,'#2F4C78',BLUE,GREY]
    ax.set_facecolor(BG)
    ax.bar(range(4),heights,bottom=bottoms,color=cols,width=.62,zorder=3)
    tops=[base,mid,end,end]
    txt=[fmt.format(base),'+'+fmt.format(mid-base),'+'+fmt.format(end-mid),fmt.format(end)]
    for i,(t,tp) in enumerate(zip(txt,tops)):
        ax.text(i,tp+(end*0.025),t,ha='center',va='bottom',color=FG,fontsize=10.5,fontweight='bold')
    ax.set_xticks(range(4)); ax.set_xticklabels(labels,color=MUTED,fontsize=8.2)
    ax.set_ylim(0,end*1.18); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(axis='x',length=0)
    ax.set_title(title,color=FG,fontsize=11.5,fontweight='bold',loc='left',pad=10)
    share=(end-mid)/(end-base)
    ax.text(0.0,-0.30,f"Returning players: {share:.0%} of the rise",transform=ax.transAxes,color=BLUE,fontsize=9.2,fontweight='bold')
bridge(axs[0],'Shots per 90',10.48,11.89,14.46,'{:.1f}','')
bridge(axs[1],'Expected goals (xG) per 90',1.67,1.84,2.17,'{:.2f}','')
fig.suptitle("Where Brighton's attacking rise comes from",color=FG,fontsize=14,fontweight='bold',x=0.05,ha='left',y=0.99)
fig.text(0.05,0.015,"7 returning players (600+ min last season, 300+ this season) at last season's per-90 rates; everyone else as they have played. Premier League stats (Opta), 2026/27 first ~9 games.",color=MUTED,fontsize=6.6)
fig.subplots_adjust(top=0.82,bottom=0.30,left=0.04,right=0.97,wspace=0.12)
out='assets/brighton_bridge.png'
fig.savefig(out,facecolor=BG); print(out)
