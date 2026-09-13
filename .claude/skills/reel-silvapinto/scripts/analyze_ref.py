import cv2, numpy as np, os, sys, json
name=sys.argv[1]; d=f"an_{name}"; fps=15
files=sorted(os.listdir(d)); n=len(files)
casc=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
rows=[]; prev=None
for i,f in enumerate(files):
    im=cv2.imread(os.path.join(d,f)); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    faces=casc.detectMultiScale(g,1.1,4,minSize=(40,40))
    fw=max([w for (x,y,w,h) in faces],default=0); fx=fy=0
    if fw: x,y,w,h=max(faces,key=lambda b:b[2]); fx,fy=x+w/2,y+h/2
    sharp=cv2.Laplacian(g,cv2.CV_64F).var(); bright=g.mean()
    diff=0 if prev is None else float(np.mean(cv2.absdiff(g,prev)))
    hist=cv2.calcHist([g],[0],None,[32],[0,256]).flatten(); hist/=hist.sum()
    hd=0 if prev is None else float(np.abs(hist-prevh).sum())
    rows.append(dict(t=round(i/fps,2),fw=int(fw),fx=round(fx,1),fy=round(fy,1),sharp=round(sharp,1),bright=round(bright,1),diff=round(diff,2),hd=round(hd,3)))
    prev=g; prevh=hist
json.dump(rows,open(f"an_{name}.json","w"))
# cuts: big frame diff
diffs=np.array([r['diff'] for r in rows]); hds=np.array([r['hd'] for r in rows]); sharps=np.array([r['sharp'] for r in rows]); fws=np.array([r['fw'] for r in rows],float)
cuts=[rows[i]['t'] for i in range(1,n) if diffs[i]>25 or hds[i]>0.5]
# merge cuts within 0.3s
m=[]; 
for c in cuts:
    if m and c-m[-1]<0.3: continue
    m.append(c)
print(f"== {name}: {n/fps:.1f}s, cuts(hard)={len(m)} at", [round(c,1) for c in m])
# face width smoothed & jumps (zoom changes)
fw_s=fws.copy(); 
for i in range(n):
    if fw_s[i]==0: fw_s[i]=fw_s[i-1] if i>0 else 0
med=np.median(fw_s[fw_s>0]); print("face width median px (of 360):",med)
# detect zoom level segments: jumps > 12% between consecutive frames
jumps=[(rows[i]['t'],round(fw_s[i-1]),round(fw_s[i])) for i in range(1,n) if fw_s[i-1]>0 and fw_s[i]>0 and abs(fw_s[i]/fw_s[i-1]-1)>0.12]
print("face-size jumps (t, before, after):",jumps[:40])
# blur dips: sharpness < 35% of rolling median
medS=np.median(sharps); dips=[rows[i]['t'] for i in range(n) if sharps[i]<0.35*medS]
print("sharpness median",round(medS,1),"blur-dip frames:",[round(x,1) for x in dips][:60])
# brightness spikes (flash)
medB=np.median([r['bright'] for r in rows]); fl=[rows[i]['t'] for i in range(n) if rows[i]['bright']>medB*1.5]
print("flash frames:",[round(x,1) for x in fl][:40])
# per-second zoom profile
prof=[(r['t'],int(fw_s[i])) for i,r in enumerate(rows) if i%7==0]
print("zoom profile (t,facepx):",prof)
