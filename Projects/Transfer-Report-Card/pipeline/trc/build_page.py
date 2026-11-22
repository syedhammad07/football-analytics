import json,gzip,base64,collections
D=json.load(open('data.json')); DET=json.load(open('detail.json')); EV=json.load(open('evidence.json'))
by=collections.defaultdict(lambda:{'d':{},'e':{}})
for i,r in enumerate(D):
    y=r[4]
    if DET[i]: by[y]['d'][i]=DET[i]
    if EV[i]: by[y]['e'][i]=EV[i]
CH={str(y):base64.b64encode(gzip.compress(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode(),9)).decode() for y,v in sorted(by.items())}
t=open('template.html').read()
import datetime
out=t.replace('__BUILT__',datetime.date.today().strftime('%d %B %Y')).replace('__DATA__',json.dumps(D,separators=(',',':'),ensure_ascii=False)).replace('__CH__',json.dumps(CH,separators=(',',':'))).replace('__PL__',open('players.json').read())
open('index.html','w').write(out); print(len(out)//1024,'KB html;',len(D),'rows')
