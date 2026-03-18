from flask import Flask,render_template_string
from flask_socketio import SocketIO,emit,join_room
import random,threading,time

app=Flask(__name__)
app.config['SECRET_KEY']='strateji2024'
socketio=SocketIO(app,cors_allowed_origins="*")
oyunlar={}

def harita_olustur(boyut=8):
    harita=[[{'sahip':None,'guc':0,'engel':False,'x':i,'y':j}for j in range(boyut)]for i in range(boyut)]
    for _ in range(8):
        i,j=random.randint(1,6),random.randint(1,6)
        harita[i][j]['engel']=True
    return harita

def bot_hamle(oda_id):
    time.sleep(1.5)
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    if not oyun['basladi']:return
    if oyun['oyuncular'][oyun['aktif']]!='🤖 Bot':return
    harita=oyun['harita']
    bot_kareler=[(i,j)for i in range(8)for j in range(8)if harita[i][j]['sahip']=='🤖 Bot'and harita[i][j]['guc']>1]
    if not bot_kareler:sonraki_tur(oda_id);return
    ki,kj=random.choice(bot_kareler)
    komsular=[(ki-1,kj),(ki+1,kj),(ki,kj-1),(ki,kj+1)]
    gecerli=[(hi,hj)for hi,hj in komsular if 0<=hi<8 and 0<=hj<8 and not harita[hi][hj]['engel']]
    if not gecerli:sonraki_tur(oda_id);return
    hi,hj=random.choice(gecerli)
    _hamle_yap_logic(oda_id,'🤖 Bot',ki,kj,hi,hj)

def _hamle_yap_logic(oda_id,oyuncu,kx,ky,hx,hy):
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    kaynak=oyun['harita'][kx][ky]
    hedef=oyun['harita'][hx][hy]
    if kaynak['sahip']!=oyuncu or kaynak['guc']<2:sonraki_tur(oda_id);return
    gonderilen=kaynak['guc']-1
    kaynak['guc']=1
    if hedef['sahip']==oyuncu:hedef['guc']+=gonderilen
    elif hedef['sahip']is None:hedef['sahip']=oyuncu;hedef['guc']=gonderilen
    else:
        if gonderilen>hedef['guc']:hedef['sahip']=oyuncu;hedef['guc']=gonderilen-hedef['guc']
        elif gonderilen==hedef['guc']:hedef['sahip']=None;hedef['guc']=0
        else:hedef['guc']-=gonderilen
    sonraki_tur(oda_id)

def sonraki_tur(oda_id):
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    oyun['aktif']=(oyun['aktif']+1)%len(oyun['oyuncular'])
    oyun['tur']+=1
    aktif=oyun['oyuncular'][oyun['aktif']]
    sayimlar={}
    for s in oyun['harita']:
        for h in s:
            if h['sahip']:sayimlar[h['sahip']]=sayimlar.get(h['sahip'],0)+1
    toplam=sum(sayimlar.values())
    kazanan=None
    for o,s in sayimlar.items():
        if s==toplam and toplam>0:kazanan=o
    if kazanan:
        socketio.emit('oyun_bitti',{'kazanan':kazanan,'istatistik':sayimlar},room=oda_id)
        return
    socketio.emit('hamle_sonucu',{'harita':oyun['harita'],'aktif_oyuncu':aktif,'tur':oyun['tur']},room=oda_id)
    if aktif=='🤖 Bot':
        t=threading.Thread(target=bot_hamle,args=(oda_id,))
        t.daemon=True
        t.start()

def sure_sayaci(oda_id):
    while oda_id in oyunlar and oyunlar[oda_id]['sure']>0 and oyunlar[oda_id]['basladi']:
        time.sleep(1)
        if oda_id not in oyunlar:return
        oyunlar[oda_id]['sure']-=1
        socketio.emit('sure_guncelle',{'sure':oyunlar[oda_id]['sure']},room=oda_id)
        if oyunlar[oda_id]['sure']==0:
            harita=oyunlar[oda_id]['harita']
            sayimlar={}
            for s in harita:
                for h in s:
                    if h['sahip']:sayimlar[h['sahip']]=sayimlar.get(h['sahip'],0)+1
            kazanan=max(sayimlar,key=sayimlar.get)if sayimlar else'Berabere'
            socketio.emit('oyun_bitti',{'kazanan':kazanan,'istatistik':sayimlar,'sure_bitti':True},room=oda_id)

HTML="""<!DOCTYPE html>
<html>
<head>
<title>⚔️ Strateji</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:white;font-family:'Rajdhani',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:15px}
h1{font-family:'Orbitron',sans-serif;font-size:24px;color:#e94560;text-shadow:0 0 20px #e9456088;margin-bottom:5px;letter-spacing:3px}
.subtitle{color:#888;font-size:13px;margin-bottom:20px;letter-spacing:2px}
.card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #e9456033;border-radius:16px;padding:25px;width:100%;max-width:400px}
input,select{width:100%;padding:12px 16px;margin:8px 0;border-radius:10px;border:1px solid #e9456044;background:#0a0a1a;color:white;font-size:16px;font-family:'Rajdhani',sans-serif;outline:none}
input:focus,select:focus{border-color:#e94560}
input::placeholder{color:#555}
.btn{width:100%;padding:13px;margin-top:10px;border-radius:10px;border:none;background:linear-gradient(135deg,#e94560,#c73652);color:white;font-size:16px;font-family:'Orbitron',sans-serif;cursor:pointer;letter-spacing:1px;transition:all 0.3s}
.btn:disabled{opacity:0.4;cursor:not-allowed}
.btn-yesil{background:linear-gradient(135deg,#4ecdc4,#2ea89f)}
#bilgi{margin:8px 0;font-size:15px;color:#ffd700;text-align:center;min-height:22px}
#sure-goster{font-family:'Orbitron',sans-serif;font-size:22px;color:#e94560;text-align:center;margin:5px 0}
.harita{display:inline-grid;gap:3px;margin:10px auto;background:#0a0a1a;padding:8px;border-radius:12px;border:1px solid #e9456022}
.hucre{width:36px;height:36px;border-radius:5px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold;background:#16213e;border:1px solid #ffffff11;transition:all 0.15s}
.hucre:hover{transform:scale(1.1);z-index:1}
.hucre.secili{border:2px solid #ffd700;box-shadow:0 0 10px #ffd700}
.hucre.hedef{border:2px solid #ff6b6b;box-shadow:0 0 10px #ff6b6b}
.hucre.engel{background:#2a2a2a;cursor:not-allowed}
.skorlar{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin:5px 0}
.skor-kart{background:#16213e;border-radius:8px;padding:5px 10px;font-size:13px;border:1px solid #ffffff22}
.oda-kodu{background:#16213e;border:1px solid #ffd70044;border-radius:8px;padding:8px;text-align:center;margin:8px 0;font-size:22px;letter-spacing:4px;color:#ffd700;font-family:'Orbitron',sans-serif}
.oyuncu-listesi{background:#0a0a1a;border-radius:8px;padding:8px;margin:5px 0;font-size:14px;line-height:2}
.sohbet-kutu{background:#16213e;border-radius:8px;padding:8px;margin:8px 0;width:100%;max-width:420px}
.sohbet-mesajlar{height:80px;overflow-y:auto;font-size:12px;margin-bottom:5px}
.sohbet-mesajlar p{margin:2px 0;padding:2px 5px}
.sohbet-giris{display:flex;gap:5px}
.sohbet-giris input{margin:0;padding:8px;font-size:13px}
.istat-kart{background:#16213e;border-radius:12px;padding:15px;text-align:center;margin:5px 0;border:1px solid #e9456033}
.kazanan-text{font-family:'Orbitron',sans-serif;font-size:20px;color:#ffd700;margin-bottom:10px}
.tur-bilgi{font-size:13px;color:#888;text-align:center}
</style>
</head>
<body>
<h1>⚔️ STRATEJİ</h1>
<p class="subtitle">ORDU SAVAŞLARI</p>

<div id="giris" class="card">
<input id="isim" placeholder="👤 Oyuncu adın"/>
<select id="mod">
<option value="bot">🤖 Bot ile oyna</option>
<option value="2">👥 2 Kişilik Online</option>
<option value="4">👥👥 4 Kişilik Online</option>
</select>
<input id="oda" placeholder="🔑 Oda kodu (boş = yeni oda)"/>
<button class="btn" onclick="katil()">OYUNA GİR</button>
</div>

<div id="bekleme" style="display:none" class="card">
<div class="oda-kodu" id="oda-kodu-goster"></div>
<div style="color:#888;font-size:12px;text-align:center;margin-bottom:10px" id="oda-aciklama"></div>
<div class="oyuncu-listesi" id="oyuncu-listesi"></div>
<button class="btn btn-yesil" id="baslat-btn" onclick="oyunuBaslat()" style="display:none" disabled>▶ OYUNU BAŞLAT</button>
<div id="bekleme-bilgi" style="color:#888;font-size:13px;text-align:center;margin-top:8px"></div>
</div>

<div id="oyun" style="display:none;width:100%;max-width:420px;flex-direction:column;align-items:center">
<div id="sure-goster"></div>
<div id="bilgi"></div>
<div class="tur-bilgi" id="tur-bilgi"></div>
<div class="skorlar" id="skorlar"></div>
<div id="secim-bilgi" style="font-size:12px;color:#aaa;text-align:center;min-height:18px"></div>
<div class="harita" id="harita" style="grid-template-columns:repeat(8,36px)"></div>
<button class="btn btn-yesil" id="btn-gonder" onclick="orduyuGonder()" style="display:none" disabled>⚔️ ORDU GÖNDER</button>
<div class="sohbet-kutu">
<div class="sohbet-mesajlar" id="sohbet-mesajlar"></div>
<div class="sohbet-giris">
<input id="sohbet-input" placeholder="Mesaj yaz..." onkeypress="if(event.key==='Enter')mesajGonder()"/>
<button class="btn" style="width:60px;padding:8px;font-size:12px;margin:0" onclick="mesajGonder()">Gönder</button>
</div>
</div>
</div>

<div id="oyun-bitti" style="display:none" class="card">
<div class="istat-kart">
<div class="kazanan-text" id="kazanan-text"></div>
<div id="istatistikler"></div>
<button class="btn" style="margin-top:10px" onclick="location.reload()">🔄 YENİDEN OYNA</button>
</div>
</div>

<script>
const socket=io();
let oyuncuIsim='',odaId='',benimSiram=false,kaptan=false,secModu='bot';
let seciliKare=null,hedefKare=null,oyuncular=[];
const renkler={};
const renkListesi=['#e94560','#4ecdc4','#ffd700','#a855f7'];

function katil(){
oyuncuIsim=document.getElementById('isim').value.trim();
secModu=document.getElementById('mod').value;
const oda=document.getElementById('oda').value.trim();
if(!oyuncuIsim)return alert('İsim gir!');
if(oda)socket.emit('odaya_katil',{isim:oyuncuIsim,oda_id:oda});
else socket.emit('oda_olustur',{isim:oyuncuIsim,mod:secModu});
}

function oyunuBaslat(){
socket.emit('oyunu_baslat',{oda_id:odaId});
}

function mesajGonder(){
const msg=document.getElementById('sohbet-input').value.trim();
if(!msg)return;
socket.emit('sohbet',{oda_id:odaId,isim:oyuncuIsim,mesaj:msg});
document.getElementById('sohbet-input').value='';
}

socket.on('oda_olusturuldu',d=>{
odaId=d.oda_id;kaptan=true;
document.getElementById('giris').style.display='none';
document.getElementById('bekleme').style.display='block';
document.getElementById('oda-kodu-goster').textContent=odaId;
if(d.mod==='bot'){
document.getElementById('oda-aciklama').textContent='Bot ile oynuyorsun!';
document.getElementById('baslat-btn').style.display='block';
document.getElementById('baslat-btn').disabled=false;
document.getElementById('bekleme-bilgi').textContent='Hazır olunca başlat!';
}else{
document.getElementById('oda-aciklama').textContent='Arkadaşına bu kodu gönder!';
}
oyuncuListesiGuncelle(d.oyuncular,d.max_oyuncu);
});

socket.on('katilindi',d=>{
odaId=d.oda_id;
document.getElementById('giris').style.display='none';
document.getElementById('bekleme').style.display='block';
document.getElementById('oda-kodu-goster').textContent=odaId;
document.getElementById('oda-aciklama').textContent='Odaya katıldın!';
oyuncuListesiGuncelle(d.oyuncular,d.max_oyuncu);
});

socket.on('oyuncu_katildi',d=>{
oyuncuListesiGuncelle(d.oyuncular,d.max_oyuncu);
if(kaptan&&d.oyuncular.length>=2){
document.getElementById('baslat-btn').style.display='block';
document.getElementById('baslat-btn').disabled=false;
document.getElementById('bekleme-bilgi').textContent='Hazır olunca başlat!';
}
});

function oyuncuListesiGuncelle(liste,max){
const div=document.getElementById('oyuncu-listesi');
div.innerHTML='<b style="color:#e94560">Oyuncular ('+liste.length+'/'+max+'):</b><br>'+liste.map((o,i)=>'<span style="color:'+(renkListesi[i]||'#fff')+'">● '+o+'</span>').join('  ');
}

socket.on('oyun_basladi',d=>{
oyuncular=d.oyuncular;
oyuncular.forEach((o,i)=>{renkler[o]=renkListesi[i];});
document.getElementById('bekleme').style.display='none';
document.getElementById('oyun').style.display='flex';
document.getElementById('oyun').style.flexDirection='column';
document.getElementById('oyun').style.alignItems='center';
haritaCiz(d.harita);
turBilgiGuncelle(d.aktif_oyuncu,d.tur);
});

socket.on('hamle_sonucu',d=>{
haritaCiz(d.harita);
turBilgiGuncelle(d.aktif_oyuncu,d.tur);
seciliKare=null;hedefKare=null;
document.getElementById('btn-gonder').style.display='none';
document.getElementById('secim-bilgi').textContent='';
});

socket.on('sure_guncelle',d=>{
const dk=Math.floor(d.sure/60);
const sn=d.sure%60;
document.getElementById('sure-goster').textContent=dk+':'+(sn<10?'0':'')+sn;
if(d.sure<=30)document.getElementById('sure-goster').style.color='#ff6b6b';
});

socket.on('sohbet_mesaj',d=>{
const div=document.getElementById('sohbet-mesajlar');
const p=document.createElement('p');
p.style.color=renkler[d.isim]||'#aaa';
p.textContent=d.isim+': '+d.mesaj;
div.appendChild(p);
div.scrollTop=div.scrollHeight;
});

socket.on('oyun_bitti',d=>{
document.getElementById('oyun').style.display='none';
document.getElementById('oyun-bitti').style.display='block';
document.getElementById('kazanan-text').textContent=(d.sure_bitti?'⏱️ SÜRE BİTTİ! ':'')+'🏆 KAZANAN: '+d.kazanan;
const ist=document.getElementById('istatistikler');
ist.innerHTML=Object.entries(d.istatistik).map(([o,s])=>'<div style="color:'+(renkler[o]||'#fff')+';margin:4px 0">'+o+': '+s+' kare</div>').join('');
});

socket.on('hata',d=>alert(d.mesaj));

function turBilgiGuncelle(aktif,tur){
benimSiram=(aktif===oyuncuIsim);
document.getElementById('tur-bilgi').innerHTML='Tur '+tur+' | Sıra: <span style="color:'+(renkler[aktif]||'#fff')+'">'+aktif+'</span>';
document.getElementById('bilgi').innerHTML=benimSiram?'⚡ Senin sıran! Kare seç!':'⏳ '+aktif+' oynuyor...';
skorGuncelle();
}

function skorGuncelle(){
if(!window.sonHarita)return;
const sayim={};
oyuncular.forEach(o=>sayim[o]=0);
window.sonHarita.forEach(s=>s.forEach(h=>{if(h.sahip)sayim[h.sahip]=(sayim[h.sahip]||0)+1;}));
document.getElementById('skorlar').innerHTML=oyuncular.map(o=>'<div class="skor-kart" style="border-color:'+(renkler[o]||'#fff')+'88;color:'+(renkler[o]||'#fff')+'">'+o+' '+(sayim[o]||0)+'</div>').join('');
}

function hucreClick(i,j){
if(!benimSiram)return;
const h=window.sonHarita[i][j];
if(h.engel)return;
if(!seciliKare){
if(h.sahip===oyuncuIsim&&h.guc>1){
seciliKare={i,j};
document.getElementById('secim-bilgi').textContent='✅ Seçildi ('+i+','+j+') Güç:'+h.guc+' | Hedef seç!';
haritaCiz(window.sonHarita);
}else{
document.getElementById('bilgi').innerHTML='⚠️ Kendi karen seç! (Güç 2+)';
}
}else{
if(i===seciliKare.i&&j===seciliKare.j){
seciliKare=null;hedefKare=null;
document.getElementById('secim-bilgi').textContent='';
document.getElementById('btn-gonder').style.display='none';
haritaCiz(window.sonHarita);return;
}
const komsu=Math.abs(i-seciliKare.i)+Math.abs(j-seciliKare.j)===1;
if(!komsu){document.getElementById('bilgi').innerHTML='⚠️ Sadece komşu kare!';return;}
hedefKare={i,j};
document.getElementById('secim-bilgi').textContent='⚔️ '+seciliKare.i+','+seciliKare.j+' → '+i+','+j;
document.getElementById('btn-gonder').style.display='block';
document.getElementById('btn-gonder').disabled=false;
haritaCiz(window.sonHarita);
}
}

function orduyuGonder(){
if(!seciliKare||!hedefKare)return;
socket.emit('hamle_yap',{oda_id:odaId,oyuncu:oyuncuIsim,kaynak_x:seciliKare.i,kaynak_y:seciliKare.j,hedef_x:hedefKare.i,hedef_y:hedefKare.j});
document.getElementById('btn-gonder').disabled=true;
}

function haritaCiz(harita){
window.sonHarita=harita;
const div=document.getElementById('harita');div.innerHTML='';
harita.forEach((satir,i)=>satir.forEach((h,j)=>{
const hucre=document.createElement('div');
hucre.className='hucre';
if(h.engel){hucre.classList.add('engel');hucre.textContent='⛰️';div.appendChild(hucre);return;}
if(seciliKare&&seciliKare.i===i&&seciliKare.j===j)hucre.classList.add('secili');
if(hedefKare&&hedefKare.i===i&&hedefKare.j===j)hucre.classList.add('hedef');
const renk=h.sahip?renkler[h.sahip]||'#888':'#16213e';
hucre.style.background=renk;
if(h.sahip)hucre.style.boxShadow='0 0 5px '+renk+'66';
if(h.guc>0)hucre.textContent=h.guc;
hucre.onclick=()=>hucreClick(i,j);
div.appendChild(hucre);
}));
skorGuncelle();
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('oda_olustur')
def oda_olustur(data):
    oda_id='P'+str(random.randint(1000,9999))
    mod=data.get('mod','2')
    max_oyuncu=4 if mod=='4' else 2
    oyunlar[oda_id]={'oyuncular':[],'harita':harita_olustur(),'tur':1,'aktif':0,'sure':300,'basladi':False,'mod':mod,'max_oyuncu':max_oyuncu}
    join_room(oda_id)
    oyunlar[oda_id]['oyuncular'].append(data['isim'])
    emit('oda_olusturuldu',{'oda_id':oda_id,'oyuncular':oyunlar[oda_id]['oyuncular'],'max_oyuncu':max_oyuncu,'mod':mod})

@socketio.on('odaya_katil')
def odaya_katil(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:emit('hata',{'mesaj':'Oda bulunamadı!'});return
    oyun=oyunlar[oda_id]
    if len(oyun['oyuncular'])>=oyun['max_oyuncu']:emit('hata',{'mesaj':'Oda dolu!'});return
    join_room(oda_id)
    oyun['oyuncular'].append(data['isim'])
    emit('katilindi',{'oda_id':oda_id,'oyuncular':oyun['oyuncular'],'max_oyuncu':oyun['max_oyuncu']})
    socketio.emit('oyuncu_katildi',{'oyuncular':oyun['oyuncular'],'max_oyuncu':oyun['max_oyuncu']},room=oda_id)

@socketio.on('oyunu_baslat')
def oyunu_baslat_event(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    if oyun['mod']=='bot' and '🤖 Bot' not in oyun['oyuncular']:
        oyun['oyuncular'].append('🤖 Bot')
    oyun['basladi']=True
    baslangic=[(0,0),(7,7),(0,7),(7,0)]
    for i,oyuncu in enumerate(oyun['oyuncular']):
        x,y=baslangic[i]
        oyun['harita'][x][y]['sahip']=oyuncu
        oyun['harita'][x][y]['guc']=5
    aktif=oyun['oyuncular'][0]
    socketio.emit('oyun_basladi',{'harita':oyun['harita'],'oyuncular':oyun['oyuncular'],'aktif_oyuncu':aktif,'tur':1},room=oda_id)
    t=threading.Thread(target=sure_sayaci,args=(oda_id,))
    t.daemon=True
    t.start()
    if aktif=='🤖 Bot':
        t2=threading.Thread(target=bot_hamle,args=(oda_id,))
        t2.daemon=True
        t2.start()

@socketio.on('hamle_yap')
def hamle_yap(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    if oyun['oyuncular'][oyun['aktif']]!=data['oyuncu']:return
    _hamle_yap_logic(oda_id,data['oyuncu'],data['kaynak_x'],data['kaynak_y'],data['hedef_x'],data['hedef_y'])

@socketio.on('sohbet')
def sohbet(data):
    socketio.emit('sohbet_mesaj',{'isim':data['isim'],'mesaj':data['mesaj']},room=data['oda_id'])

if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5000,debug=True)
