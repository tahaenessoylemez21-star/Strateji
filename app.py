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
<title>Strateji</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<style>
body{background:#1a1a2e;color:white;font-family:Arial;text-align:center;padding:10px}
h1{color:#e94560}
.harita{display:inline-grid;grid-template-columns:repeat(10,32px);gap:2px;margin:10px auto}
.hucre{width:32px;height:32px;border:1px solid #444;border-radius:3px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:10px;background:#16213e}
input,button{padding:10px;margin:5px;border-radius:8px;border:none;font-size:15px;width:80%}
button{background:#e94560;color:white;cursor:pointer}
#bilgi{margin:10px;font-size:15px;color:#ffd700}
</style>
</head>
<body>
<h1>Strateji Oyunu</h1>
<div id="giris">
<input id="isim" placeholder="Adın"/><br>
<input id="oda" placeholder="Oda kodu (boş=yeni oda)"/><br>
<button onclick="katil()">Oyuna Gir</button>
</div>
<div id="oyun" style="display:none">
<div id="bilgi"></div>
<div class="harita" id="harita"></div>
</div>
<script>
const socket=io();
let oyuncuIsim='',odaId='';
const renkler={'P1':'#e94560','P2':'#0f3460','P3':'#533483','P4':'#157347'};
function katil(){
oyuncuIsim=document.getElementById('isim').value;
const oda=document.getElementById('oda').value;
if(!oyuncuIsim)return alert('İsim gir!');
if(oda)socket.emit('odaya_katil',{isim:oyuncuIsim,oda_id:oda});
else socket.emit('oda_olustur',{isim:oyuncuIsim});
}
socket.on('oda_olusturuldu',d=>{odaId=d.oda_id;document.getElementById('giris').style.display='none';document.getElementById('oyun').style.display='block';document.getElementById('bilgi').innerHTML='Oda: <b>'+odaId+'</b> - Arkadaşlarını bekle!';});
socket.on('katilindi',d=>{odaId=d.oda_id;document.getElementById('giris').style.display='none';document.getElementById('oyun').style.display='block';document.getElementById('bilgi').innerHTML='4 oyuncu bekleniyor...';});
socket.on('oyun_basladi',d=>{haritaCiz(d.harita);document.getElementById('bilgi').innerHTML='Oyun basladi! Toprak ele gecir!';});
socket.on('harita_guncellendi',d=>haritaCiz(d.harita));
function haritaCiz(harita){
const div=document.getElementById('harita');div.innerHTML='';
harita.forEach((satir,i)=>satir.forEach((h,j)=>{
const hucre=document.createElement('div');hucre.className='hucre';
hucre.style.background=h.sahip?renkler[h.sahip]||'#888':'#16213e';
hucre.textContent=h.guc>1?h.guc:'';
hucre.onclick=()=>socket.emit('hamle_yap',{oda_id:odaId,x:i,y:j,oyuncu:oyuncuIsim});
div.appendChild(hucre);}));}
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
        if len(oyunlar[oda_id]['oyuncular'])==4:
            oyunu_baslat(oda_id)
def oyunu_baslat(oda_id):
    oyun=oyunlar[oda_id]
    for i,oyuncu in enumerate(oyun['oyuncular']):
        x,y=[(0,0),(0,9),(9,0),(9,9)][i]
        oyun['harita'][x][y]['sahip']=oyuncu
        oyun['harita'][x][y]['guc']=5
    socketio.emit('oyun_basladi',{'harita':oyun['harita']},room=oda_id)
@socketio.on('hamle_yap')
def hamle_yap(data):
    oda_id=data['oda_id']
    if oda_id not in oyunlar:return
    oyun=oyunlar[oda_id]
    h=oyun['harita'][data['x']][data['y']]
    if h['sahip']!=data['oyuncu']:h['sahip']=data['oyuncu'];h['guc']=1
    else:h['guc']+=1
    socketio.emit('harita_guncellendi',{'harita':oyun['harita']},room=oda_id)
if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5000,debug=True)
