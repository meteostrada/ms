import h5py, numpy as np, sys
f=h5py.File("sample.nc")
def walk(n,o):
    if isinstance(o,h5py.Dataset):
        a={k:(v if np.ndim(v)==0 or np.size(v)<6 else '..') for k,v in o.attrs.items() if k in('scale_factor','add_offset','_FillValue','units','long_name','valid_range','grid_mapping')}
        print("DS",n,o.shape,o.dtype,a)
f.visititems(walk)
print("ATTRS",{k:str(v)[:100] for k,v in f.attrs.items()})

for k,v in f.attrs.items():
    if any(w in k.lower() for w in ("geospatial","time_coverage","license","spatial","resolution","summary","platform","dataset","title","processing")): print("A",k,"=",str(v)[:200])
print("Rows",f["Rows"][:3],f["Rows"][-3:],"Columns",f["Columns"][:3],f["Columns"][-3:])
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rr=f["RRQPE"]
latmax=float(np.ravel(f.attrs.get("geospatial_lat_max",65))[0]) if "geospatial_lat_max" in f.attrs else 65.0
latmin=float(np.ravel(f.attrs.get("geospatial_lat_min",-65))[0]) if "geospatial_lat_min" in f.attrs else -65.0
lonmin=float(np.ravel(f.attrs.get("geospatial_lon_min",-180))[0]) if "geospatial_lon_min" in f.attrs else -180.0
lonmax=float(np.ravel(f.attrs.get("geospatial_lon_max",180))[0]) if "geospatial_lon_max" in f.attrs else 180.0
print("extent",latmin,latmax,lonmin,lonmax)
H,W=rr.shape
def row(lat): return int(round((latmax-lat)/(latmax-latmin)*(H-1)))
def col(lon): return int(round((lon-lonmin)/(lonmax-lonmin)*(W-1)))
r0,r1,c0,c1=row(47),row(30),col(-12),col(45)
a=rr[r0:r1,c0:c1].astype(float); a=np.where(a==-9990,np.nan,a*0.1)
d=f["DQF"][r0:r1,c0:c1]
print("crop",a.shape,"valid share",np.isfinite(a).mean(),"rain>0.3",np.nanmean(a>0.3),"max",np.nanmax(a))
for name,(la,lo) in {"Atene":(37.98,23.73),"Istanbul":(41.0,29.0),"Tunisi":(36.8,10.2),"Roma":(41.9,12.5),"Pavia":(45.2,9.15)}.items():
    r,c=row(la),col(lo); v=rr[r,c]; print("PUNTO",name,r,c,v, f["DQF"][r,c])
fig,ax=plt.subplots(figsize=(14,7))
ax.imshow(np.ma.masked_invalid(a),cmap="turbo",vmin=0,vmax=15)
fig.savefig("europa.png",dpi=80)
