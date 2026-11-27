#!/usr/bin/env python3
"""Generate a terminal SVG from GitHub's contribution calendar; no dependencies."""
import argparse, datetime as dt, json, os, pathlib, urllib.request, xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets/terminal.template.svg'
OUTPUT = ROOT / 'assets/terminal.svg'
COLORS = ['#21262d','#0e4429','#006d32','#26a641','#39d353']
LEVELS = {k:i for i,k in enumerate(('NONE','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FOURTH_QUARTILE'))}

def fetch():
    token = os.environ.get('CONTRIBUTIONS_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token: raise RuntimeError('No GitHub API token supplied')
    query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date weekday contributionCount contributionLevel}}}}}}'''
    request = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query':query,'variables':{'login':'danielaplan'}}).encode(), headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'danielaplan-terminal-calendar'})
    with urllib.request.urlopen(request, timeout=45) as response: payload=json.load(response)
    if payload.get('errors'): raise RuntimeError('GitHub GraphQL: '+str(payload['errors']))
    return payload['data']['user']['contributionsCollection']['contributionCalendar']

def render(calendar=None, demo=False):
    pieces=['<g id="contribution-panel">','<rect x="704" y="99" width="174" height="419" rx="9" fill="#161b22" stroke="#30363d"/>']
    def text(x,y,s,color='#e6edf3',size=11,bold=False,anchor='start'):
        pieces.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(str(s))}</text>')
    text(716,120,'$ git activity','#3fb950',13,True)
    text(716,146,calendar['totalContributions'] if calendar else '—','#3fb950',25,True)
    text(716,161,'contributions / year','#8b949e',10)
    text(716,179,'LAST 26 WEEKS','#8b949e',10,True)
    weeks=calendar['weeks'][-26:] if calendar else []
    weeks=[None]*(26-len(weeks))+weeks
    for i,c in enumerate('SMTWTFS'): text(771+i*13,195,c,'#8b949e',9,anchor='middle')
    for row,week in enumerate(weeks):
        y=202+row*10
        days={d['weekday']:d for d in week['contributionDays']} if week else {}
        if week and row%4==0 and days:
            date=dt.date.fromisoformat(min(d['date'] for d in days.values()))
            text(716,y+8,date.strftime('%b %d'),'#8b949e',9)
        for col in range(7):
            d=days.get(col); fill=COLORS[LEVELS[d['contributionLevel']]] if d else '#161b22'
            stroke='#30363d' if not d else fill
            title=f"{d['date']}: {d['contributionCount']} contributions" if d else 'No data'
            pieces.append(f'<rect x="{767+col*13}" y="{y}" width="9" height="8" rx="1.5" fill="{fill}" stroke="{stroke}" stroke-width=".6"><title>{escape(title)}</title></rect>')
    text(716,479,'Less','#8b949e',10)
    for i,c in enumerate(COLORS): pieces.append(f'<rect x="{752+i*13}" y="470" width="10" height="10" rx="2" fill="{c}"/>')
    text(865,479,'More','#8b949e',10,anchor='end')
    status='DEMO / SAMPLE DATA' if demo else ('AUTO-SYNC / 6H' if calendar else 'AWAITING FIRST SYNC')
    pieces.append('<circle cx="720" cy="500" r="3" fill="#3fb950"><animate attributeName="opacity" values="1;.4;1" dur="2.8s" repeatCount="indefinite"/></circle>')
    text(730,504,status,'#8b949e',9)
    pieces.append('</g>')
    source=TEMPLATE.read_text(); result=source.replace('</svg>',''.join(pieces)+'</svg>')
    ET.fromstring(result)
    return result

def sample():
    import random
    r=random.Random(42); today=dt.date.today(); start=today-dt.timedelta(days=(today.weekday()+1)%7+25*7)
    weeks=[]
    for i in range(26):
        days=[]
        for j in range(7):
            day=start+dt.timedelta(days=i*7+j)
            if day>today: continue
            level=r.choices(range(5),[50,25,15,7,3])[0]
            days.append({'date':day.isoformat(),'weekday':j,'contributionCount':[0,1,3,6,10][level],'contributionLevel':list(LEVELS)[level]})
        weeks.append({'contributionDays':days})
    return {'totalContributions':sum(d['contributionCount'] for w in weeks for d in w['contributionDays']), 'weeks':weeks}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--empty',action='store_true'); p.add_argument('--demo',action='store_true'); p.add_argument('--output',type=pathlib.Path,default=OUTPUT); args=p.parse_args()
    data=None if args.empty else sample() if args.demo else fetch()
    args.output.write_text(render(data,args.demo))
