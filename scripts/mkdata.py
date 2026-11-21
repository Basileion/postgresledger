import json
C='2026-11-20'
def P(plan,ram,vcpu,incl,extra,base,ha=False,maxs=None,shared=False,flag=None):
    return dict(plan=plan,ram=ram,vcpu=vcpu,incl=incl,extra=extra,base=base,ha=ha,maxs=maxs,shared=shared,flag=flag)
V=[]
V.append(dict(id='digitalocean',name='DigitalOcean Managed PostgreSQL',short='DigitalOcean',source='https://www.digitalocean.com/pricing/managed-databases',read='partial',
 free='No free tier for Managed Databases.',
 notes=['PostgreSQL Standard single-node prices, $/mo as listed. Extra storage $0.215/GiB/mo in 10 GiB steps, up to the top of each size\'s storage range.','Standby (HA) nodes are sold as additional nodes; their price was not listed as text, so HA is not modeled here.','Only the 5 sizes up to 16 GiB were listed on the page.'],
 plans=[P('1 GiB / 1 vCPU',1,'1',10,0.215,15.15,maxs=30),P('2 GiB / 1 vCPU',2,'1',30,0.215,30.45,maxs=60),P('4 GiB / 2 vCPU',4,'2',60,0.215,60.90,maxs=120),P('8 GiB / 4 vCPU',8,'4',140,0.215,122.10,maxs=280),P('16 GiB / 6 vCPU',16,'6',290,0.215,244.35,maxs=580)]))
sb=[('Micro',1,'shared',10),('Small',2,'shared',15),('Medium',4,'shared',60),('Large',8,'2 dedicated',110),('XL',16,'4 dedicated',210),('2XL',32,'8 dedicated',410),('4XL',64,'16 dedicated',960)]
V.append(dict(id='supabase',name='Supabase',short='Supabase',source='https://supabase.com/pricing',read='full',
 free='Free: 500 MB database, shared CPU, 500 MB RAM; paused after 1 week of inactivity; 2 active projects.',
 notes=['Pro plan $25/mo includes $10/mo compute credit (covers one Micro) and 8 GB disk per project, then $0.125/GB.','Bill here = $25 plan + compute add-on - $10 credit + extra disk, for one project.','Point-in-time recovery is $100/mo per 7 days of retention (not included).'],
 plans=[P(f'Pro + {n} compute',r,c,8,0.125,round(25+p-10,2),shared=(c=='shared')) for n,r,c,p in sb]))
neon=[]
for cu in [0.25,0.5,1,2,4,8,16]:
    neon.append(P(f'Launch, {cu:g} CU always on',cu*4,f'{cu:g} CU',0,0.35,round(0.106*cu*730,2)))
for cu in [0.25,0.5,1,2,4,8,16]:
    neon.append(P(f'Scale, {cu:g} CU always on',cu*4,f'{cu:g} CU',0,0.35,round(0.222*cu*730,2)))
V.append(dict(id='neon',name='Neon',short='Neon',source='https://neon.com/pricing',read='full',
 free='Free: 100 CU-hours per project, 1 GB storage per project (20 GB account total), scale-to-zero after 5 minutes (cannot be disabled).',
 notes=['Usage-based: Launch $0.106/CU-hour, Scale $0.222/CU-hour; storage $0.35/GB-month. 1 CU is about 4 GB RAM.','Rows here assume compute always on for 730 hours a month. With scale-to-zero, idle hours cost $0, so intermittent workloads pay far less (Neon lists an intermittent small database at about $15/mo on Launch).','Launch autoscales up to 16 CU (64 GB RAM).'],
 plans=neon))
rd=[('0.1c-256mb',0.25,'<1',6),('0.5c-1g',1,'<1',19),('1c-2g',2,'1',40),('1c-4g',4,'1',55),('2c-4g',4,'2',75),('2c-8g',8,'2',100),('2c-16g',16,'2',160),('4c-16g',16,'4',200),('4c-32g',32,'4',350),('8c-32g',32,'8',400),('8c-64g',64,'8',750),('16c-64g',64,'16',800)]
V.append(dict(id='render',name='Render Postgres',short='Render',source='https://render.com/pricing',read='full',
 free='Free: 256 MB RAM Postgres instance.',
 notes=['Instance price plus storage at $0.30/GB per month (storage is not bundled with the instance).','Workspace plan is extra: Hobby $0, Pro $25/mo. Bills here assume Hobby.','Larger instances up to 64 CPU / 384 GB are listed; rows here stop at 64 GB RAM.'],
 plans=[P(f'{i}',r,c,0,0.30,p) for i,r,c,p in rd]))
ps=[('PS-5',0.5,'1/16',5,15),('PS-10',1,'1/8',10,30),('PS-20',2,'1/4',17,50),('PS-40',4,'1/2',28,83),('PS-80',8,'1',50,148),('PS-160',16,'2',96,286),('PS-320',32,'4',190,570),('PS-640',64,'8',379,1135)]
pl=[]
for s,r,c,single,ha in ps:
    pl.append(P(f'{s} arm64 single node',r,c,None,None,single,flag='storage'))
    pl.append(P(f'{s} arm64 HA (3 nodes)',r,c,None,None,ha,ha=True,flag='storage'))
V.append(dict(id='planetscale',name='PlanetScale Postgres',short='PlanetScale',source='https://planetscale.com/pricing',read='partial',
 free='No free tier listed for Postgres.',
 notes=['AWS us-east-1 prices, arm64 (x86-64 costs the same or more). HA = 1 primary + 2 replicas.','The SKU price includes a starting network volume but not extra EBS storage, backups or egress; the extra-storage rate is not printed on the page, so bills here are compute only and understate storage-heavy setups.'],
 plans=pl))
V.append(dict(id='aiven',name='Aiven for PostgreSQL',short='Aiven',source='https://aiven.io/pricing?product=pg',read='partial',
 free='Free: 1 VM, 1 CPU, 1 GB RAM, 1 GB storage; no cloud or region choice.',
 notes=['Only entry prices are printed; larger plans sit behind "View 7 plans". Rows use each plan\'s entry configuration.','All networking cost is included per the page. Dynamic disk sizing costs extra on Startup and up (rate not printed), so extra storage is not modeled.','Business adds high availability (2 VMs); Premium adds a second standby (3 VMs).'],
 plans=[P('Developer',1,'1',8,None,5),P('Hobbyist',1,'1',8,None,12),P('Startup (entry)',4,'2',80,None,75),P('Business (entry, HA)',4,'2',80,None,180,ha=True),P('Premium (entry, 3 nodes)',4,'2',80,None,270,ha=True)]))
hk=[('Standard 0',4,64,50),('Standard 2',8,256,200),('Standard 3',15,512,400),('Standard 4',30.5,768,750),('Standard 5',61,1024,1400)]
hp=[('Premium 0',4,64,200),('Premium 2',8,256,350),('Premium 3',15,512,750),('Premium 4',30.5,768,1200),('Premium 5',61,1024,2500)]
V.append(dict(id='heroku',name='Heroku Postgres',short='Heroku',source='https://elements.heroku.com/addons/heroku-postgresql',read='full',
 free='No free plan. Essential 0 is $5/mo (shared, 1 GB storage).',
 notes=['Classic plans bundle a storage cap; there is no per-GB add-on, so a bigger disk means a bigger plan.','Essential 0/1/2 ($5/$9/$20, 1/10/32 GB) run on shared resources with no stated RAM, so they are not in RAM-based comparisons.','Premium plans add high availability. Advanced tier pricing was not printed as text.'],
 plans=[P(n,r,'',s,None,p,maxs=s) for n,r,s,p in hk]+[P(n,r,'',s,None,p,ha=True,maxs=s) for n,r,s,p in hp]))
for v in V: v['checked']=C
json.dump(V,open('/workspace/postgresledger/data/vendors.json','w'),indent=1)
print(len(V),sum(len(v['plans']) for v in V))
