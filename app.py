from flask import Flask,render_template_string
from flask_socketio import SocketIO,emit,join_room
import random
app=Flask(__name__)
app.config['SECRET_KEY']='strateji2024'
socketio=SocketIO(app,cors_allowed_origins="*")
oyunlar={}
def harita_olustur(boyut=10):
    return [[{'sahip':None,'guc':1,'x':i,'y':j}for j in range(boyut)]for i in range(boyut)]
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
h1{font-family:'Orbitron',sans-serif;font-size:28px;color:#e94560;text-shadow:0 0 20px #e9456088;margin-bottom:5px;letter-spacing:3px}
.subtitle{color:#888;font-size:14px;margin-bottom:30px;letter-spacing:2px}
.card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #e9456033;border-radius:16px;padding:25px;width:100%;max-width:400px;box-shadow:0 0 30px #e9456022}
input{width:100%;padding:12px 16px;margin:8px 0;border-radius:10px;border:1px solid #e9456044;background:#0a0a1a;color:white;font-size:16px;font-family:'Rajdhani',sans-serif;outline:none;transition:border 0.3s}
input:focus{border-color:#e94560;box-shadow:0 0 10px #e9456033}
input::placeholder{color:#555}
button{width:100%;padding:14px;margin-top:12px;border-radius:10px;border:none;background:linear-gradient(135deg,#e94560,#c73652);color:white;font-size:18px;font-family:'Orbitron',sans-serif;cursor:pointer;letter-spacing:2px;transition:all 0.3s;box-shadow:0 4px 15px #e9456044}
button:hover{transform:translateY(-2px);box-shadow:0 6px 20px #e9456066}
button:active{transform:translateY(0)}
#bilgi{margin:10px 0;font-size:16px;color:#ffd700;text-align:center;min-height:24px;text-shadow:0 0 10px #ffd70066}
.harita{display:inline-grid;grid-template-columns:repeat(10,34px);gap:3px;margin:15px auto;background:#0a0a1a;padding:10px;border-radius:12px;border:1px solid #e9456022;box-shadow:0 0 20px #00000066}
.hucre{width:34px;height:34px;border-radius:5px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;background:#16213e;border:1px solid #ffffff11;transition:all 0.2s;box-shadow:inset 0 0 5px #00000044}
.hucre:hover{transform:scale(1.15);z-index:1;box-shadow:0 0 10px currentColor}
.skorlar{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:8px 0}
.skor-kart{background:#16213e;border-radius:8px;padding:6px 12px;font-size:13px;border:1px solid #ffffff11}
.oda-kodu{background:#16213e;border:1px solid #ffd70044;border-radius:8px;padding:10px;text-align:center;margin:10px 0;font-size:20px;letter-spacing:4px;color:#ffd700;font-family:'Orbitron',sans-serif}
.oyuncu-sayisi{color:#888;font-size:13px;margin-top:5px}
</style>
</head>
<body>
<h1>⚔️ STRATEJİ</h1>
<p class="subtitle">TOPRAK SAVAŞLARI</p>
<div id="giris" class="card">
<input id="isim" placeholder="👤 Oyuncu adın"/>
<input id="oda" placeholder="🔑 Oda kodu (boş = yeni oda)"/>
<button onclick="katil()">OYUNA GİR</button>
</div>
<div id="oyun" style="display:none;width:100%;max-width:420px">
<div id="bilgi"></div>
<div id="oda-bilgi"></div>
<div class="skorlar" id="skorlar"></div>
<div class="harita" id="harita"></div>
</div>
<script>
const socket=io();
let oyuncuIsim='',odaId='';
const renkler={};
const renkListesi=['#e94560','#4ecdc4','#ffd700','#a855f7'];
const isimler=[];

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
document.getElementById('oyun').style.flexDirection='column';
document.getElementById('oyun').style.alignItems='center';
document.getElementById('oda-bilgi').innerHTML='<div class="oda-kodu">'+odaId+'</div><div class="oyuncu-sayisi">Arkadaşlarına bu kodu gönder!</div>';
document.getElementById('bilgi').innerHTML='⏳ Oyuncular bekleniyor...';
});

socket.on('katilindi',d=>{
odaId=d.oda_id;
document.getElementById('giris').style.display='none';
document.getElementById('oyun').style.display='flex';
document.getElementById('oyun').style.flexDirection='column';
document.getElementById('oyun').style.alignItems='center';
document.getElementById('bilgi').innerHTML='✅ Odaya katıldın! Oyun başlaması bekleniyor...';
});

socket.on('oyun_basladi',d=>{
d.oyuncular.forEach((o,i)=>{renkler[o]=renkListesi[i];});
document.getElementById('oda-bilgi').innerHTML='';
haritaCiz(d.harita,d.oyuncular);
document.getElementById('bilgi').innerHTML='⚔️ Savaş başladı!';
});

socket.on('harita_guncellendi',d=>{
haritaCiz(d.harita,d.oyuncular);
skorGuncelle(d.harita,d.oyuncular);
});

function skorGuncelle(harita,oyuncular){
const sayim={};
oyuncular.forEach(o=>sayim[o]=0);
harita.forEach(s=>s.forEach(h=>{if(h.sahip)sayim[h.sahip]=(sayim[h.sahip]||0)+1;}));
const div=document.getElementById('skorlar');
div.innerHTML=oyuncular.map(o=>'<div class="skor-kart" style="border-color:'+renkler[o]+'44;color:'+renkler[o]+'">'+o+': '+(sayim[o]||0)+'</div>').join('');
}

function haritaCiz(harita,oyuncular){
if(oyuncular)skorGuncelle(harita,oyuncular);
const div=document.getElementById('harita');
div.innerHTML='';
harita.forEach((satir,i)=>satir.forEach((h,j)=>{
const hucre=document.createElement('div');
hucre.className='hucre';
const renk=h.sahip?renkler[h.sahip]||'#888':'#16213e';
hucre.style.background=renk;
if(h.sahip)hucre.style.boxShadow='0 0 6px '+renk+'88';
hucre.textContent=h.guc>1?h.guc:'';
hucre.onclick=()=>socket.emit('hamle_yap',{oda_id:odaId,x:i,y:j,oyuncu:oyuncuIsim});
div.appendChild(hucre);
}));
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
    oyunlar[oda_id]={'oyuncular':[],'harita':harita_olustur()}
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
    for i,oyuncu in enumerate(oyun['oyuncular']):
        x,y=[(0,0),(0,9),(9,0),(9,9)][i]
        oyun['harita'][x][y]['sahip']=oyuncu
        oyun['harita'][x][y]['guc']=5
    socketio.emit('oyun_basladi',{'harita':oyun['harita'],'oyuncular':oyun['oyuncular']},room=oda_id)
@socketio.on('hamle_yap')
def hamle_yap(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    h=oyun['harita'][data['x']][data['y']]
    if h['sahip']!=data['oyuncu']:h['sahip']=data['oyuncu'];h['guc']=1
    else:h['guc']+=1
    socketio.emit('harita_guncellendi',{'harita':oyun['harita'],'oyuncular':oyun['oyuncular']},room=oda_id)
if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5000,debug=True)
