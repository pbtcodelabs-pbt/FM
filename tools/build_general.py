# 🥬 سبزی منڈی (جنرل ایپ) — صدام والی ماسٹر فائل سے خودکار تیاری
import re, sys, json, os
import os.path as _p
# استعمال (ریپو کی جڑ سے): python3 tools/build_general.py 'SM299TU#002'
ROOT=_p.dirname(_p.dirname(_p.abspath(__file__)))
SRC=ROOT; OUT=_p.join(ROOT,'general')
VERSION=sys.argv[1]
os.makedirs(OUT, exist_ok=True)
s=open(f'{SRC}/index.html',encoding='utf-8').read()
def rep(old,new,cnt=1):
    global s
    n=s.count(old); assert n==cnt,(n,old[:90]); s=s.replace(old,new)

# ---------- 0) ورژن ----------
s=re.sub(r"const APP_BUILD_VERSION = '[^']*';", f"const APP_BUILD_VERSION = '{VERSION}';", s, count=1)

# ---------- 1) سب سے پہلے چلنے والا حفاظتی سکرپٹ: الگ اسٹوریج، کلاؤڈ بند ----------
boot = r'''<script>
/* 🥬 سبزی منڈی — جنرل ایڈیشن کا حفاظتی حصہ (ہر چیز سے پہلے چلتا ہے)
   1) اس ایپ کا سارا فون والا ڈیٹا "SM::" کے الگ خانے میں — کسی دوسری ایپ (مثلاً فروٹ منڈی) سے کبھی نہ ملے
   2) کلاؤڈ (فائربیس) مکمل بند — جب تک اس ایپ کا اپنا فائربیس پروجیکٹ نہ لگے، کوئی ڈیٹا کلاؤڈ پر نہیں جاتا */
const APP_EDITION = 'general';
(function(){
  const P = 'SM::';
  const SP = Storage.prototype;
  const g = SP.getItem, st = SP.setItem, rm = SP.removeItem, k0 = SP.key;
  const lenDesc = Object.getOwnPropertyDescriptor(SP, 'length');
  function rawKeys(store){ const out = []; const n = lenDesc.get.call(store); for(let i = 0; i < n; i++){ out.push(k0.call(store, i)); } return out; }
  function mine(store){ return rawKeys(store).filter(k => k && k.indexOf(P) === 0).map(k => k.slice(P.length)); }
  SP.getItem = function(k){ return g.call(this, P + k); };
  SP.setItem = function(k, v){ return st.call(this, P + k, v); };
  SP.removeItem = function(k){ return rm.call(this, P + k); };
  SP.key = function(i){ const a = mine(this); return i < a.length ? a[i] : null; };
  SP.clear = function(){ mine(this).forEach(k => rm.call(this, P + k)); };
  Object.defineProperty(SP, 'length', { get(){ return mine(this).length; }, configurable: true });
  window.smLsKeys = function(){ return mine(window.localStorage); };
  const of = window.fetch.bind(window);
  window.fetch = function(input, init){
    const u = (typeof input === 'string') ? input : (input && input.url) || '';
    if(/firestore\.googleapis\.com|identitytoolkit\.googleapis\.com|securetoken\.googleapis\.com|firebaseio\.com/.test(u)){
      return Promise.resolve(new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } }));
    }
    return of(input, init);
  };
})();
function smBiz(){ try{ return (AppState.settings.businessName || '').trim() || 'سبزی منڈی'; }catch(e){ return 'سبزی منڈی'; } }
function smPhone(){ try{ return AppState.settings.businessPhone || ''; }catch(e){ return ''; } }
function smOwner(){ try{ return AppState.settings.ownerName || 'مالک'; }catch(e){ return 'مالک'; } }
</script>
'''
i=s.index('<head>')+len('<head>')
# charset meta پہلے رہے
m=re.search(r'<meta charset[^>]*>', s)
ins = m.end() if m and m.start() < s.index('</head>') else i
s=s[:ins]+'\n'+boot+s[ins:]

rep('Object.keys(localStorage)','smLsKeys()',2)
s=s.replace('indexedDB.open(', "indexedDB.open('SM_'+")

# ---------- 2) آئیکن / فونٹ فائلیں ایک فولڈر اوپر ----------
rep('href="favicon-32.png"','href="../favicon-32.png"')
rep('href="icon-180.png"','href="../icon-180.png"')
rep('href="icon-192.png"','href="../icon-192.png"')
rep("url('./JameelNooriNastaleeq-Regular.ttf')","url('../JameelNooriNastaleeq-Regular.ttf')")
rep("url('./JameelNooriNastaleeq-Kasheeda.ttf')","url('../JameelNooriNastaleeq-Kasheeda.ttf')")

# ---------- 3) زبردستی والا صدام کا نام/نمبر ہٹائیں ----------
rep("AppState.settings.businessName = 'صدام حسین فروٹ منڈی';\nAppState.settings.businessPhone = '03425556364';",
    "AppState.settings.businessName = AppState.settings.businessName || '';\nAppState.settings.businessPhone = AppState.settings.businessPhone || '';")

# ---------- 4) صدام کا ڈیٹا (سیڈ) خالی ----------
for name in ['CUSTOMERS_SEED_DATA','SUPPLIERS_SEED_DATA','APPROVAL_REQUESTS_SEED_DATA','INVOICES_SEED_DATA','LEDGER_CUSTOMERS_SEED_V1','LEDGER_SUPPLIERS_SEED_V1']:
    a=s.index(f'const {name} = [')+len(f'const {name} = [')
    b=s.index('\n];',a)
    s=s[:a]+' /* 🥬 جنرل ایپ: کوئی پرانا ریکارڈ نہیں */'+s[b:]
a=s.index('const USERS_SEED_DATA = [')
b=s.index('\n];',a)+3
s=s[:b]+"\nUSERS_SEED_DATA.splice(1); USERS_SEED_DATA[0].name = 'مالک'; USERS_SEED_DATA[0].phone = ''; // 🥬 صرف مالک (ایڈمن)\n"+s[b:]

# ---------- 5) نام اور نمبر — ہر جگہ دکان کا اپنا ----------
NAMES=['صدام حسین فروٹ منڈی','صدام فروٹ منڈی']
lines=s.split('\n')
in_script=False
out=[]
def js_replace(line, name, fn):
    res=''; idx=0
    while True:
        p=line.find(name, idx)
        if p<0: res+=line[idx:]; break
        before=line[:p]
        bt=before.count('`')-before.count('\\`')
        if bt%2==1:
            res+=line[idx:p]+'${'+fn+'}'; idx=p+len(name); continue
        q=None
        for ch in ["'",'"']:
            cnt=len(re.findall(r'(?<!\\)'+re.escape(ch), before))
            if cnt%2==1: q=ch; break
        if q:
            # پورا لفظی جملہ یہی نام ہو؟
            if line[p-1:p]==q and line[p+len(name):p+len(name)+1]==q:
                res+=line[idx:p-1]+fn; idx=p+len(name)+1; continue
            res+=line[idx:p]+q+' + '+fn+' + '+q; idx=p+len(name); continue
        res+=line[idx:p]+'سبزی منڈی'; idx=p+len(name)
    return res
for ln in lines:
    stripped=ln.strip()
    if re.search(r'<script(?![^>]*src)[^>]*>', ln): in_script=True
    is_comment = stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('<!--')
    if not is_comment:
        if in_script and '<script' not in ln:
            for n in NAMES:
                if n in ln: ln=js_replace(ln, n, 'smBiz()')
            if '03425556364' in ln: ln=js_replace(ln, '📞 03425556364', "('📞 ' + smPhone())") if '📞 03425556364' in ln else js_replace(ln,'03425556364','smPhone()')
            if "'Saddam Hussain'" in ln and 'USERS_SEED_DATA' not in ln and "name:'Saddam Hussain'" not in ln: ln=ln.replace("'Saddam Hussain'","smOwner()")
        else:
            for n in NAMES: ln=ln.replace(n,'سبزی منڈی')
            ln=ln.replace('📞 03425556364','')
    if '</script>' in ln: in_script=False
    out.append(ln)
s='\n'.join(out)
s=s.replace('Fruit Mandi POS','Sabzi Mandi POS')
for a_,b_ in [("acc.name || 'صدام حسین'","acc.name || smOwner()"),("'شکریہ — صدام حسین'","'شکریہ — ' + smBiz()"),
              ('صرف صدام حسین (ایڈمن)','صرف ایڈمن'),('صرف ایڈمن (صدام)','صرف ایڈمن'),('صدام حسین جلد','ایڈمن جلد'),
              ('صدام کو','ایڈمن کو'),('Powered by Saddam Fruit Mandi','Powered by Sabzi Mandi'),("name:'Saddam Hussain'","name:'مالک'"),
              ('Saddam Fruit Mandi','Sabzi Mandi'),('Saddam Hussain','Owner'),('صدام کی ہدایت','ہدایت'),('صدام حسین','مالک'),('صدام','مالک'),('Saddam','Owner')]:
    s=s.replace(a_,b_)
s=s.replace('<title>سبزی منڈی</title>','<title>سبزی منڈی</title>')

# ---------- 6) ہیڈر عنوان / لوگو کو پہچان (id) ----------
rep('white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">سبزی منڈی</span>\n      <span id="connStatusBadge"',
    'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" id="smTopTitle">سبزی منڈی</span>\n      <span id="connStatusBadge"')
rep('<div class="brand">سبزی منڈی</div>','<div class="brand" id="smSideBrand">سبزی منڈی</div>')
k=s.index('<span id="connStatusBadge"')
j=s.rfind('<img src="data:image/png;base64,',0,k)
s=s[:j]+'<img id="smTopLogo" '+s[j+5:]

# ---------- 7) رجسٹریشن فارم + برانڈنگ ----------
reg = r'''
<!-- 🥬 سبزی منڈی — پہلی بار: دکان کی رجسٹریشن -->
<div id="smRegOverlay" dir="rtl" style="display:none; position:fixed; inset:0; z-index:2147483000; background:linear-gradient(160deg,#065f46,#022c22); overflow:auto; font-family:'JameelNooriNastaleeqKasheeda','JameelNooriNastaleeq','Noto Nastaliq Urdu',serif;">
  <div style="max-width:420px; margin:28px auto; background:#fff; border-radius:20px; padding:18px 16px; box-shadow:0 10px 30px rgba(0,0,0,.35);">
    <div style="text-align:center; font-size:44px;">🥬</div>
    <div style="text-align:center; font-size:26px; font-weight:800; color:#065f46;">سبزی منڈی</div>
    <div style="text-align:center; font-size:15px; color:#475569; margin-bottom:12px;">اپنی دکان رجسٹر کریں</div>
    <label style="font-weight:800; color:#0f172a; font-size:15px;">🏪 دکان کا نام *</label>
    <input id="smRegShop" type="text" dir="rtl" placeholder="مثلاً رحمان سبزی منڈی" style="width:100%; box-sizing:border-box; padding:11px; margin:4px 0 10px; border:2px solid #86efac; border-radius:10px; font-family:inherit; font-size:17px;">
    <label style="font-weight:800; color:#0f172a; font-size:15px;">👤 مالک کا نام *</label>
    <input id="smRegOwner" type="text" dir="rtl" placeholder="مالک کا پورا نام" style="width:100%; box-sizing:border-box; padding:11px; margin:4px 0 10px; border:2px solid #86efac; border-radius:10px; font-family:inherit; font-size:17px;">
    <label style="font-weight:800; color:#0f172a; font-size:15px;">📱 مالک کا موبائل نمبر *</label>
    <input id="smRegPhone" type="tel" inputmode="numeric" dir="ltr" placeholder="03XXXXXXXXX" maxlength="13" style="width:100%; box-sizing:border-box; padding:11px; margin:4px 0 10px; border:2px solid #86efac; border-radius:10px; font-family:'Arial Black',Arial,sans-serif; font-size:18px; text-align:center;">
    <label style="font-weight:800; color:#0f172a; font-size:15px;">🖼️ دکان کی تصویر / لوگو <span style="font-size:12px; color:#64748b;">(اختیاری)</span></label>
    <div style="display:flex; align-items:center; gap:10px; margin:6px 0 14px;">
      <img id="smRegPhotoPrev" style="width:64px; height:64px; border-radius:14px; object-fit:cover; background:#f1f5f9; border:2px dashed #cbd5e1; display:block;" alt="">
      <label style="flex:1; text-align:center; padding:10px; background:#eef2ff; color:#1e3a8a; border-radius:10px; font-weight:800; cursor:pointer;">📷 تصویر لگائیں
        <input id="smRegPhoto" type="file" accept="image/*" style="display:none;" onchange="smRegPickPhoto(this)">
      </label>
    </div>
    <button type="button" onclick="smRegSave()" style="width:100%; padding:13px; border:none; border-radius:12px; background:linear-gradient(135deg,#16a34a,#065f46); color:#fff; font-family:inherit; font-size:19px; font-weight:800; cursor:pointer; box-shadow:0 4px 0 rgba(0,0,0,.25);">✅ رجسٹر کریں</button>
    <div style="text-align:center; font-size:12.5px; color:#64748b; margin-top:10px; line-height:1.9;">ابتدائی پن: <b dir="ltr">1234</b> — لاگ ان کے بعد سیٹنگز سے بدل لیں</div>
  </div>
</div>
<script>
let smRegPhotoData = '';
function smRegPickPhoto(inp){
  const f = inp.files && inp.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = () => {
    const img = new Image();
    img.onload = () => {
      const M = 256, sc = Math.min(1, M / Math.max(img.width, img.height));
      const c = document.createElement('canvas'); c.width = Math.round(img.width * sc); c.height = Math.round(img.height * sc);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      smRegPhotoData = c.toDataURL('image/jpeg', 0.85);
      document.getElementById('smRegPhotoPrev').src = smRegPhotoData;
    };
    img.src = r.result;
  };
  r.readAsDataURL(f);
}
function smApplyBranding(){
  const n = smBiz();
  document.title = n;
  const set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
  set('smTopTitle', n); set('smSideBrand', n); set('mobileBrandText', n); set('hbcBusinessName', n); set('smLoginShop', n);
  const logo = AppState.settings.shopLogoDataUrl;
  if(logo){ const im = document.getElementById('smTopLogo'); if(im) im.src = logo; }
}
function smRegSave(){
  const shop = document.getElementById('smRegShop').value.trim();
  const owner = document.getElementById('smRegOwner').value.trim();
  const phone = document.getElementById('smRegPhone').value.replace(/[^0-9]/g, '');
  if(!shop){ alert('دکان کا نام لکھیں'); return; }
  if(!owner){ alert('مالک کا نام لکھیں'); return; }
  if(!/^03\d{9}$/.test(phone)){ alert('درست موبائل نمبر لکھیں (03XXXXXXXXX)'); return; }
  AppState.settings.businessName = shop;
  AppState.settings.ownerName = owner;
  AppState.settings.businessPhone = phone;
  if(smRegPhotoData) AppState.settings.shopLogoDataUrl = smRegPhotoData;
  AppState.settings.smRegistered = true;
  AppState.settings.smRegisteredAt = new Date().toISOString();
  saveToStorage('settings', AppState.settings);
  try{
    const adm = usersData.find(u => u.role === 'admin');
    if(adm){ adm.name = owner; adm.phone = phone; saveToStorage('users', usersData); }
  }catch(e){}
  document.getElementById('smRegOverlay').style.display = 'none';
  smApplyBranding();
  try{ setupLoginScreen(); }catch(e){}
}
window.addEventListener('DOMContentLoaded', () => {
  smApplyBranding();
  if(!AppState.settings.smRegistered) document.getElementById('smRegOverlay').style.display = 'block';
});
</script>
'''
k=s.rindex('</body>')
s=s[:k]+reg+s[k:]
# لاگ ان سکرین پر دکان کا نام
rep('    <div id="loginVersionBadge"','    <div id="smLoginShop" style="text-align:center; color:#fff; font-size:22px; font-weight:800; margin:4px 0 8px; font-family:\'JameelNooriNastaleeqKasheeda\',\'JameelNooriNastaleeq\',serif; text-shadow:0 2px 4px rgba(0,0,0,.4);">سبزی منڈی</div>\n    <div id="loginVersionBadge"')
open(f'{OUT}/index.html','w',encoding='utf-8').write(s)

# ---------- 8) sw.js ----------
w=open(f'{SRC}/sw.js',encoding='utf-8').read()
w=re.sub(r"const CACHE_VERSION = '[^']*';", f"const CACHE_VERSION = '{VERSION}';", w, count=1)
w=w.replace('saddam-fruit-mandi-','sabzi-mandi-general-')  # کیش کا نام اور صفائی — دونوں صرف سبزی منڈی کے اپنے
w=w.replace("// ---------- 🏷️ صدام فروٹ منڈی — Service Worker ----------","// ---------- 🥬 سبزی منڈی (جنرل ایپ) — Service Worker ----------")
for f in ['favicon-32.png','icon-180.png','icon-192.png','icon-512.png','JameelNooriNastaleeq-Regular.ttf','JameelNooriNastaleeq-Kasheeda.ttf']:
    w=w.replace(f"'./{f}'", f"'../{f}'")
w=w.replace("'./fonts/","'../fonts/")
w=w.replace('صدام کی ہدایت','ہدایت').replace('صدام','مالک')
open(f'{OUT}/sw.js','w',encoding='utf-8').write(w)

# ---------- 9) manifest ----------
man={"name":"سبزی منڈی","short_name":"سبزی منڈی","start_url":"./","scope":"./","display":"standalone","background_color":"#065f46","theme_color":"#065f46","dir":"rtl","lang":"ur",
     "icons":[{"src":"../icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},{"src":"../icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}
open(f'{OUT}/manifest.json','w',encoding='utf-8').write(json.dumps(man,ensure_ascii=False,indent=2))
print('built', VERSION)
