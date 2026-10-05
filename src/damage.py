from __future__ import annotations
import cv2
import numpy as np
DAMAGE_CLASSES=["surface_anomaly","crack_candidate","stain_candidate"]
def detect_damage_candidates(image, *, min_area_px=100, max_regions=25):
    if image is None:return []
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY); blur=cv2.GaussianBlur(gray,(5,5),0); residual=cv2.absdiff(gray,blur)
    _,mask=cv2.threshold(residual,18,255,cv2.THRESH_BINARY); k=np.ones((3,3),np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,k); mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,k)
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); h,w=gray.shape[:2]; out=[]
    for c in sorted(contours,key=cv2.contourArea,reverse=True)[:max_regions]:
        area=float(cv2.contourArea(c))
        if area<min_area_px: continue
        x,y,bw,bh=cv2.boundingRect(c)
        out.append({"class":"surface_anomaly","bbox_px":[int(x),int(y),int(bw),int(bh)],"area_px":area,"extent_px":{"width":int(bw),"height":int(bh),"area":area,"image_width":int(w),"image_height":int(h)},"confidence":{"value":0.25,"status":"candidate_only","reason":"heuristic visual anomaly detector"},"requires_review":True})
    return out
def concealed_damage_flag(*, visible_damage_count, low_visibility, depth_confidence_low):
    flag=bool(low_visibility or depth_confidence_low)
    return {"flagged":flag,"rule":"Flag when visibility is low or depth confidence is low; do not infer concealed damage as confirmed damage.","visible_damage_count":int(visible_damage_count),"requires_human_inspection":flag}
