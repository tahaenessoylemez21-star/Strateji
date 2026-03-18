from flask import Flask,render_template_string
from flask_socketio import SocketIO,emit,join_room
import random
app=Flask(__name__)
app.config['SECRET_KEY']='strateji2024'
socketio=SocketIO(app,cors_allowed_origins="*")
oyunlar={}
def harita_olustur(boyut=8):
    return [[{'sahip':None,'guc':0,'x':i,'y':j}for j in range(boyut)]for i in range(boyut)]
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
.card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #e9456033;border-radius:16px;padding:25px;width:100%;max-width:400px;box-shadow:0 0 30px #e9456022}
input{width:100%;padding:12px 16px;margin:8px 0;border-radius:10px;border:1px solid #e9456044;background:#0a0a1a;color:white;font-size:16px;font-family:'Rajdhani',sans-serif;outline:none;transition:border 0.3s}
input:focus{border-color:#e94560;box-shadow:0 0 10px #e9456033}
input::placeholder{color:#555}
button{width:100%;padding:14px;margin-top:12px;border-radius:10px;border:none;background:linear-gradient(135deg,#e94560,#c73652);color:white;font-size:16px;font-family:'Orbitron',sans-serif;cursor:pointer;letter-spacing:1px;transition:all 0.3s;box-shadow:0 4px 15px #e9456044}
button:active{transform:scale(0.98)}
#bilgi{margin:8px 0;font-size:15px;color:#ffd700;text-align:center;min-height:22px;text-shadow:0 0 10px #ffd70066}
#tur-bilgi{font-size:13px;color:#888;text-align:center;margin-bottom:5px}
.harita{display:inline-grid;gap:3px;margin:10px auto;background:#0a0a1a;padding:10px;border-radius:12px;border:1px solid #e9456022}
.hucre{width:38px;height:38px;border-radius:6px;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:13px;font-weight:bold;background:#16213e;border:1px solid #ffffff11;transition:all 0.15s;position:relative}
.hucre:hover{transform:scale(1.12);z-index:1}
.hucre.secili{border:2px solid #ffd700;box-shadow:0 0 12px #ffd700;}
.hucre .guc{font-size:14px;font-weight:bold}
.hucre .flag{font-size:9px;opacity:0.8}
.skorlar{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin:6px 0}
.skor-kart{background:#16213e;border-radius:8px;padding:5px 10px;font-size:13px;border:1px solid #ffffff11}
.skor-kart.aktif{border-width:2px;box-shadow:0 0 8px currentColor}
.oda-kodu{background:#16213e;border:1px solid #ffd70044;border-radius:8px;padding:8px;text-align:center;margin:8px 0;font-size:22px;letter-spacing:4px;color:#ffd700;font-family:'Orbitron',sans-serif}
.bilgi-kutu{background:#16213e;border-radius:8px;padding:8px 12px;font-size:13px;color:#aaa;text-align:center;margin:5px 0;border:1px solid #ffffff11}
.btn-gonder{background:linear-gradient(135deg,#4ecdc4,#2ea89f);margin-top:6px;font-size:13px;padding:10px}
.btn-gonder:disabled{opacity:0.4;cursor:not-allowed}
</style>
</head>
<body>
<h1>⚔️ STRATEJİ</h1>
<p class="subtitle">ORDU SAVAŞLARI</p>
<div id="giris" class="card">
<input id="isim" placeholder="👤 Oyuncu adın"/>
<input id="oda" placeholder="🔑 Oda kodu (boş = yeni oda)"/>
<button onclick="katil()">OYUNA GİR</button>
</div>
<div id="oyun" style="display:none;width:100%;max-width:420px;display:none;flex-direction:column;align-items:center">
<div id="bilgi"></div>
<div id="tur-bilgi"></div>
<div id="oda-bilgi"></div>
<div class="skorlar" id="skorlar"></div>
<div id="secim-bilgi" class="bilgi-kutu" style="display:none"></div>
<div class="harita" id="harita" style="grid-template-columns:repeat(8,38px)"></div>
<button class="btn-gonder" id="btn-gonder" onclick="orduyuGonder()" style="display:none" disabled>⚔️ ORDU GÖNDER</button>
</div>
<script>
const socket=io();
let oyuncuIsim='',odaId='',benimSiram=false;
let seciliKare=null,hedefKare=null;
const renkler={};
const renkListesi=['#e94560','#4ecdc4','#ffd700','#a855f7'];
let oyuncular=[];

function katil(){
oyuncuIsim=document.getElementById('isim').value.trim();
const oda=document.getElementById('oda').value.trim();
if(!oyuncuIsim)return alert('İsim gir!');
if(oda)socket.emit('odaya_katil',{isim:oyuncuIsim,oda_id:oda});
else socket.emit('oda_olustur',{isim:oyuncuIsim});
}

socket.on('oda_olusturuldu',d=>{
odaId=d.oda_id;
document.getElementById('giris').style.display='none';
document.getElementById('oyun').style.display='flex';
document.getElementById('oda-bilgi').innerHTML='<div class="oda-kodu">'+odaId+'</div><div style="color:#888;font-size:12px;text-align:center">Arkadaşına bu kodu gönder!</div>';
document.getElementById('bilgi').innerHTML='⏳ Rakip bekleniyor...';
});

socket.on('katilindi',d=>{
odaId=d.oda_id;
document.getElementById('giris').style.display='none';
document.getElementById('oyun').style.display='flex';
document.getElementById('bilgi').innerHTML='✅ Katıldın! Oyun başlıyor...';
});

socket.on('oyun_basladi',d=>{
oyuncular=d.oyuncular;
oyuncular.forEach((o,i)=>{renkler[o]=renkListesi[i];});
document.getElementById('oda-bilgi').innerHTML='';
haritaCiz(d.harita);
turBilgiGuncelle(d.aktif_oyuncu,d.tur);
});

socket.on('hamle_sonucu',d=>{
haritaCiz(d.harita);
turBilgiGuncelle(d.aktif_oyuncu,d.tur);
seciliKare=null;hedefKare=null;
document.getElementById('btn-gonder').style.display='none';
document.getElementById('secim-bilgi').style.display='none';
});

socket.on('oyun_bitti',d=>{
document.getElementById('bilgi').innerHTML='🏆 KAZANAN: '+d.kazanan+'! ('+d.skor+' kare)';
document.getElementById('tur-bilgi').innerHTML='Oyun bitti!';
});

function turBilgiGuncelle(aktif,tur){
benimSiram=(aktif===oyuncuIsim);
document.getElementById('tur-bilgi').innerHTML='Tur '+tur+' | Sıra: <span style="color:'+(renkler[aktif]||'#fff')+'">'+aktif+'</span>';
if(benimSiram){
document.getElementById('bilgi').innerHTML='⚡ Senin sıran! Kare seç!';
}else{
document.getElementById('bilgi').innerHTML='⏳ '+aktif+' oynuyor...';
}
skorGuncelle();
}

function skorGuncelle(){
if(!oyuncular.length)return;
const harita=window.sonHarita;
if(!harita)return;
const sayim={};
oyuncular.forEach(o=>sayim[o]=0);
harita.forEach(s=>s.forEach(h=>{if(h.sahip)sayim[h.sahip]=(sayim[h.sahip]||0)+1;}));
const aktifOyuncu=document.getElementById('tur-bilgi').innerHTML.includes(oyuncuIsim)?oyuncuIsim:'';
document.getElementById('skorlar').innerHTML=oyuncular.map(o=>'<div class="skor-kart'+(o===aktifOyuncu?' aktif':'')+'" style="border-color:'+renkler[o]+'88;color:'+renkler[o]+'">'+o+' '+( sayim[o]||0)+'</div>').join('');
}

function hucreClick(i,j){
if(!benimSiram)return;
const harita=window.sonHarita;
const h=harita[i][j];
if(!seciliKare){
if(h.sahip===oyuncuIsim&&h.guc>1){
seciliKare={i,j};
document.getElementById('secim-bilgi').style.display='block';
document.getElementById('secim-bilgi').innerHTML='✅ Seçildi: ('+i+','+j+') | Güç: '+h.guc+' | Şimdi hedef seç!';
haritaCiz(harita);
}else{
document.getElementById('bilgi').innerHTML='⚠️ Kendi kare seç! (Güç 2+)';
}
}else{
if(i===seciliKare.i&&j===seciliKare.j){
seciliKare=null;
document.getElementById('secim-bilgi').style.display='none';
document.getElementById('btn-gonder').style.display='none';
haritaCiz(harita);
return;
}
const kaynak=harita[seciliKare.i][seciliKare.j];
const komsu=Math.abs(i-seciliKare.i)+Math.abs(j-seciliKare.j)===1;
if(!komsu){document.getElementById('bilgi').innerHTML='⚠️ Sadece komşu kareye gönderebilirsin!';return;}
hedefKare={i,j};
document.getElementById('secim-bilgi').innerHTML='⚔️ '+seciliKare.i+','+seciliKare.j+' → '+i+','+j+' | Güç: '+kaynak.guc;
document.getElementById('btn-gonder').style.display='block';
document.getElementById('btn-gonder').disabled=false;
haritaCiz(harita);
}
}

function orduyuGonder(){
if(!seciliKare||!hedefKare)return;
socket.emit('hamle_yap',{oda_id:odaId,oyuncu:oyuncuIsim,kaynak_x:seciliKare.i,kaynak_y:seciliKare.j,hedef_x:hedefKare.i,hedef_y:hedefKare.j});
document.getElementById('btn-gonder').disabled=true;
}

function haritaCiz(harita){
window.sonHarita=harita;
const div=document.getElementById('harita');
div.innerHTML='';
harita.forEach((satir,i)=>satir.forEach((h,j)=>{
const hucre=document.createElement('div');
hucre.className='hucre';
if(seciliKare&&seciliKare.i===i&&seciliKare.j===j)hucre.classList.add('secili');
if(hedefKare&&hedefKare.i===i&&hedefKare.j===j){hucre.style.border='2px solid #ff6b6b';hucre.style.boxShadow='0 0 10px #ff6b6b';}
const renk=h.sahip?renkler[h.sahip]||'#888':'#16213e';
hucre.style.background=renk;
if(h.sahip&&!seciliKare)hucre.style.boxShadow='0 0 5px '+renk+'66';
if(h.guc>0)hucre.innerHTML='<span class="guc">'+h.guc+'</span>';
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
    oyunlar[oda_id]={'oyuncular':[],'harita':harita_olustur(),'tur':1,'aktif':0}
    join_room(oda_id)
    oyunlar[oda_id]['oyuncular'].append(data['isim'])
    emit('oda_olusturuldu',{'oda_id':oda_id})
@socketio.on('odaya_katil')
def odaya_katil(data):
    oda_id=data['oda_id']
    if oda_id in oyunlar and len(oyunlar[oda_id]['oyuncular'])<4:
        join_room(oda_id)
        oyunlar[oda_id]['oyuncular'].append(data['isim'])
        emit('katilindi',{'oda_id':oda_id})
        if len(oyunlar[oda_id]['oyuncular'])==2:
            oyunu_baslat(oda_id)
def oyunu_baslat(oda_id):
    oyun=oyunlar[oda_id]
    baslangic=[(0,0),(7,7),(0,7),(7,0)]
    for i,oyuncu in enumerate(oyun['oyuncular']):
        x,y=baslangic[i]
        oyun['harita'][x][y]['sahip']=oyuncu
        oyun['harita'][x][y]['guc']=5
    aktif=oyun['oyuncular'][0]
    socketio.emit('oyun_basladi',{'harita':oyun['harita'],'oyuncular':oyun['oyuncular'],'aktif_oyuncu':aktif,'tur':1},room=oda_id)
@socketio.on('hamle_yap')
def hamle_yap(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    oyuncu=data['oyuncu']
    aktif_idx=oyun['aktif']
    if oyun['oyuncular'][aktif_idx]!=oyuncu:return
    kx,ky=data['kaynak_x'],data['kaynak_y']
    hx,hy=data['hedef_x'],data['hedef_y']
    kaynak=oyun['harita'][kx][ky]
    hedef=oyun['harita'][hx][hy]
    if kaynak['sahip']!=oyuncu or kaynak['guc']<2:return
    gonderilen=kaynak['guc']-1
    kaynak['guc']=1
    if hedef['sahip']==oyuncu:
        hedef['guc']+=gonderilen
    elif hedef['sahip'] is None:
        hedef['sahip']=oyuncu
        hedef['guc']=gonderilen
    else:
        if gonderilen>hedef['guc']:
            hedef['sahip']=oyuncu
            hedef['guc']=gonderilen-hedef['guc']
        elif gonderilen==hedef['guc']:
            hedef['sahip']=None
            hedef['guc']=0
        else:
            hedef['guc']-=gonderilen
    oyun['aktif']=(aktif_idx+1)%len(oyun['oyuncular'])
    oyun['tur']+=1
    aktif=oyun['oyuncular'][oyun['aktif']]
    sayimlar={}
    for s in oyun['harita']:
        for h in s:
            if h['sahip']:sayimlar[h['sahip']]=sayimlar.get(h['sahip'],0)+1
    toplam=sum(sayimlar.values())
    kazanan=None
    for o,s in sayimlar.items():
        if s==toplam:kazanan=o
    if kazanan:
        socketio.emit('oyun_bitti',{'kazanan':kazanan,'skor':toplam},room=oda_id)
    else:
        socketio.emit('hamle_sonucu',{'harita':oyun['harita'],'aktif_oyuncu':aktif,'tur':oyun['tur']},room=oda_id)
if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5000,debug=True)
    
