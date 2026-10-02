import os, sys, json, time, requests
D="/home/user/marketing/entregas/runway_teste"
B="https://api.dev.runwayml.com/v1"
H={"Authorization":"Bearer "+os.environ["RUNWAYML_API_SECRET"],"X-Runway-Version":"2024-11-06"}
BASE=("Keep the exact same man, same face, same identity, same expressions, same head and mouth movements and same clothing. "
"Do not change his face. Replace only the background with a real, modern, upscale law office: wooden bookshelves with legal books, "
"a large window with soft daylight, subtle natural motion in the background (a colleague walking by out of focus, slight parallax), "
"shallow depth of field. Relight the man to match the scene: soft, even frontal key light from the window side, natural skin tones, "
"balanced exposure, no harsh shadows, no color cast. Photorealistic, like footage from a professional cinema camera. Keep the original framing")
JOBS={
 "pmes":("pmes_trecho_16x9.mp4", BASE+" (horizontal close-up, head and shoulders)."),
 "iases":("iases_trecho_9x16.mp4", BASE+" (vertical selfie framing, arm-length close-up). Keep his sunglasses."),
}
log=json.load(open(sys.argv[1])) if os.path.exists(sys.argv[1]) else {}
def rec(name,**k): log.setdefault(name,{}).update(k); json.dump(log,open(sys.argv[1],"w"),indent=2,ensure_ascii=False)
for name,(fn,prompt) in JOBS.items():
    if log.get(name,{}).get("status")=="SUCCEEDED": continue
    r=requests.post(B+"/uploads",headers=H,json={"filename":fn,"type":"ephemeral"},timeout=60)
    if r.status_code!=200: rec(name,upload_error=f"{r.status_code} {r.text}"); continue
    u=r.json()
    with open(os.path.join(D,fn),"rb") as f:
        up=requests.post(u["uploadUrl"],data=u["fields"],files={"file":(fn,f,"video/mp4")},timeout=300)
    if up.status_code>=300: rec(name,upload_error=f"{up.status_code} {up.text[:500]}"); continue
    body={"model":"aleph2","videoUri":u["runwayUri"],"promptText":prompt}
    r=requests.post(B+"/video_to_video",headers=H,json=body,timeout=60)
    att=log.get(name,{}).get("attempts",[])
    att.append({"model":"aleph2","http":r.status_code,"response":r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:500]})
    rec(name,attempts=att,prompt=prompt,model="aleph2")
    if r.status_code!=200: continue
    tid=r.json()["id"]; rec(name,task_id=tid,estimatedCost=r.json().get("estimatedCost"))
    print(name,"task",tid,r.json().get("estimatedCost"),flush=True)
for name in JOBS:
    tid=log.get(name,{}).get("task_id")
    if not tid or log[name].get("status")=="SUCCEEDED": continue
    for _ in range(180):
        t=requests.get(f"{B}/tasks/{tid}",headers=H,timeout=60).json()
        if t.get("status") in ("SUCCEEDED","FAILED","CANCELLED"): break
        time.sleep(10)
    rec(name,status=t.get("status"),task=t)
    print(name,t.get("status"),t.get("failure"),t.get("failureCode"),flush=True)
    if t.get("status")=="SUCCEEDED":
        v=requests.get(t["output"][0],timeout=300); open(os.path.join(D,f"{name}_runway.mp4"),"wb").write(v.content)
