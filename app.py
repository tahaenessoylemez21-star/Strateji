from flask import Flask,render_template_string
from flask_socketio import SocketIO,emit,join_room
import random,threading,time

app=Flask(__name__)
app.config['SECRET_KEY']='strateji2024'
socketio=SocketIO(app,cors_allowed_origins="*")
oyunlar={}

def harita_olustur(boyut=8):
    harita=[[{'sahip':None,'guc':0,'engel':False}for j in range(boyut)]for i in range(boyut)]
    engel_sayisi=0
    while engel_sayisi<6:
        i,j=random.randint(1,6),random.randint(1,6)
        if not harita[i][j]['engel']:
            harita[i][j]['engel']=True
            engel_sayisi+=1
    return harita

def bot_hamle_yap(oda_id):
    time.sleep(1)
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    if not oyun['basladi']:return
    aktif=oyun['oyuncular'][oyun['aktif']]
    if aktif!='Bot':return
    harita=oyun['harita']
    secenekler=[]
    for i in range(8):
        for j in range(8):
            if harita[i][j]['sahip']=='Bot' and harita[i][j]['guc']>1:
                for di,dj in[(-1,0),(1,0),(0,-1),(0,1)]:
                    ni,nj=i+di,j+dj
                    if 0<=ni<8 and 0<=nj<8 and not harita[ni][nj]['engel']:
                        secenekler.append((i,j,ni,nj))
    if not secenekler:
        tur_gec(oda_id)
        return
    ki,kj,hi,hj=random.choice(secenekler)
    hamle_islemi(oda_id,'Bot',ki,kj,hi,hj)

def hamle_islemi(oda_id,oyuncu,ki,kj,hi,hj):
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    kaynak=oyun['harita'][ki][kj]
    hedef=oyun['harita'][hi][hj]
    if kaynak['sahip']!=oyuncu or kaynak['guc']<2:
        tur_gec(oda_id)
        return
    guc=kaynak['guc']-1
    kaynak['guc']=1
    if hedef['sahip']==oyuncu:
        hedef['guc']+=guc
    elif hedef['sahip'] is None:
        hedef['sahip']=oyuncu
        hedef['guc']=guc
    else:
        if guc>hedef['guc']:
            hedef['sahip']=oyuncu
            hedef['guc']=guc-hedef['guc']
        elif guc==hedef['guc']:
            hedef['sahip']=None
            hedef['guc']=0
        else:
            hedef['guc']-=guc
    tur_gec(oda_id)

def tur_gec(oda_id):
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    oyun['aktif']=(oyun['aktif']+1)%len(oyun['oyuncular'])
    oyun['tur']+=1
    aktif=oyun['oyuncular'][oyun['aktif']]
    sayim=skor_hesapla(oyun['harita'])
    toplam=sum(sayim.values())
    if toplam>0:
        for o,s in sayim.items():
            if s==toplam:
                socketio.emit('oyun_bitti',{'kazanan':o,'sayim':sayim},room=oda_id)
                return
    socketio.emit('guncelle',{
        'harita':oyun['harita'],
        'aktif':aktif,
        'tur':oyun['tur'],
        'sayim':sayim,
        'sure':oyun['sure']
    },room=oda_id)
    if aktif=='Bot':
        t=threading.Thread(target=bot_hamle_yap,args=(oda_id,))
        t.daemon=True
        t.start()

def skor_hesapla(harita):
    sayim={}
    for satir in harita:
        for h in satir:
            if h['sahip']:
                sayim[h['sahip']]=sayim.get(h['sahip'],0)+1
    return sayim

def sure_say(oda_id):
    while oda_id in oyunlar and oyunlar[oda_id]['basladi'] and oyunlar[oda_id]['sure']>0:
        time.sleep(1)
        if oda_id not in oyunlar:return
        oyunlar[oda_id]['sure']-=1
        socketio.emit('sure',{'sure':oyunlar[oda_id]['sure']},room=oda_id)
        if oyunlar[oda_id]['sure']==0:
            sayim=skor_hesapla(oyunlar[oda_id]['harita'])
            kazanan=max(sayim,key=sayim.get) if sayim else 'Berabere'
            socketio.emit('oyun_bitti',{'kazanan':kazanan,'sayim':sayim,'sure_bitti':True},room=oda_id)

HTML="""<!DOCTYPE html>
<html>
<head>
<title>Strateji</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#fff;font-family:'Rajdhani',sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:10px}
h1{font-family:'Orbitron',sans-serif;color:#e94560;font-size:22px;letter-spacing:3px;text-shadow:0 0 15px #e9456066}
.sub{color:#555;font-size:12px;letter-spacing:2px;margin-bottom:15px}
.card{background:#111827;border:1px solid #e9456022;border-radius:14px;padding:20px;width:100%;max-width:380px}
input,select{width:100%;padding:11px;margin:6px 0;border-radius:8px;border:1px solid #333;background:#0a0a1a;color:#fff;font-size:15px;font-family:'Rajdhani',sans-serif;outline:none}
input:focus,select:focus{border-color:#e94560}
.btn{width:100%;padding:12px;margin-top:8px;border-radius:8px;border:none;font-size:15px;font-family:'Orbitron',sans-serif;cursor:pointer;letter-spacing:1px}
.btn-red{background:linear-gradient(135deg,#e94560,#c73652);color:#fff}
.btn-green{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn:disabled{opacity:0.3;cursor:not-allowed}
#sure{font-family:'Orbitron',sans-serif;font-size:28px;color:#e94560;margin:5px 0}
#bilgi{font-size:14px;color:#ffd700;margin:4px 0;text-align:center;min-height:20px}
#tur{font-size:12px;color:#666;margin:2px 0;text-align:center}
.skorlar{display:flex;gap:8px;justify-content:center;margin:6px 0;flex-wrap:wrap}
.skor{padding:4px 10px;border-radius:6px;font-size:13px;border:1px solid #333}
.grid{display:grid;grid-template-columns:repeat(8,38px);gap:3px;background:#0a0a1a;padding:8px;border-radius:10px;margin:8px 0;border:1px solid #1a1a2e}
.cell{width:38px;height:38px;border-radius:5px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold;border:1px solid #ffffff0a;transition:transform 0.1s;background:#111827}
.cell:active{transform:scale(0.9)}
.cell.mine{border:2px solid #ffd700}
.cell.engel{background:#1a1a1a;cursor:default;font-size:18px}
.sohbet{width:100%;max-width:380px;margin-top:8px}
.mesajlar{background:#111827;border-radius:8px;padding:8px;height:70px;overflow-y:auto;font-size:12px;margin-bottom:4px;border:1px solid #1e293b}
.mesaj-gir{display:flex;gap:4px}
.mesaj-gir input{margin:0;padding:8px;font-size:13px}
.mesaj-gir button{width:70px;padding:8px;margin:0;background:#e94560;border:none;border-radius:8px;color:#fff;font-size:12px;cursor:pointer}
.bitis{text-align:center}
.kazanan{font-family:'Orbitron',sans-serif;font-size:22px;color:#ffd700;margin:10px 0}
.oda-kod{font-family:'Orbitron',sans-serif;font-size:24px;color:#ffd700;letter-spacing:4px;text-align:center;margin:8px 0;padding:10px;background:#0a0a1a;border-radius:8px}
.oyuncu-list{font-size:14px;line-height:1.8;margin:8px 0}
</style>
</head>
<body>
<h1>⚔️ STRATEJİ</h1>
<p class="sub">ORDU SAVAŞLARI</p>

<div id="ekran-giris" class="card">
  <input id="isim" placeholder="👤 Adın"/>
  <select id="mod">
    <option value="bot">🤖 Bota karşı oyna</option>
    <option value="2">👥 2 Kişilik Online</option>
    <option value="4">👥👥 4 Kişilik Online</option>
  </select>
  <input id="oda-gir" placeholder="🔑 Oda kodu (boş = yeni oda)"/>
  <button class="btn btn-red" onclick="giris()">OYUNA GİR</button>
</div>

<div id="ekran-bekle" class="card" style="display:none">
  <div class="oda-kod" id="oda-goster"></div>
  <div id="bekle-acik" style="color:#888;font-size:12px;text-align:center"></div>
  <div class="oyuncu-list" id="oyuncu-list"></div>
  <button class="btn btn-green" id="btn-baslat" onclick="baslat()" style="display:none" disabled>▶ OYUNU BAŞLAT</button>
</div>

<div id="ekran-oyun" style="display:none;flex-direction:column;align-items:center;width:100%;max-width:400px">
  <div id="sure">5:00</div>
  <div id="bilgi"></div>
  <div id="tur"></div>
  <div class="skorlar" id="skorlar"></div>
  <div class="grid" id="grid"></div>
  <div class="sohbet">
    <div class="mesajlar" id="mesajlar"></div>
    <div class="mesaj-gir">
      <input id="msg" placeholder="Mesaj..." onkeypress="if(event.key==='Enter')mesaj()"/>
      <button onclick="mesaj()">Gönder</button>
    </div>
  </div>
</div>

<div id="ekran-bitis" class="card bitis" style="display:none">
  <div class="kazanan" id="kazanan"></div>
  <div id="final-skor" style="margin:10px 0"></div>
  <button class="btn btn-red" onclick="location.reload()">🔄 YENİDEN OYNA</button>
</div>

<script>
const io_socket=io();
let ben='',oda='',siram=false,kaptan=false,mod='bot';
const renkler=['#e94560','#22c55e','#ffd700','#a855f7'];
const oyuncuRenk={};
let oyuncular=[];

function giris(){
  ben=document.getElementById('isim').value.trim();
  mod=document.getElementById('mod').value;
  const kod=document.getElementById('oda-gir').value.trim();
  if(!ben)return alert('İsim gir!');
  if(kod)io_socket.emit('katil',{isim:ben,oda:kod});
  else io_socket.emit('yeni_oda',{isim:ben,mod:mod});
}

function baslat(){
  io_socket.emit('baslat',{oda:oda});
}

function mesaj(){
  const m=document.getElementById('msg').value.trim();
  if(!m)return;
  io_socket.emit('mesaj',{oda:oda,isim:ben,m:m});
  document.getElementById('msg').value='';
}

io_socket.on('oda_tamam',d=>{
  oda=d.oda;kaptan=true;
  goster('ekran-bekle');
  document.getElementById('oda-goster').textContent=d.oda;
  if(d.mod==='bot'){
    document.getElementById('bekle-acik').textContent='Bot ile oynuyorsun!';
    document.getElementById('btn-baslat').style.display='block';
    document.getElementById('btn-baslat').disabled=false;
  }else{
    document.getElementById('bekle-acik').textContent='Arkadaşına bu kodu gönder!';
  }
  oyuncuGuncelle(d.oyuncular,d.max);
});

io_socket.on('katildi',d=>{
  oda=d.oda;
  goster('ekran-bekle');
  document.getElementById('oda-goster').textContent=d.oda;
  document.getElementById('bekle-acik').textContent='Odaya katıldın!';
  oyuncuGuncelle(d.oyuncular,d.max);
});

io_socket.on('oyuncu_geldi',d=>{
  oyuncuGuncelle(d.oyuncular,d.max);
  if(kaptan&&d.oyuncular.length>=2){
    document.getElementById('btn-baslat').style.display='block';
    document.getElementById('btn-baslat').disabled=false;
  }
});

function oyuncuGuncelle(liste,max){
  oyuncular=liste;
  liste.forEach((o,i)=>oyuncuRenk[o]=renkler[i]);
  document.getElementById('oyuncu-list').innerHTML='<b style="color:#e94560">Oyuncular ('+liste.length+'/'+max+'):</b><br>'+
  liste.map((o,i)=>'<span style="color:'+renkler[i]+'">● '+o+'</span>').join('  ');
}

io_socket.on('oyun_basladi',d=>{
  oyuncular=d.oyuncular;
  oyuncular.forEach((o,i)=>oyuncuRenk[o]=renkler[i]);
  goster('ekran-oyun');
  guncelle(d);
});

io_socket.on('guncelle',d=>guncelle(d));

io_socket.on('sure',d=>{
  const dk=Math.floor(d.sure/60),sn=d.sure%60;
  document.getElementById('sure').textContent=dk+':'+(sn<10?'0':'')+sn;
  document.getElementById('sure').style.color=d.sure<=30?'#ff4444':'#e94560';
});

io_socket.on('mesaj_geldi',d=>{
  const div=document.getElementById('mesajlar');
  const p=document.createElement('p');
  p.style.color=oyuncuRenk[d.isim]||'#aaa';
  p.textContent=d.isim+': '+d.m;
  div.appendChild(p);
  div.scrollTop=div.scrollHeight;
});

io_socket.on('oyun_bitti',d=>{
  goster('ekran-bitis');
  document.getElementById('kazanan').textContent=(d.sure_bitti?'⏱️ SÜRE BİTTİ!\n':'')+'🏆 '+d.kazanan+' KAZANDI!';
  document.getElementById('final-skor').innerHTML=Object.entries(d.sayim).map(([o,s])=>
  '<div style="color:'+(oyuncuRenk[o]||'#fff')+';margin:3px">'+o+': '+s+' kare</div>').join('');
});

io_socket.on('hata',d=>alert(d.m));

function guncelle(d){
  siram=(d.aktif===ben);
  document.getElementById('bilgi').textContent=siram?'⚡ Senin sıran! Kareye dokun!':'⏳ '+d.aktif+' oynuyor...';
  document.getElementById('tur').textContent='Tur '+d.tur;
  skorGoster(d.sayim);
  gridCiz(d.harita);
}

function skorGoster(sayim){
  if(!sayim)return;
  document.getElementById('skorlar').innerHTML=oyuncular.map(o=>
  '<div class="skor" style="border-color:'+(oyuncuRenk[o]||'#fff')+'66;color:'+(oyuncuRenk[o]||'#fff')+'">'+o+' '+(sayim[o]||0)+'</div>').join('');
}

function gridCiz(harita){
  window._h=harita;
  const g=document.getElementById('grid');g.innerHTML='';
  harita.forEach((satir,i)=>satir.forEach((h,j)=>{
    const c=document.createElement('div');
    c.className='cell';
    if(h.engel){c.classList.add('engel');c.textContent='⛰️';g.appendChild(c);return;}
    const renk=h.sahip?oyuncuRenk[h.sahip]||'#555':'#111827';
    c.style.background=renk;
    if(h.sahip===ben)c.classList.add('mine');
    if(h.guc>0)c.textContent=h.guc;
    c.onclick=()=>tikla(i,j);
    g.appendChild(c);
  }));
}

function tikla(i,j){
  if(!siram||!window._h)return;
  const h=window._h[i][j];
  if(h.engel)return;
  if(h.sahip!==ben||h.guc<2){
    document.getElementById('bilgi').textContent='⚠️ Kendi güçlü kareni seç! (Güç 2+)';
    return;
  }
  const komsular=[{di:-1,dj:0},{di:1,dj:0},{di:0,dj:-1},{di:0,dj:1}];
  const hedefler=komsular.map(k=>({ni:i+k.di,nj:j+k.dj}))
    .filter(({ni,nj})=>ni>=0&&ni<8&&nj>=0&&nj<8&&!window._h[ni][nj].engel);
  if(hedefler.length===0)return;
  if(hedefler.length===1){
    io_socket.emit('hamle',{oda:oda,oyuncu:ben,ki:i,kj:j,hi:hedefler[0].ni,hj:hedefler[0].nj});
    siram=false;
    document.getElementById('bilgi').textContent='⏳ Hamle yapıldı...';
    return;
  }
  document.getElementById('bilgi').textContent='👆 Hedef kareyi seç!';
  window._kaynak={i,j};
  gridCizSecim(window._h,i,j,hedefler);
}

function gridCizSecim(harita,ki,kj,hedefler){
  const g=document.getElementById('grid');g.innerHTML='';
  harita.forEach((satir,i)=>satir.forEach((h,j)=>{
    const c=document.createElement('div');
    c.className='cell';
    if(h.engel){c.classList.add('engel');c.textContent='⛰️';g.appendChild(c);return;}
    const renk=h.sahip?oyuncuRenk[h.sahip]||'#555':'#111827';
    c.style.background=renk;
    if(i===ki&&j===kj){c.style.border='2px solid #ffd700';c.style.boxShadow='0 0 8px #ffd700';}
    const hedef=hedefler.find(x=>x.ni===i&&x.nj===j);
    if(hedef){c.style.border='2px solid #ff4444';c.style.boxShadow='0 0 8px #ff4444';
      c.onclick=()=>{
        io_socket.emit('hamle',{oda:oda,oyuncu:ben,ki:ki,kj:kj,hi:i,hj:j});
        siram=false;
        document.getElementById('bilgi').textContent='⏳ Hamle yapıldı...';
      };
    }else{
      if(h.guc>0)c.textContent=h.guc;
      c.onclick=()=>{gridCiz(harita);document.getElementById('bilgi').textContent='⚡ Senin sıran! Kareye dokun!';};
    }
    if(h.guc>0&&!hedef)c.textContent=h.guc;
    g.appendChild(c);
  }));
}

function goster(id){
  ['ekran-giris','ekran-bekle','ekran-oyun','ekran-bitis'].forEach(x=>{
    const el=document.getElementById(x);
    el.style.display=x===id?(id==='ekran-oyun'?'flex':'block'):'none';
  });
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('yeni_oda')
def yeni_oda(data):
    oda=('P'+str(random.randint(1000,9999)))
    mod=data.get('mod','2')
    max_o=4 if mod=='4' else 2
    oyunlar[oda]={'oyuncular':[],'harita':harita_olustur(),'tur':1,'aktif':0,'sure':300,'basladi':False,'mod':mod,'max':max_o}
    join_room(oda)
    oyunlar[oda]['oyuncular'].append(data['isim'])
    emit('oda_tamam',{'oda':oda,'oyuncular':oyunlar[oda]['oyuncular'],'max':max_o,'mod':mod})

@socketio.on('katil')
def katil(data):
    oda=data['oda']
    if oda not in oyunlar:emit('hata',{'m':'Oda bulunamadı!'});return
    o=oyunlar[oda]
    if len(o['oyuncular'])>=o['max']:emit('hata',{'m':'Oda dolu!'});return
    join_room(oda)
    o['oyuncular'].append(data['isim'])
    emit('katildi',{'oda':oda,'oyuncular':o['oyuncular'],'max':o['max']})
    socketio.emit('oyuncu_geldi',{'oyuncular':o['oyuncular'],'max':o['max']},room=oda)

@socketio.on('baslat')
def baslat(data):
    oda=data['oda']
    if oda not in oyunlar:return
    o=oyunlar[oda]
    if o['mod']=='bot' and 'Bot' not in o['oyuncular']:
        o['oyuncular'].append('Bot')
    o['basladi']=True
    bas=[(0,0),(7,7),(0,7),(7,0)]
    for idx,oyuncu in enumerate(o['oyuncular']):
        x,y=bas[idx]
        o['harita'][x][y]['sahip']=oyuncu
        o['harita'][x][y]['guc']=5
    aktif=o['oyuncular'][0]
    sayim=skor_hesapla(o['harita'])
    socketio.emit('oyun_basladi',{'harita':o['harita'],'oyuncular':o['oyuncular'],'aktif':aktif,'tur':1,'sayim':sayim},room=oda)
    threading.Thread(target=sure_say,args=(oda,),daemon=True).start()
    if aktif=='Bot':
        threading.Thread(target=bot_hamle_yap,args=(oda,),daemon=True).start()

@socketio.on('hamle')
def hamle(data):
    oda=data['oda']
    if oda not in oyunlar:return
    o=oyunlar[oda]
    if o['oyuncular'][o['aktif']]!=data['oyuncu']:return
    hamle_islemi(oda,data['oyuncu'],data['ki'],data['kj'],data['hi'],data['hj'])

@socketio.on('mesaj')
def mesaj(data):
    socketio.emit('mesaj_geldi',{'isim':data['isim'],'m':data['m']},room=data['oda'])

if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5000,debug=True)
