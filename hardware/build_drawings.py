"""Create matching editable SVG sheets and a Korean vector PDF. Python + reportlab."""
from pathlib import Path
from html import escape
import json
import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, landscape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'web' / 'assets' / 'drawings'
PDF = ROOT / 'web' / 'downloads' / 'chamgap-assembly-v1.pdf'
OUT.mkdir(parents=True, exist_ok=True)
PDF.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('KR', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KRB', 'C:/Windows/Fonts/malgunbd.ttf'))
W, H = 1120, 792
PAGE = landscape(A3)
SCALE = PAGE[0] / W
c = canvas.Canvas(str(PDF), pagesize=PAGE, pageCompression=1)
c.setTitle('참값 × FlyCheck 하드웨어 조립도면 - 제작 검토용 v1 / 미실측')
c.setAuthor('CHAMGAP Project')
NAVY, BLUE, CYAN, GRAY = '#152C49', '#2F6BDE', '#008597', '#61738B'
LINE, PALE, WHITE, AMBER = '#D6E0EC', '#F2F6FC', '#FFFFFF', '#A75C12'
manifest = []


class Sheet:
    def __init__(self, number, file, title, subtitle):
        self.number, self.file, self.title = number, file, title
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="792" viewBox="0 0 1120 792" role="img" aria-label="{escape(title)}">', '<style>text{font-family:"Malgun Gothic","Noto Sans KR",sans-serif}</style>']
        c.saveState()
        c.scale(SCALE, SCALE)
        self.rect(0, 0, W, H, WHITE, WHITE)
        self.text(48, 35, 'CHAMGAP  /  FLYCHECK', 12, BLUE, True)
        self.text(48, 74, title, 27, NAVY, True)
        self.text(48, 103, subtitle, 12, GRAY)
        self.rect(850, 32, 222, 28, PALE, LINE, 6)
        self.text(961, 51, '제작 검토용 v1 / 미실측', 12, BLUE, True, 'middle')
        self.line(48, 119, 1072, 119, LINE)
        self.line(48, 720, 1072, 720, LINE)
        self.text(48, 740, '도면 기준  MASTER v4 · 18-21 / 29장   |   단위 mm   |   표기 치수 우선 · 축척 없음', 10, GRAY)
        self.text(48, 758, '실물 홀·체결·하중·DC 차단 정격 확정 전 가공 및 통전 승인용으로 사용하지 않음', 10, GRAY)
        self.text(1072, 742, f'CG-HW-{number:02d}   /   2026.10.01', 11, NAVY, True, 'end')
        self.text(1072, 760, f'{number:02d} / 08', 10, GRAY, anchor='end')
        manifest.append(dict(id=f'CG-HW-{number:02d}', file=file, title=title, description=subtitle, status='제작 검토용 v1 · 미실측'))

    def rect(self, x, y, w, h, fill=WHITE, stroke=LINE, radius=0, width=1, dash=False):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}"{self.dash_attr(dash)}/>')
        c.setLineWidth(width)
        c.setDash([5, 4] if dash else [])
        if fill: c.setFillColor(HexColor(fill))
        if stroke: c.setStrokeColor(HexColor(stroke))
        c.roundRect(x, H-y-h, w, h, radius, stroke=int(bool(stroke)), fill=int(bool(fill)))

    def dash_attr(self, dash):
        return ' stroke-dasharray="5 4"' if dash else ''

    def line(self, x1, y1, x2, y2, color=BLUE, width=1.2, dash=False):
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{self.dash_attr(dash)}/>')
        c.setStrokeColor(HexColor(color)); c.setLineWidth(width); c.setDash([5,4] if dash else [])
        c.line(x1, H-y1, x2, H-y2)

    def poly(self, points, fill=None, stroke=BLUE, width=1.2, dash=False, closed=True):
        coords=' '.join(f'{x},{y}' for x,y in points)
        tag='polygon' if closed else 'polyline'
        self.svg.append(f'<{tag} points="{coords}" fill="{fill or "none"}" stroke="{stroke}" stroke-width="{width}"{self.dash_attr(dash)}/>')
        p=c.beginPath(); p.moveTo(points[0][0], H-points[0][1])
        for x,y in points[1:]: p.lineTo(x,H-y)
        if closed: p.close()
        c.setStrokeColor(HexColor(stroke)); c.setLineWidth(width); c.setDash([5,4] if dash else [])
        if fill: c.setFillColor(HexColor(fill))
        c.drawPath(p,stroke=1,fill=int(bool(fill)))

    def circle(self,x,y,r,fill=WHITE,stroke=BLUE,width=1.2):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke}" stroke-width="{width}"/>')
        c.setStrokeColor(HexColor(stroke)); c.setLineWidth(width); c.setDash([])
        if fill:c.setFillColor(HexColor(fill))
        c.circle(x,H-y,r,stroke=1,fill=int(bool(fill)))

    def text(self,x,y,t,size=12,color=NAVY,bold=False,anchor='start'):
        # Both formats share measured text and coordinates; no raster lettering.
        self.svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(str(t))}</text>')
        c.setFont('KRB' if bold else 'KR', size); c.setFillColor(HexColor(color))
        if anchor=='middle':c.drawCentredString(x,H-y,str(t))
        elif anchor=='end':c.drawRightString(x,H-y,str(t))
        else:c.drawString(x,H-y,str(t))

    def lines(self,x,y,lines,size=12,leading=20,color=GRAY,bold=False):
        for i,t in enumerate(lines):self.text(x,y+i*leading,t,size,color,bold)

    def arrow(self,x1,y1,x2,y2,color=BLUE,width=1.4):
        self.line(x1,y1,x2,y2,color,width)
        angle=math.atan2(y2-y1,x2-x1)
        a=7
        points=[(x2,y2),(x2-a*math.cos(angle-.45),y2-a*math.sin(angle-.45)),(x2-a*math.cos(angle+.45),y2-a*math.sin(angle+.45))]
        self.poly(points,color,color,.5)

    def dimh(self,x1,x2,y,source_y,label):
        self.line(x1,source_y,x1,y+6,LINE,.8);self.line(x2,source_y,x2,y+6,LINE,.8)
        self.line(x1,y,x2,y,GRAY,.8)
        for x in (x1,x2):self.line(x-4,y+4,x+4,y-4,GRAY,.8)
        self.text((x1+x2)/2,y-7,label,11,GRAY,anchor='middle')

    def dimv(self,y1,y2,x,source_x,label):
        self.line(source_x,y1,x+5,y1,LINE,.8);self.line(source_x,y2,x+5,y2,LINE,.8)
        self.line(x,y1,x,y2,GRAY,.8)
        for y in (y1,y2):self.line(x-4,y+4,x+4,y-4,GRAY,.8)
        self.text(x-9,(y1+y2)/2+4,label,11,GRAY,anchor='end')

    def label(self,x,y,n,t):
        self.circle(x,y-4,11,BLUE,BLUE)
        self.text(x,y,str(n),10,WHITE,True,'middle'); self.text(x+20,y,t,12,NAVY,True)

    def note(self,x,y,w,title,lines):
        height=45+len(lines)*19
        self.rect(x,y,w,height,PALE,None,6)
        self.text(x+16,y+24,title,13,NAVY,True)
        self.lines(x+16,y+46,lines,11,19)

    def table(self,x,y,widths,headers,rows,rowh=36,size=11):
        total=sum(widths)
        self.rect(x,y,total,31,NAVY,NAVY)
        xx=x
        for w,h in zip(widths,headers):self.text(xx+10,y+21,h,11,WHITE,True);xx+=w
        yy=y+31
        for i,row in enumerate(rows):
            self.rect(x,yy,total,rowh,PALE if i%2==0 else WHITE,LINE,.0,.5)
            xx=x
            for w,t in zip(widths,row):
                vals=str(t).split('\n')
                for k,v in enumerate(vals):self.text(xx+10,yy+19+k*15,v,size)
                xx+=w
            yy+=rowh
        return yy

    def finish(self):
        self.svg.append('</svg>')
        (OUT/self.file).write_text('\n'.join(self.svg),encoding='utf-8')
        c.restoreState();c.showPage()


def pilot():
    s=Sheet(1,'01-pilot.svg','01  책상 위 1구역 조립 배치','첫 제작 범위: ESP32 1대 · 온습도 2개 · 수분 프로브 2개 · 펌프 1대 · 계량 받침 1개')
    s.text(48,151,'평면 개념도',15,NAVY,True)
    s.text(48,174,'책상 크기와 이격거리는 현장에서 결정 / 점선은 점유·분리 구획',11,GRAY)
    s.rect(64,202,680,415,WHITE,LINE,8,width=1.4)
    s.rect(86,224,211,355,PALE,LINE,4,dash=True)
    s.text(105,250,'전장 구획 · 물보다 높은 고정 위치',11,NAVY,True)
    s.rect(109,275,166,128,WHITE,BLUE,6)
    s.text(192,306,'E01  ESP32',15,NAVY,True,'middle')
    s.text(192,332,'E07  HX711',13,GRAY,anchor='middle')
    s.text(192,360,'C07 함체 / 건식 받침',12,GRAY,anchor='middle')
    s.rect(109,430,166,55,WHITE,BLUE,4)
    s.text(192,453,'E05  DFR0457',13,NAVY,True,'middle')
    s.text(192,473,'전력선 별도 고정',11,GRAY,anchor='middle')
    s.circle(145,537,19,WHITE,BLUE,2)
    s.text(174,535,'물리 정지 조작부',11,NAVY,True)
    s.text(174,552,'접근 가능한 위치',10,GRAY)
    s.rect(337,243,197,233,PALE,BLUE,4,width=1.6)
    s.rect(355,279,161,161,WHITE,BLUE,2)
    s.text(436,326,'W03 용기',15,NAVY,True,'middle')
    s.text(436,352,'180 × 180 이하',12,GRAY,anchor='middle')
    s.text(436,380,'물받이와 함께 계량',11,GRAY,anchor='middle')
    for x,label in [(387,'A'),(480,'B')]:
        s.rect(x-8,397,16,27,PALE,BLUE,2);s.text(x,415,label,10,BLUE,True,'middle')
    s.dimh(337,534,510,476,'계량 상판 220')
    s.dimv(243,476,320,337,'260')
    s.text(436,537,'로드셀 + 상·하판 높이 ≤ 40 목표',11,GRAY,anchor='middle')
    s.rect(584,268,124,141,PALE,CYAN,8)
    s.text(646,307,'W02 물통',14,NAVY,True,'middle')
    s.text(646,332,'기성품 약 5 L',11,GRAY,anchor='middle')
    s.text(646,353,'초기 충전 ≤ 3 L 제안',10,GRAY,anchor='middle')
    s.text(646,381,'넘침 트레이·고정',11,CYAN,anchor='middle')
    s.circle(646,484,30,WHITE,CYAN,1.6)
    s.text(646,489,'E04',13,CYAN,True,'middle')
    s.arrow(646,409,646,450,CYAN,2)
    s.poly([(616,484),(562,484),(562,256),(502,256)],None,CYAN,2,closed=False)
    s.arrow(502,256,502,285,CYAN,2)
    s.text(585,537,'펌프 + 튜브 고정',11,CYAN)
    s.line(295,341,315,341,BLUE,1.3,dash=True)
    s.poly([(315,341),(315,220),(496,220),(496,238)],None,BLUE,1.3,True,False)
    s.text(361,216,'별도 지지바 / 선에 여유 루프',10,GRAY)
    s.arrow(365,570,365,550,BLUE)
    s.text(385,573,'정면 / 작업자',11,GRAY)
    s.note(778,198,294,'조립 전에 확보',[
        '평평하고 움직이지 않는 기존 책상',
        '용기·배지·물·상판을 포함한 총질량',
        '전자장치로 흘러가지 않는 낙수 경로',
        '물통·펌프·출수구의 독립된 고정',
        'USB 전원과 12 V 모터 전원 구분'])
    s.note(778,374,294,'설치 원칙',[
        '온습도 A/B는 함체 밖의 동일 통풍 조건',
        '프로브 A/B는 같은 깊이·방향으로 삽입',
        '튜브·전선은 계량 상판을 당기지 않음',
        '물받이도 상판 위에서 함께 계량',
        '노트북은 별도 건식 위치에 배치'])
    s.text(64,652,'오늘의 1차 완료 기준',14,BLUE,True)
    s.lines(64,677,['전압·센서 주소 확인 → 원시값 수집 → 빈 판/기준 질량 검수 → 독립 컵 급수로 공급량 측정'],12,20,NAVY)
    s.finish()


def frame():
    s=Sheet(2,'02-frame.svg','02  3구역 프레임 외형 · 배치','바닥 설치형 800 × 400 × 1200 제안 / 좌측 앞 바닥 원점, x 오른쪽 · y 뒤쪽 · z 위쪽')
    # front, scale .36
    sx,sy,k=91,610,.36
    def box(x,z,w,h,fill=PALE,stroke=BLUE):s.rect(sx+x*k,sy-(z+h)*k,w*k,h*k,fill,stroke)
    s.text(91,154,'정면도  x-z',14,NAVY,True)
    for x in [0,780]:box(x,0,20,1200)
    for z in [0,580,1180]:box(20,z,760,20)
    box(0,600,800,12,BLUE,BLUE)
    for x in [50,290,530]:
        box(x,612,220,40);box(x+20,652,180,200,WHITE)
        s.text(sx+(x+110)*k,sy-742*k,f'Z{1+[50,290,530].index(x)}',13,NAVY,True,'middle')
    for i,x in enumerate([40,300,560]):
        box(x,990,200,150,PALE)
        s.text(sx+(x+100)*k,sy-1065*k,f'BOX {i+1}',10,NAVY,True,'middle')
    box(50,80,250,250,PALE,CYAN)
    s.text(sx+175*k,sy-205*k,'水 / 5 L',11,CYAN,anchor='middle')
    for x in [425,545,665]:s.circle(sx+x*k,sy-200*k,13,WHITE,CYAN)
    s.dimh(sx,sx+800*k,650,610,'800')
    s.dimv(sy-1200*k,sy,69,sx,'1200')
    s.line(sx+800*k,sy-600*k,402,sy-600*k,LINE)
    s.text(407,sy-600*k+4,'z 600',10,GRAY)
    # side
    tx,ty=510,610
    s.text(510,154,'측면도  y-z',14,NAVY,True)
    def side(y,z,w,h,fill=PALE,stroke=BLUE):s.rect(tx+y*k,ty-(z+h)*k,w*k,h*k,fill,stroke)
    for y in [0,380]:side(y,0,20,1200)
    for z in [0,580,1180]:side(20,z,360,20)
    side(0,600,400,12,BLUE)
    side(60,612,260,40);side(100,652,180,200,WHITE)
    side(280,990,100,150,PALE)
    side(80,80,200,250,PALE,CYAN)
    s.line(tx,ty-960*k,tx+360*k,ty-960*k,BLUE,1.2,True)
    s.dimh(tx,tx+400*k,650,610,'400')
    s.text(tx+200*k,ty-940*k,'상단 지지바 높이 실측',9,GRAY,anchor='middle')
    # plan
    px,py,q=740,206,.39
    s.text(740,154,'평면도  x-y',14,NAVY,True)
    s.text(740,176,'재배 선반 높이 z 612 / 위에서 봄',10,GRAY)
    s.rect(px,py,800*q,400*q,WHITE,BLUE,1)
    for i,x in enumerate([50,290,530]):
        s.rect(px+x*q,py+(400-320)*q,220*q,260*q,PALE,BLUE)
        s.rect(px+(x+20)*q,py+(400-280)*q,180*q,180*q,WHITE,BLUE)
        s.text(px+(x+110)*q,py+220*q,f'Z{i+1}',12,NAVY,True,'middle')
    s.dimh(px,px+800*q,397,py+400*q,'50 + 220 + 20 + 220 + 20 + 220 + 50 = 800')
    s.text(px+800*q/2,py-8,'뒤쪽 y=400',10,GRAY,anchor='middle')
    s.table(738,423,[79,119,118],['항목','x 범위','y 범위'],[
        ['Z1 받침','50 - 270','60 - 320'],['Z2 받침','290 - 510','60 - 320'],['Z3 받침','530 - 750','60 - 320']],30,10)
    s.note(737,567,334,'후면 전장함 / 캐리어',[
        '본체: 200 W × 100 D × 150 H (회전 배치)',
        'y 280-380 / z 990-1140',
        'x: 40-240 / 300-500 / 560-760',
        '뚜껑·글랜드·지지판 간섭은 실물 확인'])
    s.text(91,687,'계량 받침 높이가 달라지면 용기 z 좌표를 재계산. 발·캡 돌출, 보강판, 캐리어는 외형 치수에 미포함.',11,GRAY)
    s.finish()


def exploded():
    s=Sheet(3,'03-exploded.svg','03  계량 받침 분해 조립 원리','막대형 로드셀: 한 끝은 베이스에, 반대 끝은 하중 상판에 고정 / PP-A410 실물 고정 방향 확인')
    s.text(50,153,'분해도 / 형상 개념 · 홀 위치 미확정',14,NAVY,True)
    def plate(y,fill=PALE):
        s.poly([(112,y),(388,y),(469,y-45),(193,y-45)],fill,BLUE,1.5)
        s.poly([(112,y),(388,y),(388,y+10),(112,y+10)],WHITE,BLUE,1.2)
        s.poly([(388,y),(469,y-45),(469,y-35),(388,y+10)],WHITE,BLUE,1.2)
    # pot and tray
    s.poly([(205,177),(368,177),(350,250),(222,250)],WHITE,BLUE,1.5)
    s.line(205,177,242,156,BLUE);s.line(242,156,405,156,BLUE);s.line(405,156,368,177,BLUE)
    s.poly([(174,264),(397,264),(428,247),(205,247)],PALE,BLUE,1.2)
    s.line(190,281,455,281,LINE,1,True)
    plate(341)
    # upper spacer and load cell
    s.rect(349,382,35,25,PALE,BLUE)
    s.rect(218,435,175,31,WHITE,BLUE,2)
    s.circle(280,450,8,None,BLUE);s.circle(325,450,8,None,BLUE)
    s.rect(224,493,35,25,PALE,BLUE)
    plate(571)
    for x in [241,367]:s.line(x,362,x,549,LINE,1,True)
    s.arrow(515,290,515,590,BLUE,1.4);s.text(515,621,'하중 전달',11,BLUE,True,'middle')
    for y,n,t in [(213,'1','용기 + 물받이'),(332,'2','상판 220 × 260'),(397,'3','상판측 스페이서'),(454,'4','E06 로드셀'),(510,'5','베이스측 스페이서'),(570,'6','고정 베이스')]:
        s.line(477,y-5,544,y-5,LINE);s.label(568,y,n,t)
    s.dimh(112,388,624,581,'220 (목표 외형)')
    s.text(286,648,'깊이 260 / 완성 높이 ≤ 40 목표',11,GRAY,anchor='middle')
    s.note(752,166,320,'체결 순서',[
        '① 베이스에 로드셀 고정측을 체결',
        '② 반대 끝에 스페이서와 상판을 체결',
        '③ 중앙 변형부와 판 사이 여유 확보',
        '④ 전선에 여유를 두고 베이스에서 고정',
        '⑤ 상판에 물받이·용기를 함께 배치'])
    s.note(752,349,320,'반드시 실측해서 채울 값',[
        '로드셀 길이·폭·높이, 홀 간격·나사산',
        '상·하판 두께와 재료, 스페이서 높이',
        '볼트 길이·체결 토크, 과부하 스토퍼',
        '측하중 억제 구조와 전도 안정성'])
    s.note(752,513,320,'검수: 작은 질량 변화가 보이는가',[
        '빈 판 영점 → 알려진 질량 → 반복 제거',
        '약 10 g 추가 변화와 반복 잡음 비교',
        '선·튜브를 움직여 영점 변화 기록',
        '10 kg 정격은 10 g 식별 보장이 아님'])
    s.text(50,691,'※ 도면의 원·직사각형은 구조 설명용이다. 표시된 나사홀·로드셀 비율을 출력물에서 재어 가공하지 않는다.',11,GRAY)
    s.finish()


def wiring():
    s=Sheet(4,'04-wiring.svg','04  한 구역 신호 배선 · 하네스','클래식 ESP32 DevKit 기준 검토안 / 실제 커넥터 핀 번호·전선 색상·기판 방향은 실물로 확정')
    s.rect(63,193,221,359,PALE,BLUE,7,1.5)
    s.text(173,224,'E01  ESP32',18,NAVY,True,'middle')
    rows=[('I2C SDA / SCL','21 / 22'),('수분 A / B ADC1','32 / 33'),('HX711 DT / SCK','26 / 27'),('펌프 명령','25'),('정지 보조 입력','34'),('누수 보조 입력','35')]
    for i,(name,pin) in enumerate(rows):
        y=270+i*45;s.text(81,y,name,11,GRAY);s.text(264,y,pin,12,BLUE,True,'end')
    s.text(82,534,'3V3 / GND · USB 5V 입력',11,NAVY,True)
    devices=[(160,'E02  SHT31 A / B','0x44 / 0x45 주소를 각각 검수','H01-04',BLUE),(250,'E03  SEN0193 A / B','3V3 · GND · OUT(A=32, B=33)','H05-06',BLUE),(340,'E07  HX711','DT=26 / SCK=27 · 로직 전압 검수','H07-08',BLUE),(430,'E05  DFR0457','25 → 신호 / 외부 OFF 바이어스','H10',BLUE),(520,'정지 · 누수 보조 입력회로','34 / 35 · 외부 바이어스·단선 감지','H11-12',GRAY)]
    for y,title,note,harness,color in devices:
        s.rect(397,y,360,64,WHITE,color,5)
        s.text(414,y+24,title,14,NAVY,True)
        s.text(414,y+47,note,11,GRAY)
        s.text(379,y+24,harness,11,color,True,'end')
    for y0,y1 in [(264,192),(309,282),(354,372),(399,462),(444,545),(489,565)]:
        s.poly([(284,y0),(311+(y0%13),y0),(311+(y0%13),y1),(397,y1)],None,BLUE,1.2,False,False)
    s.rect(813,340,252,64,PALE,BLUE,5)
    s.text(830,365,'E06  4선식 로드셀',13,NAVY,True)
    s.text(830,388,'E+ / E- / A+ / A-',12,GRAY)
    s.line(757,372,813,372,BLUE,1.4);s.text(785,333,'H09',10,BLUE,True,'middle')
    s.note(810,152,260,'3.3 V 신호 기준',[
        'GPIO에 5 V 출력 직결 금지',
        'SHT31 풀업도 3.3 V 기준 확인',
        'GPIO34/35 내부 풀업 없음',
        '3핀 센서/12 V 커넥터 혼용 금지'])
    s.note(810,438,260,'모터 제어 전',[
        'H10은 제어 신호 경로',
        '3핀의 전원/GND/신호는 제조사 확인',
        '12 V 전력선은 05 도면 참조',
        '부팅·업로드 중 물리 모터 전원 차단'])
    s.rect(63,586,694,43,PALE,None,5)
    s.text(78,613,'H13  USB 5V 어댑터 → ESP32 USB-C / 센서 3V3 전원 용량·모듈 호환성 확인',11,NAVY)
    s.lines(63,660,['H01/H03: 3V3·GND → SHT31 A/B    H02/H04: GPIO21/22 → SDA/SCL',
                       'H07: 검수된 로직 전원·GND → HX711    H09: 로드셀 선 색상은 판매 자료 우선',
                       '하네스 양 끝에 Z1-H01 형식으로 표시. Z2/Z3도 같은 규칙으로 식별한다.'],11,19,GRAY)
    s.finish()


def power_water():
    s=Sheet(5,'05-water-power.svg','05  펌프 전력 경로 · 독립 물길','논리 연결도 / 실제 DFR0457 전력·제어 단자의 위치는 제조사 핀아웃과 수령품으로 확인')
    s.text(48,150,'12 V 저전압 전력 경로',15,NAVY,True)
    blocks=[(48,180,143,'P01  12V 어댑터','완제품 · (+)'),(222,180,132,'주 퓨즈','정격 미확정'),(385,180,170,'물리 DC 차단 경로','스위치/접촉기 검토'),(586,180,143,'분배 단자대','정격·선경 검수')]
    for x,y,w,title,sub in blocks:
        s.rect(x,y,w,63,PALE,BLUE,4)
        s.text(x+w/2,y+25,title,12,NAVY,True,'middle');s.text(x+w/2,y+47,sub,10,GRAY,anchor='middle')
    for x1,x2 in [(191,222),(354,385),(555,586)]:s.arrow(x1,211,x2,211,BLUE,2)
    s.line(657,243,657,417,BLUE,2)
    for i,y in enumerate([273,333,393]):
        s.line(657,y+24,704,y+24,BLUE,2)
        s.rect(704,y,104,47,WHITE,BLUE,3)
        s.text(756,y+20,f'Z{i+1} 분기 퓨즈',11,NAVY,True,'middle');s.text(756,y+36,'정격 미확정',9,GRAY,anchor='middle')
        s.arrow(808,y+24,832,y+24,BLUE,2)
        s.rect(832,y,109,47,PALE,BLUE,3)
        s.text(886,y+28,'DFR0457',12,NAVY,True,'middle')
        s.arrow(941,y+24,966,y+24,BLUE,2)
        s.circle(993,y+24,23,WHITE,BLUE,1.5);s.text(993,y+28,f'M{i+1}',12,NAVY,True,'middle')
    s.note(48,278,540,'실제 단자·보호 구성 확인',[
        '어댑터 (-) → 검수된 공통 귀환점 → 각 모듈의 지정된 GND',
        'ESP32 신호 GND → DFR0457 제조사 지침의 기준 접지',
        '각 펌프 양단에 정격 검토된 역기전력 억제 회로',
        '보호소자 극성·전류·열·DC 차단 능력은 실물 부하 기준 선정',
        '1N4007은 구매 후보. 모든 펌프/PWM에 적합한 것으로 확정하지 않음'])
    s.line(48,459,1072,459,LINE)
    s.text(48,487,'물통은 공용 / 펌프 이후 물길은 세 갈래 독립',15,CYAN,True)
    s.rect(61,525,165,114,PALE,CYAN,7)
    s.text(143,560,'뚜껑 있는 물통',14,NAVY,True,'middle')
    s.text(143,585,'5 L 기성품',12,GRAY,anchor='middle')
    s.text(143,611,'초기 충전 ≤ 3 L 제안',10,GRAY,anchor='middle')
    for i,y in enumerate([529,581,633]):
        s.poly([(226,560+i*18),(270+i*14,560+i*18),(270+i*14,y),(343,y)],None,CYAN,1.7,closed=False)
        s.rect(343,y-18,133,37,WHITE,CYAN,4)
        s.text(409,y+5,f'펌프 {i+1}',12,NAVY,True,'middle')
        s.arrow(476,y,543,y,CYAN,2)
        s.rect(543,y-18,199,37,WHITE,CYAN,4)
        s.text(642,y+5,f'고정 출수구 {i+1}',12,NAVY,True,'middle')
        s.arrow(742,y,813,y,CYAN,2)
        s.rect(813,y-18,243,37,PALE,CYAN,4)
        s.text(934,y+5,f'Z{i+1} 용기 + 물받이 / 계량',12,NAVY,True,'middle')
    s.text(61,680,'튜브 W01: 내경 2.5 / 외경 4.5 mm 후보. 펌프 헤드 튜브와 호환·밀폐 여부 확인 후 사용.',11,GRAY)
    s.text(61,699,'출수구·튜브는 프레임에서 지지. 배수·누수·호스 힘이 질량 변화에 섞이는 구간은 별도 기록.',11,GRAY)
    s.finish()


def assembly():
    s=Sheet(6,'06-assembly.svg','06  1구역 조립 순서 · 부품 묶음','1구역을 검수한 다음 동일 모델로 3구역 복제 / 부품 ID는 원문 19장 구매표와 연결')
    s.table(48,149,[48,208,363,405],['순서','조립 작업','사용 부품 / 필요한 도구','다음 단계로 넘어갈 기준'],[
        ['01','책상·고정·낙수 경로','기존 책상, 고정 지그, 물받이 / 줄자·수평계','전장·물 구획 분리, 물통·용기 전도 방지'],
        ['02','센서 회로 무수 연결','E01 + E02×2 + E03×2 / 멀티미터·USB','3.3 V 범위, 주소 0x44/45, 원시 ADC 확인'],
        ['03','동일 조건 센서 비교','A/B 센서 지그 / 온습도·원시값 로그','센서 ID·편차·시간축·누락 여부 기록'],
        ['04','계량 받침 조립·검수','E06 + E07 + 판/스페이서 / 기준 질량','영점·반복성·호스 힘 영향 / 약 10 g 식별'],
        ['05','독립 컵 펌프 시험','E04 + E05 + P01/P04/P06/P07 / 독립 저울','정격 검토 완료 후 물리 차단·부팅 OFF 확인'],
        ['06','펌프 공급량 보정','W01/W02 + 펌프 / 타이머·독립 저울','운전시간 ≥3종, 각 ≥2회부터 질량 기록'],
        ['07','배지·프로브 설치','W03 + W04 + A/B 프로브 / 깊이 기준자','배지·다짐·깊이·방향 고정, 반응 지연 기록'],
        ['08','3구역 복제·마감','노드 2세트 추가 + C07×3 + 선택 프레임','구역 ID, 한 구역 작동의 타 계량 영향 검수'],
    ],45,11)
    s.text(48,568,'1구역 우선 준비 수량',14,BLUE,True)
    s.note(48,586,326,'센서 · 제어 · 계량',[
        'E01 ESP32 ×1 / E02 SHT31 ×2',
        'E03 SEN0193 ×2 / E06 로드셀 ×1',
        'E07 HX711 ×1 / 상·하판 각1'])
    s.note(398,586,326,'급수 · 전원',[
        'E04 펌프 ×1 / E05 DFR0457 ×1',
        'P01 12 V · P02 USB 전원 각1',
        '차단·퓨즈·전력선은 정격 확정 후'])
    s.note(748,586,324,'고정 · 시험',[
        '물통·화분·물받이 각1 / 튜브',
        '멀티미터·독립 저울·기준 질량',
        '드라이버·고정구·라벨·절연 마감'])
    s.finish()


def verification():
    s=Sheet(7,'07-verification.svg','07  미확정 치수 · 제작 전 검수표','기계 revision M1 / 보드 revision B0 / 하네스 revision H1 / 실측칸을 채운 뒤 도면과 BOM을 함께 갱신')
    s.table(48,148,[189,341,354,140],['확정할 항목','현재 기준 / 아직 남은 일','실측값 · 검수 결과','담당 / 날짜'],[
        ['로드셀 지그','220×260 외형 / 홀·나사·판두께·여유 미정','',''],
        ['계량 성능','총 하중, 영점·반복성·크리프·10 g 변화','',''],
        ['프로파일 결합','2020 맞댐 가정 / 홈·브래킷·T너트 모델','',''],
        ['구조 안정성','후면 보강, 발 고정, 총 적재질량 검토','',''],
        ['전장함 캐리어','760×250 제안 / 판두께·홀·글랜드·개폐','',''],
        ['펌프·튜브','고정홀, 헤드/연장 튜브 적합성, 누수','',''],
        ['DC 전력 보호','기동/연속/구속 전류, 전선·차단·퓨즈 정격','',''],
        ['보드·센서 회로','실크·핀배열·I2C 주소·출력 HIGH 전압','',''],
        ['정지·누수 입력','접점/단선 회로, 부팅 OFF·재시작 잠금','',''],
    ],40,11)
    s.note(48,565,494,'실제 급수 연동 전에 남길 증거',[
        '모터 전력 물리 차단 사진과 회로 검토 기록',
        '전원복구·업로드·통신두절·계량이상에서 신규 펄스 차단',
        '펌프 보정 CSV, 기준 질량 로그, 지그 실측 치수표',
        '원문 제안 한도(10 mL/회 등)는 책임자가 실물 검수 후 결정'])
    s.note(566,565,506,'근거와 도면 사용 범위',[
        '사용자 제공 MASTER v4의 18-21 / 29장 기반',
        'DFRobot DFR0457: wiki.dfrobot.com/dfr0457/',
        'Espressif 공식 ESP32 GPIO 문서 (2026-10-01 조회)',
        '완료되지 않은 가공·전기·실물 시험을 완료로 표시하지 않음'])
    s.finish()


def cutlist():
    s=Sheet(8,'08-cutlist.svg','08  프레임 절단안 · 선반 판 상세','2020 기둥 사이에 가로재를 끼우는 맞댐 구조 가정 / 제품·체결 방식이 바뀌면 절단 길이 재계산')
    s.table(48,148,[189,67,130,130,508],['부재','수량','길이 / 1개','총 길이','위치 / 계산 근거'],[
        ['수직 기둥','4','1200','4800','외형 높이 1200 / 가로재 높이를 다시 더하지 않음'],
        ['폭 방향 가로재','6','760','4560','800 - 20 - 20 / 하부·선반·상부 링 각2'],
        ['깊이 방향 가로재','6','360','2160','400 - 20 - 20 / 하부·선반·상부 링 각2'],
        ['선반 보강 깊이재','2','360','720','받침 사이 위치 조정 / 체결 간섭 검토'],
        ['합계','18','-','12,240','12.24 m / 절단 손실·여분·추가 캐리어 제외'],
    ],37,11)
    s.text(48,413,'선반 판 평면 상세 / 절개 제안',15,NAVY,True)
    x,y,k=80,460,.49
    # notched outline, 800 x 400 with 22 x 22 corners
    p=[(22,0),(778,0),(778,22),(800,22),(800,378),(778,378),(778,400),(22,400),(22,378),(0,378),(0,22),(22,22)]
    s.poly([(x+a*k,y+b*k) for a,b in p],PALE,BLUE,1.5)
    for xx in [280,520]:s.line(x+xx*k,y+20*k,x+xx*k,y+380*k,BLUE,1.2,True)
    s.dimh(x,x+800*k,y+228,y+400*k,'800')
    s.dimv(y,y+400*k,58,x,'400')
    s.text(x+196,y+96,'판 두께 12 제안',14,NAVY,True,'middle')
    s.text(x+196,y+120,'4모서리 22 × 22 절개 제안',11,GRAY,anchor='middle')
    s.text(x+196,y+144,'기둥·브래킷 실물 간섭 확인 후 확정',11,GRAY,anchor='middle')
    s.note(566,409,506,'설치 높이 기준',[
        '하부 링 z 0-20 / 선반 링 z 580-600',
        '상부 링 z 1180-1200',
        '선반 판 윗면 z 612 (판 두께 12 적용 시)',
        '계량 받침 높이 40이면 용기 바닥 z 652'])
    s.note(566,573,506,'절단 발주 전 확인',[
        '프로파일 단면·브래킷·T너트·볼트 규격을 한 세트로 선정',
        '후면 대각 또는 판 보강과 발 고정 검토',
        '별도 제안: 전장함 캐리어 약 760×250 / 두께 미정',
        '프레임 견적·하중 검토 전에는 기존 책상 파일럿부터 진행'])
    s.finish()


for draw in [pilot,frame,exploded,wiring,power_water,assembly,verification,cutlist]:
    draw()
c.save()
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Created {PDF} and {len(manifest)} editable SVG sheets')
