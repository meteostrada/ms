import urllib.request, re, datetime
B="https://noaa-enterprise-rainrate-pds.s3.amazonaws.com"
def get(u, hdr=None, n=None):
    r=urllib.request.Request(u, headers=hdr or {"User-Agent":"MeteoStrada-sonda"})
    with urllib.request.urlopen(r, timeout=90) as f:
        return f.status, dict(f.headers), (f.read() if n is None else f.read(n))
def ls(prefix, delim="/", extra=""):
    s,h,b=get(f"{B}/?list-type=2&prefix={prefix}&delimiter={delim}{extra}")
    t=b.decode()
    return re.findall(r"<Prefix>([^<]*)</Prefix>",t)[1:], re.findall(r"<Key>([^<]*)</Key>",t), re.findall(r"<Size>(\d+)</Size>",t), re.findall(r"<LastModified>([^<]*)</LastModified>",t)
P="BLEND/RainRate-Blend-INST/"
d,k,s,m=ls(P); print("LEVEL1",d[:10],len(d),k[:5])
now=datetime.datetime.utcnow()
for sub in d[-3:]:
    d2,k2,s2,m2=ls(sub); print("SUB",sub,d2[-5:],len(d2),k2[-3:])
# prova con il giorno corrente / ultimo livello
cur=d[-1]
d2,k2,s2,m2=ls(cur)
cur2=d2[-1] if d2 else cur
d3,k3,s3,m3=ls(cur2)
while d3:
    cur2=d3[-1]; d3,k3,s3,m3=ls(cur2)
print("DEEPEST",cur2,len(k3))
allk,alls,allm=[],[],[]
d4,k4,s4,m4=ls(cur2,delim="")
for a,b,c in list(zip(k4,s4,m4))[-12:]: print("FILE",a,b,c)
print("NOW",now.isoformat())
if k4:
    key=k4[-1]
    s,h,body=get(f"{B}/{key}", hdr={"User-Agent":"x","Origin":"https://example.org"})
    print("GET",key,s,len(body)); 
    for x in ["Content-Type","Content-Length","Access-Control-Allow-Origin","Last-Modified"]: print(x,h.get(x))
    open("sample.nc","wb").write(body)
    print("HEAD16",body[:16])
