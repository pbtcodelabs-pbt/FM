# 🥬 سبزی منڈی (جنرل ایپ) — صدام والی ماسٹر فائل سے خودکار تیاری
import re, sys, json, os
import os.path as _p
# 🥬 استعمال (SM ریپو کی جڑ سے):
#   python3 tools/build_general.py <FM ریپو کا فولڈر> 'SM299TU#003'
# FM (صدام) کی index.html + sw.js پڑھتا ہے → SM ریپو کی جڑ میں index.html, sw.js, manifest.json لکھتا ہے
ROOT=_p.dirname(_p.dirname(_p.abspath(__file__)))
SRC=sys.argv[1]; OUT=ROOT
VERSION=sys.argv[2]
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
  // ---------- ☁️ سبزی منڈی کا اپنا فائربیس (sabzi-mandi-143e6) — صدام والا کبھی نہیں ----------
  // لائسنس/ٹرائل/ڈیوائس ہمیشہ کھلے؛ دکان کا ڈیٹا (shops/<موبائل>/…) صرف آن لائن پیکج (P1+1 سے اوپر) میں
  const of = window.fetch.bind(window);
  window.fetch = function(input, init){
    const u = (typeof input === 'string') ? input : (input && input.url) || '';
    if(/firestore\.googleapis\.com/.test(u) && /\/documents\/shops\//.test(u) && !smIsCloudPlan()){
      return Promise.resolve(new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } }));
    }
    return of(input, init);
  };
})();
function _smSettings(){ try{ return JSON.parse(localStorage.getItem('fmPos_settings') || '{}') || {}; }catch(e){ return {}; } }
// 📦 پیکج: P1 = صرف مالک (اکیلا صارف: فون + گوگل ڈرائیو)؛ P1+1 = مالک + 1 ملازم … P1+5 = مالک + 5 ملازم (آن لائن کلاؤڈ)
const SM_PLAN_STAFF = { 'P1': 0, 'P1+1': 1, 'P1+2': 2, 'P1+3': 3, 'P1+4': 4, 'P1+5': 5 };
const SM_PLAN_LEGACY = { P2: 'P1+1', P3: 'P1+2', P4: 'P1+3', P5: 'P1+4', P6: 'P1+5' }; // پرانے بنے کوڈ اب بھی چلیں
function smNormPlan(p){ p = String(p || '').trim(); if(SM_PLAN_LEGACY[p]) p = SM_PLAN_LEGACY[p]; return SM_PLAN_STAFF[p] !== undefined ? p : null; }
function smPlan(){ try{ return smNormPlan((typeof AppState !== 'undefined' && AppState.settings && AppState.settings.smPlan) || _smSettings().smPlan) || 'P1'; }catch(e){ return 'P1'; } }
function smIsCloudPlan(){ return (SM_PLAN_STAFF[smPlan()] || 0) > 0; }
function smShopMobile(){ try{ return ((typeof AppState !== 'undefined' && AppState.settings && AppState.settings.businessPhone) || _smSettings().businessPhone || 'unregistered').replace(/[^0-9]/g, '') || 'unregistered'; }catch(e){ return 'unregistered'; } }
function smMakeShopCode(){
  const A = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; let out = '';
  try{ const r = new Uint32Array(8); crypto.getRandomValues(r); for(let i = 0; i < 8; i++) out += A[r[i] % A.length]; }
  catch(e){ for(let i = 0; i < 8; i++) out += A[Math.floor(Math.random() * A.length)]; }
  return out;
}
function smShopCode(){
  try{
    const st = (typeof AppState !== 'undefined' && AppState.settings) ? AppState.settings : _smSettings();
    if(st.smShopCode) return st.smShopCode;
    if(st.smRegistered && !st.smJoinedAsStaff){ // پہلے سے رجسٹر دکان جس کے پاس ابھی کوڈ نہیں — ایک بار بنا کر محفوظ
      const c = smMakeShopCode(); st.smShopCode = c;
      try{ const raw = _smSettings(); raw.smShopCode = c; localStorage.setItem('fmPos_settings', JSON.stringify(raw)); }catch(e){}
      return c;
    }
  }catch(e){}
  return '';
}
function smShopBase(){ const c = smShopCode(); return 'shops/' + smShopMobile() + (c ? '-' + c : '') + '/data/'; }
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

# ---------- 1b) سبزی منڈی کا اپنا فائربیس ----------
s=re.sub(r"const FIREBASE_PROJECT_ID = '[^']*';", "const FIREBASE_PROJECT_ID = 'sabzi-mandi-143e6';", s, count=1)
s=re.sub(r"const FIREBASE_API_KEY = '[^']*';", "const FIREBASE_API_KEY = 'AIzaSyAfvu0JOHGgNzp9HEcRpCnE40jSN2X2n7w';", s, count=1)
# ---------- 1c) ہر دکان کا ڈیٹا الگ: shopData/ → shops/<موبائل>/data/ ----------
s=s.replace("'shopData/", "smShopBase() + '").replace("`shopData/", "`${smShopBase()}")
# ---------- 2) آئیکن `icons/` اور فونٹ `fonts/` فولڈر میں (صاف ستھرا ریپو) ----------
#    (FM210FR281 سے FM خود بھی icons/ اور fonts/ میں ہے — تب یہ قدم کچھ نہیں بدلتا، صرف تصدیق کرتا ہے)
for f in ['favicon-32.png','icon-180.png','icon-192.png']:
    if f'href="icons/{f}"' not in s: rep(f'href="{f}"', f'href="icons/{f}"')
for f in ['JameelNooriNastaleeq-Regular.ttf','JameelNooriNastaleeq-Kasheeda.ttf']:
    if f"url('./fonts/{f}')" not in s: rep(f"url('./{f}')", f"url('./fonts/{f}')")
    assert f"url('./fonts/{f}')" in s

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


# ---------- 4b) 🧹 نمونے (ڈیمو) کا سارا مواد ختم — نئی دکان بالکل خالی؛ مثالوں میں صرف ABC / XYZ اور کوئی رقم نہیں ----------
# منظوری کے منتظر نمونے کے بل (Aslam Bhai / Muhammad Usman / Walk-in / Lipton Tea) ہر لانچ پر نظر آتے تھے
a=s.index('let pendingBillsData = [')
b=s.index('\n];', a)+3
s=s[:a]+'let pendingBillsData = []; // 🥬 جنرل ایپ: کوئی نمونہ بل نہیں'+s[b:]
rep('let nextPendingId = 3;', 'let nextPendingId = 1;')
rep("loadFromStorage('nextCustomerId', 4)", "loadFromStorage('nextCustomerId', 1)")
rep("loadFromStorage('nextSupplierId', 3)", "loadFromStorage('nextSupplierId', 1)")
# امپورٹ ٹیمپلیٹ (CSV) کی مثالی قطاریں — اصلی لگنے والے نام نہیں
_CUST_ROWS = "'Aslam Bhai,03001234567,Main Bazaar,Lahore', 'Fatima Traders,03211234567,Shop 12 Anarkali,Lahore'"
_SUP_ROWS = "'Khalid Suppliers,03331234567,Warehouse Road,Karachi', 'Al-Madina Traders,03451234567,Wholesale Market,Faisalabad'"
assert _CUST_ROWS in s and _SUP_ROWS in s
s = s.replace(_CUST_ROWS, "'ABC,03000000001,Address,City', 'XYZ,03000000002,Address,City'")
s = s.replace(_SUP_ROWS, "'ABC,03000000001,Address,City', 'XYZ,03000000002,Address,City'")
_PROD_ROWS = "    'Lipton Tea,Beverages,1kg,8964000111,700,850,780,24,5,,Aisle 4',\n    'Lipton Tea,Beverages,500g,8964000112,360,450,410,40,10,,Aisle 4',\n    'Sugar,Grocery,Default,8964000200,140,160,150,100,20,,Warehouse-1',\n"
assert _PROD_ROWS in s
s = s.replace(_PROD_ROWS, "    'ABC,Category,Default,,0,0,0,0,0,,',\n    'XYZ,Category,Default,,0,0,0,0,0,,',\n")
for _o, _n in [('FM_Product_Import_Template','SM_Product_Import_Template'),('FM_Customer_Import_Template','SM_Customer_Import_Template'),('FM_Supplier_Import_Template','SM_Supplier_Import_Template')]:
    assert _o in s; s = s.replace(_o, _n)
# پرانے تبصروں میں صدام کے پروجیکٹ کا نام — بھی نہ رہے
s = s.replace('fm-saddam-mandi.web.app', 'other-project.web.app').replace('fm-saddam-mandi', 'other-project')

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
# ---------- ⚡ تیز اپڈیٹ ----------
rep("navigator.serviceWorker.register('./sw.js').then((reg) => {",
    "navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).then((reg) => {\n      document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible') reg.update().catch(()=>{}); });\n      window.addEventListener('focus', () => reg.update().catch(()=>{}));\n      setTimeout(() => reg.update().catch(()=>{}), 3000);")
rep("setInterval(() => { reg.update(); }, 60 * 1000);","setInterval(() => { reg.update().catch(()=>{}); }, 30 * 1000);")
for a_,b_ in [("acc.name || 'صدام حسین'","acc.name || smOwner()"),("'شکریہ — صدام حسین'","'شکریہ — ' + smBiz()"),
              ('صرف صدام حسین (ایڈمن)','صرف ایڈمن'),('صرف ایڈمن (صدام)','صرف ایڈمن'),('صدام حسین جلد','ایڈمن جلد'),
              ('صدام کو','ایڈمن کو'),('Powered by Saddam Fruit Mandi','Powered by Sabzi Mandi'),("name:'Saddam Hussain'","name:'مالک'"),
              ('Saddam Fruit Mandi','Sabzi Mandi'),('Saddam Hussain','Owner'),('صدام کی ہدایت','ہدایت'),('صدام حسین','مالک'),('صدام','مالک'),('Saddam','Owner')]:
    s=s.replace(a_,b_)
s=s.replace('<title>سبزی منڈی</title>','<title>سبزی منڈی</title>')

# ---------- 5a) ⏳ کوڈ بنتے وقت باریک پراگریس لائن (بٹن اور نتیجے کے ڈبے کے بیچ) ----------
_GEN_OLD = '<button class="testPrintBtn" style="background:#dcfce7; color:#15803d;" onclick="generateGiftCode()">🎁 Generate Code</button>'
_GEN_NEW = ('<button class="testPrintBtn" id="giftGenBtn" style="background:#dcfce7; color:#15803d;" onclick="generateGiftCode()">🎁 Generate Code</button>\n'
            '<div id="giftGenProgress" style="display:none; height:5px; margin:8px 2px 10px; border-radius:999px; background:#d1fae5; overflow:hidden;">'
            '<div id="giftGenProgressBar" style="height:100%; width:0%; background:linear-gradient(90deg,#16a34a,#22c55e); border-radius:999px; transition:width .25s ease;"></div></div>')
rep(_GEN_OLD, _GEN_NEW)
_A_OLD = "  const code = generateRandomGiftCode();\n\n  const fields = {"
_A_NEW = ("  const _gp = document.getElementById('giftGenProgress'), _gb = document.getElementById('giftGenProgressBar'), _gbtn = document.getElementById('giftGenBtn');\n"
          "  let _gt = null, _gw = 8;\n"
          "  if(_gp){ _gp.style.display = 'block'; _gb.style.width = '8%'; _gt = setInterval(() => { _gw = Math.min(90, _gw + (90 - _gw) * 0.18); _gb.style.width = _gw + '%'; }, 200); }\n"
          "  if(_gbtn){ _gbtn.disabled = true; _gbtn.style.opacity = '.65'; }\n"
          "  const code = generateRandomGiftCode();\n\n  const fields = {")
rep(_A_OLD, _A_NEW)
_B_OLD = ("    loadIssuedCodesList(); // ---------- نیا کوڈ فہرست میں فوراً نظر آ جائے ----------\n  }catch(e){\n"
          "    alert('⚠️ کوڈ نہیں بن سکا — انٹرنیٹ چیک کریں اور دوبارہ کوشش کریں۔ (' + e.message + ')');\n  }")
_B_NEW = ("    loadIssuedCodesList(); // ---------- نیا کوڈ فہرست میں فوراً نظر آ جائے ----------\n    if(_gb) _gb.style.width = '100%';\n  }catch(e){\n"
          "    if(_gb){ _gb.style.background = '#ef4444'; _gb.style.width = '100%'; }\n"
          "    alert('⚠️ کوڈ نہیں بن سکا — انٹرنیٹ چیک کریں اور دوبارہ کوشش کریں۔ (' + e.message + ')');\n  }\n"
          "  finally{\n    if(_gt) clearInterval(_gt);\n    if(_gbtn){ _gbtn.disabled = false; _gbtn.style.opacity = '1'; }\n"
          "    setTimeout(() => { if(_gp) _gp.style.display = 'none'; if(_gb){ _gb.style.width = '0%'; _gb.style.background = 'linear-gradient(90deg,#16a34a,#22c55e)'; } }, 900);\n  }")
rep(_B_OLD, _B_NEW)

# ---------- 5b) 📦 پیکج: P1 (صرف مالک)، P1+1 … P1+5 (مالک + 1…5 ملازم) ----------
i=s.index('<select id="giftCodeDaysInput"'); j=s.index('</select>', i)+len('</select>')
_PLAN_SEL = '\n<select id="giftCodePlanInput" style="width:100%; padding:9px; margin-bottom:8px; border:2px solid #16a34a; border-radius:8px; font-weight:800;"><option value="P1">📦 P1 — صرف مالک (اکیلا، گوگل ڈرائیو)</option><option value="P1+1">📦 P1+1 — مالک + 1 ملازم (آن لائن)</option><option value="P1+2">📦 P1+2 — مالک + 2 ملازم</option><option value="P1+3">📦 P1+3 — مالک + 3 ملازم</option><option value="P1+4">📦 P1+4 — مالک + 4 ملازم</option><option value="P1+5">📦 P1+5 — مالک + 5 ملازم</option></select>'
s=s[:j]+_PLAN_SEL+s[j:]
rep("  if(nameVal) fields.customerName = { stringValue: nameVal };", "  if(nameVal) fields.customerName = { stringValue: nameVal };\n  fields.plan = { stringValue: (document.getElementById('giftCodePlanInput') || {}).value || 'P1' }; // 📦 پیکج")
# کوڈ لگنے پر پیکج
k=s.index('async function activateSubscription(code){')
_k = "  const data = _parseFirestoreFields(doc.fields || {});"
k2=s.index(_k, k)+len(_k)
s=s[:k2]+"\n  if(data.plan){ try{ smSetPlan(data.plan); }catch(e){} } // 📦 پیکج"+s[k2:]
# ملازموں کی حد
rep("""  if(role === 'salesman' && screens.length === 0){""", r'''  { // 📦 پیکج کی حد
    const _lim = SM_PLAN_STAFF[smPlan()] || 0;
    const _cnt = usersData.filter(u => u.role !== 'admin' && u.role !== 'customer' && u.is_active !== false).length;
    if(role !== 'customer' && _cnt >= _lim){
      alert(_lim === 0 ? `📦 آپ کا پیکج P1 (صرف مالک) ہے — ملازم شامل نہیں ہو سکتے۔\n\nملازم کے لیے پیکج P1+1 یا اس سے اوپر لیں (ڈویلپر: 03206793793)۔`
        : `📦 آپ کے پیکج ${smPlan()} (مالک + ${_lim} ملازم) میں حد پوری ہو گئی۔\n\nمزید ملازم کے لیے پیکج بڑھائیں (ڈویلپر: 03206793793)۔`);
      return;
    }
  }
  if(role === 'salesman' && screens.length === 0){''')

# ---------- 5c) 🔁 بحالی: پیکج واپس + خوبصورت پیغام + "سبسکرپشن چیک" بٹن ----------
rep("async function _licFindByUid(uid){\n  let best = null;", "async function _licFindByUid(uid){\n  let best = null; let _maxPlan = null; const _licTodayStr = _smYMD(new Date());")
rep("if(d.subscriptionExpiry) best = { expiry: d.subscriptionExpiry, on: d.subscriptionActivatedOn || '', code: d.lastActivationCode || '' };",
    "if(d.subscriptionExpiry) best = { expiry: d.subscriptionExpiry, on: d.subscriptionActivatedOn || '', code: d.lastActivationCode || '', plan: d.smPlan || '' };")
rep("if(!best || exp > best.expiry) best = { expiry: exp, on, code };",
    "const _np = smNormPlan(d.plan) || 'P1'; if(exp >= _licTodayStr && (!_maxPlan || SM_PLAN_STAFF[_np] > SM_PLAN_STAFF[_maxPlan])) _maxPlan = _np;\n        if(!best || exp > best.expiry) best = { expiry: exp, on, code };")
rep("  return best;\n}\nlet _licRestoreBusy = null;", "  if(best && _maxPlan) best.plan = _maxPlan;\n  return best;\n}\nlet _licRestoreBusy = null;")
rep("_licApplyRestore(best.expiry, best.on, best.code);", "_licApplyRestore(best.expiry, best.on, best.code, best.plan);")
rep("function _licApplyRestore(expiryStr, activatedOn, code){\n", "function _licApplyRestore(expiryStr, activatedOn, code, plan){\n  try{ smAfterRestore(expiryStr, code, plan); }catch(e){} // 📦 پیکج بحال + خوبصورت پیغام\n")
i=s.index('function _licApplyRestore('); j=s.index('\n}\n', i)
s=s[:i]+s[i:j].replace('}, 1200);','}, 5200);')+s[j:]
rep("lastActivationCode: { stringValue: String(AppState.settings.lastActivationCode || '') },", "lastActivationCode: { stringValue: String(AppState.settings.lastActivationCode || '') }, smPlan: { stringValue: smPlan() },")
_pill = '<div id="loginSubStatus" style="display:inline-block; background:#eef2ff; border-radius:16px; padding:4px 14px; margin-bottom:6px; font-size:11px; font-weight:800; color:var(--primary-dark);"></div>'
rep(_pill, _pill + '\n    <div style="margin:0 0 8px;"><button type="button" id="smSubCheckBtn" onclick="smRefreshSubscription(this)" style="width:auto !important; margin:0 !important; padding:5px 14px !important; font-size:12px !important; border-radius:999px !important; background:#ecfdf5 !important; color:#065f46 !important; border:1.5px solid #6ee7b7 !important; font-weight:800; cursor:pointer; box-shadow:none !important;">🔄 سبسکرپشن چیک / تازہ کریں</button></div>\n    <div id="smSubCheckMsg" style="display:none;"></div>')
rep("${row('📅 ختم ہونے کی تاریخ', val(_bkEsc(expTxt)))}", "${row('📅 ختم ہونے کی تاریخ', val(_bkEsc(expTxt)))}\n    ${row('📦 پیکج', val(_bkEsc(smPlan())))}")
rep("function smBiz(){", r'''function smPlanText(p){ p = smNormPlan(p) || 'P1'; const n = SM_PLAN_STAFF[p]; return n === 0 ? 'صرف مالک' : ('مالک + ' + n + ' ملازم'); }
function smSetPlan(plan, quiet){
  const np = smNormPlan(plan); if(!np) return false;
  AppState.settings.smPlan = np;
  try{ saveToStorage('settings', AppState.settings); }catch(e){}
  try{ smApplyBranding(); }catch(e){}
  if(!quiet) setTimeout(() => { try{ smPushLicenseMirror(); }catch(e){} }, 3000);
  return true;
}
async function smFetchPlanForCode(code){
  try{
    const res = await fetch(`${FIRESTORE_BASE}/licenses/${encodeURIComponent(code)}?key=${FIREBASE_API_KEY}`);
    if(!res.ok) return null;
    const d = await res.json(); const np = smNormPlan(d.fields && d.fields.plan && d.fields.plan.stringValue);
    if(np) smSetPlan(np);
    return np;
  }catch(e){ return null; }
}
async function smAfterRestore(expiryStr, code, plan){
  let p = smNormPlan(plan);
  if(!p && code) p = await smFetchPlanForCode(code);
  if(p) smSetPlan(p);
  smShowRestoreCard(expiryStr, p || smPlan());
}
function smShowRestoreCard(expiryStr, plan){
  try{
    const days = Math.max(0, Math.round((new Date(expiryStr) - new Date()) / 86400000));
    const p = smNormPlan(plan) || 'P1';
    const old = document.getElementById('smRestoreCard'); if(old) old.remove();
    const el = document.createElement('div'); el.id = 'smRestoreCard';
    el.style.cssText = 'position:fixed; inset:0; z-index:2147483600; background:rgba(2,44,34,.8); display:flex; align-items:center; justify-content:center; padding:18px;';
    el.innerHTML = `<div dir="rtl" style="background:#fff; border-radius:22px; max-width:380px; width:100%; padding:22px 18px 18px; text-align:center; box-shadow:0 14px 44px rgba(0,0,0,.5); font-family:'JameelNooriNastaleeqKasheeda','JameelNooriNastaleeq',serif;">
      <div style="font-size:48px; line-height:1.2;">✅</div>
      <div style="font-size:22px; font-weight:900; color:#065f46; margin:4px 0 10px;">آپ کی سبسکرپشن بحال ہو گئی</div>
      <div style="font-size:16px; color:#334155; line-height:2;">آپ کی پرانی سبسکرپشن کے <b style="color:#15803d; font-family:Arial,sans-serif;">${days}</b> دن باقی ہیں۔<br>پیکج: <b style="font-family:Arial,sans-serif; color:#0f766e;">📦 ${p}</b> — ${smPlanText(p)}<br><span style="color:#0f766e; font-weight:900;">نیا کوڈ لگانے کی ضرورت نہیں</span><br>آپ کی ایپ کھل رہی ہے…</div>
      <button type="button" onclick="document.getElementById('smRestoreCard').remove()" style="margin-top:14px; width:auto !important; padding:8px 28px !important; border:none !important; border-radius:999px !important; background:#16a34a !important; color:#fff !important; font-size:15px !important; font-weight:800; cursor:pointer;">ٹھیک ہے</button>
    </div>`;
    document.body.appendChild(el);
    setTimeout(() => { try{ el.remove(); }catch(e){} }, 7000);
  }catch(e){}
}
async function smRefreshSubscription(btn){
  const label = btn ? btn.textContent : '';
  if(btn){ btn.disabled = true; btn.textContent = '⏳ چیک ہو رہا ہے…'; }
  let note = '';
  try{
    const uid = getOrCreateDeviceUID();
    const best = await _licFindByUid(uid);
    const today = _smYMD(new Date());
    if(best && best.expiry && best.expiry >= today){
      if(AppState.settings.isOnFreeTrial || !AppState.settings.subscriptionExpiry || best.expiry > AppState.settings.subscriptionExpiry){
        AppState.settings.subscriptionExpiry = best.expiry; AppState.settings.isOnFreeTrial = false;
        if(best.on) AppState.settings.subscriptionActivatedOn = best.on;
        if(best.code) AppState.settings.lastActivationCode = best.code;
        persistAllData();
      }
      if(best.plan) smSetPlan(best.plan, true); else if(best.code) await smFetchPlanForCode(best.code);
    }
    try{ setupLoginScreen(); }catch(e){}
    try{ renderLoginLicenseInfo(); }catch(e){}
    smApplyBranding();
    const days = daysLeftInSubscription();
    if(isSubscriptionActive()){
      note = AppState.settings.isOnFreeTrial
        ? '🎁 مفت آزمائش چل رہی ہے — ' + days + ' دن باقی'
        : '✅ آپ کی سبسکرپشن فعال ہے\n📦 پیکج ' + smPlan() + ' (' + smPlanText(smPlan()) + ')\n📅 ' + days + ' دن باقی';
    } else note = '⚠️ کوئی فعال سبسکرپشن نہیں ملی — کوڈ لگائیں یا ڈویلپر سے رابطہ کریں (03206793793)';
  }catch(e){ note = '⚠️ انٹرنیٹ چیک کریں اور دوبارہ کوشش کریں'; }
  const box = document.getElementById('smSubCheckMsg');
  if(box){
    box.style.cssText = 'display:block; margin:0 0 8px; background:#ecfdf5; border:1.5px solid #86efac; color:#065f46; border-radius:12px; padding:8px 12px; font-size:13px; font-weight:800; line-height:1.8; white-space:pre-line;';
    box.textContent = note;
    setTimeout(() => { try{ box.style.display = 'none'; }catch(e){} }, 9000);
  }
  if(btn){ btn.disabled = false; btn.textContent = label; }
}
function smBiz(){''')


# ---------- 5d) 📅 پورے دن (آج کا دن شامل نہیں) + باقی دن جمع + ≤6 دن پر سرخ چمکتی وارننگ ----------
# (الف) مقامی تاریخ — پہلے toISOString (UTC) تھا، رات/صبح سویرے ایک دن کم ہو جاتا تھا (30 کی جگہ 29)
for _old, _new in [
  ("new Date(Number(data.expiresAt)).toISOString().slice(0,10)", "_smYMD(new Date(Number(data.expiresAt)))"),
  ("new Date(Number(data.activatedAt)).toISOString().slice(0,10)", "_smYMD(new Date(Number(data.activatedAt)))"),
  ("new Date(ms).toISOString().slice(0, 10)", "_smYMD(new Date(ms))"),
  ("new Date(Number(d.activatedAt)).toISOString().slice(0, 10)", "_smYMD(new Date(Number(d.activatedAt)))"),
  ("AppState.settings.subscriptionActivatedOn = new Date().toISOString().slice(0,10);", "AppState.settings.subscriptionActivatedOn = _smYMD(new Date());"),
  ("AppState.settings.subscriptionExpiry = trialEnd.toISOString().slice(0,10);", "AppState.settings.subscriptionExpiry = _smYMD(trialEnd);"),
]:
    assert _old in s, _old
    s = s.replace(_old, _new)
# (ب) نیا کوڈ: باقی دن + نئے دن (6 + 30 = 36)، شروع آج کے بعد سے
rep("""  const hasActivePaidSub = isSubscriptionActive() && !AppState.settings.isOnFreeTrial;
  const base = hasActivePaidSub ? new Date(AppState.settings.subscriptionExpiry) : new Date();
  base.setDate(base.getDate() + daysNum);
  const newExpiryStr = base.toISOString().slice(0,10);""",
"""  // 📅 پورے دن: آج کا دن گنتی میں شامل نہیں (30 دن کا کوڈ = آج سے پورے 30 دن)؛ پرانے باقی دن بھی جمع (6 + 30 = 36)
  const hasActivePaidSub = isSubscriptionActive() && !AppState.settings.isOnFreeTrial;
  const carriedDays = hasActivePaidSub ? daysLeftInSubscription() : 0;
  const base = hasActivePaidSub ? _smParseYMD(AppState.settings.subscriptionExpiry) : (() => { const t = new Date(); t.setHours(0, 0, 0, 0); return t; })();
  base.setDate(base.getDate() + daysNum);
  const newExpiryStr = _smYMD(base);""")
rep("return {success:true, expiry: newExpiryStr, daysGranted: daysNum};", "return {success:true, expiry: newExpiryStr, daysGranted: daysNum, carried: carriedDays, totalDays: daysNum + carriedDays};")
# (ج) پیغامات (اردو، جمع شدہ دنوں کے ساتھ)
rep("msgEl.textContent = `✅ Activated! ${result.daysGranted} day(s) added — valid until ${result.expiry}. Opening app...`;", "msgEl.textContent = smActMsg(result) + ' ایپ کھل رہی ہے…';")
rep("msgEl.textContent = `✅ Activated! ${result.daysGranted} day(s) added — valid until ${result.expiry}.`;", "msgEl.textContent = smActMsg(result);")
# (د) سرخ چمکتی وارننگ: ہوم کی سبسکرپشن پٹی + لاگ ان کی پٹی
rep("function renderUserList(){", "function _origRenderUserList(){")
rep("function smBiz(){", "function renderUserList(){ _origRenderUserList.apply(this, arguments); try{ smRenderShopCodeRow(); }catch(e){} }\nfunction smBiz(){")
rep("function renderSubscriptionBanner(){", "function _origRenderSubscriptionBanner(){")
rep("function setupLoginScreen(){", "function _origSetupLoginScreen(){")
_css = '''<style id="smSubWarnCss">
@keyframes smSubGlow { 0%,100%{ box-shadow:0 0 6px 1px rgba(239,68,68,.55); } 50%{ box-shadow:0 0 20px 6px rgba(239,68,68,.95); } }
#subBoxRow.smSubWarn{ background:linear-gradient(135deg,#dc2626,#7f1d1d) !important; border:2px solid #fecaca !important; border-radius:14px !important; animation:smSubGlow 1.6s ease-in-out infinite; }
#subBoxRow.smSubWarn *:not(button){ background:transparent !important; color:#fff !important; font-weight:900 !important; border-color:transparent !important; text-shadow:0 1px 2px rgba(0,0,0,.4); }
#subBoxRow.smSubWarn #subBoxDaysVal{ font-size:1.12em !important; white-space:nowrap; }
#subBoxRow.smSubWarn{ flex-wrap:nowrap; overflow:hidden; }
#loginSubStatus.smSubWarn{ background:linear-gradient(135deg,#dc2626,#991b1b) !important; color:#fff !important; border:2px solid #fecaca !important; animation:smSubGlow 1.6s ease-in-out infinite; font-size:13.5px !important; font-weight:900 !important; padding:6px 16px !important; }
</style>
'''
s = s.replace("</head>", _css + "</head>", 1)  # صرف پہلا (اصل) head
rep("function smBiz(){", r'''function _smYMD(d){ const y = d.getFullYear(), m = String(d.getMonth() + 1).padStart(2, '0'), dd = String(d.getDate()).padStart(2, '0'); return y + '-' + m + '-' + dd; }
function _smParseYMD(str){ const p = String(str).split('-').map(Number); return new Date(p[0], (p[1] || 1) - 1, p[2] || 1); }
function smActMsg(r){
  if(r.restored) return '✅ سبسکرپشن بحال ہو گئی — ' + formatDateDMY(r.expiry) + ' تک۔';
  const tot = r.totalDays || r.daysGranted;
  return (r.carried > 0)
    ? '✅ ' + r.daysGranted + ' دن + پرانے ' + r.carried + ' دن = کل ' + tot + ' دن کی سبسکرپشن — ' + formatDateDMY(r.expiry) + ' تک۔'
    : '✅ ' + r.daysGranted + ' دن کی سبسکرپشن فعال — ' + formatDateDMY(r.expiry) + ' تک۔';
}
function smApplySubWarning(){
  try{
    const active = isSubscriptionActive();
    const days = active ? daysLeftInSubscription() : 99;
    const warn = active && days <= (AppState.settings.isOnFreeTrial ? 2 : 6);
    const row = document.getElementById('subBoxRow'), pill = document.getElementById('loginSubStatus');
    [row, pill].forEach(el => { if(el) el.classList.toggle('smSubWarn', warn); });
    if(pill && warn) pill.textContent = (days === 0) ? '⚠️ آج سبسکرپشن کا آخری دن ہے' : ('⚠️ ' + days + ' دن باقی — تجدید کروائیں');
  }catch(e){}
}
function renderSubscriptionBanner(){ _origRenderSubscriptionBanner(); smApplySubWarning(); }
async function setupLoginScreen(){ const r = await _origSetupLoginScreen.apply(this, arguments); try{ smApplySubWarning(); }catch(e){} return r; }
function smBiz(){''')


# ---------- 5e) 🔐 ملازم کوڈ — دکان کا خفیہ راستہ (موبائل + کوڈ)؛ بغیر کوڈ کوئی دکان سے نہیں جڑ سکتا ----------
rep('<div class="pageTitle">🔑 ملازمین</div>', '<div class="pageTitle">🔑 ملازمین</div>\n      <div id="smShopCodeRow" class="admin-only" style="display:none;"></div>')
rep("function renderSubscriptionBanner(){ _origRenderSubscriptionBanner(); smApplySubWarning(); }", "function renderSubscriptionBanner(){ _origRenderSubscriptionBanner(); smApplySubWarning(); }")
# 👔 ملازم کو سبسکرپشن پٹی نظر نہ آئے (صرف مالک)؛ "ہوم" اجازت کی فہرست سے ہٹ گئی (ہوم ہر ملازم کو ہمیشہ ملتا ہے، اس میں اس کی اجازت والی سکرینیں ہی نظر آتی ہیں)
if "AppState.currentRole !== 'admin'){ row.style.display = 'none'; return; }" not in s:  # FM110TH274 سے FM میں یہ جانچ پہلے ہی ہے
    rep("if(!isHomePage || !isSubscriptionActive()){ row.style.display = 'none'; return; }", "if(!isHomePage || !isSubscriptionActive() || AppState.currentRole !== 'admin'){ row.style.display = 'none'; return; }")
rep("const ASSIGNABLE_SCREENS = [\n  {key:'home', label:'🏠 ہوم'},\n", "const ASSIGNABLE_SCREENS = [\n")
rep("function smBiz(){", r'''function smFmtCode(c){ c = String(c || ''); return c.length > 4 ? c.slice(0, 4) + '-' + c.slice(4) : c; }
let _smCodeOpen = false;
function smToggleShopCode(){ _smCodeOpen = !_smCodeOpen; smRenderShopCodeRow(); }
function smRenderShopCodeRow(){
  const el = document.getElementById('smShopCodeRow'); if(!el) return;
  const act = document.querySelector('.screen.active');
  if(!(act && act.id === 'screen-users') || AppState.currentRole !== 'admin' || !smIsCloudPlan() || AppState.settings.smJoinedAsStaff){ el.style.display = 'none'; _smCodeOpen = false; return; }
  el.style.display = 'block';
  const bar = `<button type="button" onclick="smToggleShopCode()" style="width:100% !important; margin:4px 0 6px !important; padding:7px 12px !important; border-radius:12px !important; background:#ecfdf5 !important; color:#065f46 !important; border:1.5px solid #86efac !important; font-weight:800; font-size:13.5px !important; display:flex; justify-content:space-between; align-items:center; cursor:pointer; box-shadow:none !important;"><span>🔐 ملازم کے لیے نمبر + کوڈ</span><span style="font-size:12px;">${_smCodeOpen ? '▲ بند کریں' : '▼ دیکھیں / بھیجیں'}</span></button>`;
  const rowStyle = 'flex:1; font-family:Arial,sans-serif; font-weight:900; direction:ltr; text-align:center; background:#fff; border:1.5px dashed #34d399; border-radius:10px; padding:6px;';
  const box = `<div dir="rtl" style="margin:0 0 8px; background:#ecfdf5; border:1.5px solid #86efac; border-radius:12px; padding:8px 10px;">
    <div style="font-size:12px; font-weight:600; color:#475569;">نیا فون / نیا ملازم جوڑتے وقت یہ دونوں چیزیں بھیجیں — ملازم پورا پیغام کاپی کر کے "دکان سے جڑیں" میں پیسٹ کر دے، ہاتھ سے کچھ لکھنا نہیں۔</div>
    <div style="display:flex; gap:8px; margin-top:6px;"><span style="${rowStyle} font-size:11px; font-weight:700; flex:0 0 auto; border:none; background:transparent; align-self:center;">📱 رجسٹر نمبر</span><span style="${rowStyle} font-size:19px; letter-spacing:1px;">${smShopMobile()}</span></div>
    <div style="display:flex; gap:8px; margin-top:6px;"><span style="${rowStyle} font-size:11px; font-weight:700; flex:0 0 auto; border:none; background:transparent; align-self:center;">🔐 کوڈ</span><span style="${rowStyle} font-size:20px; letter-spacing:2px;">${smFmtCode(smShopCode())}</span></div>
    <div style="display:flex; gap:8px; margin-top:8px;">
      <button type="button" onclick="smCopyShopCode()" style="flex:1; width:auto !important; margin:0 !important; padding:9px 8px !important; border-radius:10px !important; background:#e0f2fe !important; color:#075985 !important; border:none !important; font-weight:800; cursor:pointer;">📋 نمبر + کوڈ کاپی</button>
      <button type="button" onclick="smShareShopCode()" style="flex:1; width:auto !important; margin:0 !important; padding:9px 8px !important; border-radius:10px !important; background:#dcfce7 !important; color:#166534 !important; border:none !important; font-weight:800; cursor:pointer;">📤 واٹس ایپ پر بھیجیں</button>
    </div></div>`;
  el.innerHTML = bar + (_smCodeOpen ? box : '');
}
function smShopCodeBlock(){ return 'دکان: ' + smBiz() + '\nموبائل: ' + smShopMobile() + '\nکوڈ: ' + smFmtCode(smShopCode()); }
function smShopCodeMessage(){
  const url = location.origin + location.pathname.replace(/index\.html$/, '');
  return 'سبزی منڈی ایپ — دکان سے جڑنے کے لیے:\n1) ایپ کھولیں: ' + url + '\n2) "📲 ملازم ہیں؟ دکان سے جڑیں" دبائیں\n3) یہ پورا پیغام کاپی کر کے وہاں پیسٹ کر دیں\n\n' + smShopCodeBlock();
}
async function smCopyShopCode(){
  const txt = smShopCodeBlock();
  try{ await navigator.clipboard.writeText(txt); alert('✅ موبائل نمبر اور کوڈ دونوں کاپی ہو گئے — ملازم کو بھیج دیں'); }
  catch(e){ prompt('پورا متن کاپی کر لیں:', txt); }
}
function smShareShopCode(){ window.open('https://wa.me/?text=' + encodeURIComponent(smShopCodeMessage()), '_blank'); }
// پیسٹ کیے متن سے نمبر اور کوڈ خود نکالیں (پیغام میں کچھ بھی اور لکھا ہو تو بھی)
function smParseJoinText(raw){
  const txt = String(raw || '').replace(/https?:\/\/\S+/g, ' ');
  let mobile = '', code = '';
  const m = txt.replace(/[\s\-]/g, '').match(/03\d{9}/);
  if(m) mobile = m[0];
  let cl = txt.match(/کوڈ\s*[:：]\s*([A-Za-z0-9\-\s]{8,12})/);
  if(cl){ code = cl[1].toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8); }
  if(code.length !== 8){
    const g = txt.replace(/[0-9]{3,}/g, ' ').match(/(?<![A-Za-z0-9])([A-Za-z2-9]{4})[-\s]?([A-Za-z2-9]{4})(?![A-Za-z0-9])/);
    code = g ? (g[1] + g[2]).toUpperCase() : '';
  }
  return { mobile, code };
}
function smBiz(){''')

# ---------- 5f) 👔 ملازم کے فون پر سبسکرپشن/دن/ایکسپائری بالکل نظر نہ آئے (صرف مالک کو)؛ ختم ہو تو صرف سادہ پیغام ----------
rep("function smBiz(){", r'''function smStaffCleanLogin(){
  try{
    if(!AppState.settings.smJoinedAsStaff) return;
    const active = isSubscriptionActive();
    const pill = document.getElementById('loginSubStatus');
    if(pill){
      pill.classList.remove('smSubWarn');
      if(active) pill.style.display = 'none';
      else { pill.style.display = ''; pill.textContent = '⚠️ دکان کی سبسکرپشن ختم ہے — مالک سے کہیں کہ تجدید کروائیں'; }
    }
    const chk = document.getElementById('smSubCheckBtn'); if(chk && chk.parentElement) chk.parentElement.style.display = 'none';
    ['smSubCheckMsg','smPlanBadge','loginLicenseInfoBox'].forEach(id => { const el = document.getElementById(id); if(el) el.style.display = 'none'; });
  }catch(e){}
}
function smStaffCleanGate(){
  try{
    if(!AppState.settings.smJoinedAsStaff) return;
    const g = document.getElementById('subscriptionGateScreen'); if(!g) return;
    const st = document.getElementById('subGateStatus');
    if(st) st.textContent = 'دکان کی سبسکرپشن ختم ہو چکی ہے۔ مالک سے کہیں کہ سبسکرپشن کی تجدید کروائیں، پھر نیچے "دوبارہ چیک کریں" دبائیں۔';
    g.querySelectorAll('input, label, .loginHint').forEach(el => { el.style.display = 'none'; });
    g.querySelectorAll('button').forEach(b => { const t = b.textContent || ''; if(/Activate/i.test(t)) b.style.display = 'none'; });
    const uid = document.getElementById('subGateUid'); if(uid && uid.parentElement) uid.parentElement.style.display = 'none';
    let rb = document.getElementById('smStaffRecheckBtn');
    if(!rb){
      rb = document.createElement('button'); rb.id = 'smStaffRecheckBtn'; rb.type = 'button'; rb.textContent = '🔄 دوبارہ چیک کریں';
      rb.style.cssText = 'margin-top:12px; width:100%; padding:11px; border:none; border-radius:10px; background:#16a34a; color:#fff; font-weight:800; font-size:15px; cursor:pointer;';
      rb.onclick = async () => { rb.textContent = '⏳ …'; const ok = await smPullLicenseMirror(); if(ok && isSubscriptionActive()) location.reload(); else { rb.textContent = '🔄 دوبارہ چیک کریں'; const m = document.getElementById('subGateMsg'); if(m){ m.style.color = '#b91c1c'; m.textContent = 'ابھی تک تجدید نہیں ہوئی۔'; } } };
      const box = g.querySelector('.loginBox'); if(box) box.appendChild(rb);
    }
  }catch(e){}
}
function smBiz(){''')
rep("async function setupLoginScreen(){ const r = await _origSetupLoginScreen.apply(this, arguments); try{ smApplySubWarning(); }catch(e){} return r; }",
    "async function setupLoginScreen(){ const r = await _origSetupLoginScreen.apply(this, arguments); try{ smApplySubWarning(); }catch(e){} try{ smStaffCleanLogin(); }catch(e){} return r; }")
rep("function showSubscriptionGate(){", "function _origShowSubscriptionGate(){")
rep("function smBiz(){", "function showSubscriptionGate(){ _origShowSubscriptionGate(); setTimeout(smStaffCleanGate, 50); setTimeout(smStaffCleanGate, 700); }\nfunction smBiz(){")

# ---------- 5g) 🏪 دکانوں کی رجسٹری (صرف ڈویلپر کے لیے) — ہر مالک کا فون کلاؤڈ میں اپنی دکان کی مختصر تفصیل رکھتا ہے ----------
# registry/<مالک کا موبائل>: دکان، مالک، پیکج، میعاد، ملازموں کے نام/یوزر نیم (PIN کبھی نہیں)، ورژن، آخری بار کب کھلی
# فائربیس Rules میں اس کا پڑھنا بند (read: false) — صرف فائربیس کنسول میں ڈویلپر کو نظر آتا ہے؛ لکھنا صرف ایپ سے
rep("function smBiz(){", r'''const SM_REGISTRY_CONSOLE = 'https://console.firebase.google.com/project/sabzi-mandi-143e6/firestore/databases/-default-/data/~2Fregistry';
async function smPushRegistry(){
  try{
    const st = AppState.settings;
    if(!st.smRegistered || st.smJoinedAsStaff || !navigator.onLine) return; // صرف مالک کا فون
    const mobile = smShopMobile(); if(!mobile || mobile === 'unregistered') return;
    const staff = usersData.filter(u => u.role !== 'admin' && u.role !== 'customer').map(u => ({ n: u.name, u: u.username || '', a: u.is_active !== false }));
    const f = {
      shop: { stringValue: smBiz() }, owner: { stringValue: smOwner() }, mobile: { stringValue: mobile },
      plan: { stringValue: smPlan() }, staffLimit: { integerValue: String(SM_PLAN_STAFF[smPlan()] || 0) },
      staffCount: { integerValue: String(staff.length) }, staff: { stringValue: JSON.stringify(staff) },
      expiry: { stringValue: st.subscriptionExpiry || '' }, trial: { booleanValue: !!st.isOnFreeTrial },
      activatedOn: { stringValue: st.subscriptionActivatedOn || '' }, code: { stringValue: st.lastActivationCode || '' },
      version: { stringValue: (typeof APP_BUILD_VERSION !== 'undefined') ? APP_BUILD_VERSION : '' },
      deviceUID: { stringValue: st.deviceUID || '' }, lastSeen: { integerValue: String(Date.now()) },
      registeredAt: { stringValue: st.smRegisteredAt || '' }
    };
    await authFirestoreFetch(`registry/${mobile}?key=${FIREBASE_API_KEY}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fields: f }) });
  }catch(e){}
}
setTimeout(() => { try{ smPushRegistry(); }catch(e){} }, 12000);
setInterval(() => { try{ smPushRegistry(); }catch(e){} }, 20 * 60 * 1000);
function smBiz(){''')
# smSetPlan کے بعد بھی (پیکج بدلنے پر فوراً)
rep("  if(!quiet) setTimeout(() => { try{ smPushLicenseMirror(); }catch(e){} }, 3000);\n  return true;", "  if(!quiet) setTimeout(() => { try{ smPushLicenseMirror(); smPushRegistry(); }catch(e){} }, 3000);\n  return true;")
# ڈویلپر پینل: ایک بٹن جو فائربیس کنسول میں رجسٹری کھولے
rep("      <!-- ---------- 🚧 ہدایت (25 ستمبر، دوپہر): مینٹیننس موڈ بٹن", """      <!-- ---------- 🏪 دکانوں کی رجسٹری ---------- -->
      <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:12px; padding:12px; margin-bottom:14px;" dir="rtl">
        <div style="font-size:12.5px; font-weight:800; color:#166534; margin-bottom:4px;">🏪 دکانوں کی فہرست</div>
        <div style="font-size:11px; color:#64748b; margin-bottom:8px; line-height:1.6;">ہر دکان: مالک، موبائل، پیکج، میعاد، ملازموں کے نام، ورژن، آخری بار کب کھلی۔ فائربیس میں کھلتی ہے (صرف آپ کے گوگل اکاؤنٹ سے)۔</div>
        <button type="button" onclick="window.open(SM_REGISTRY_CONSOLE, '_blank')" style="width:100%; padding:11px; border:none; border-radius:10px; background:#16a34a; color:#fff; font-weight:900; font-size:14px; cursor:pointer;">🏪 دکانوں کی فہرست کھولیں</button>
      </div>

      <!-- ---------- 🚧 ہدایت (25 ستمبر، دوپہر): مینٹیننس موڈ بٹن""")

# ---------- 6) ہیڈر عنوان / لوگو کو پہچان (id) ----------
rep('white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">سبزی منڈی</span>\n      <span id="connStatusBadge"',
    'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" id="smTopTitle">سبزی منڈی</span>\n      <span id="connStatusBadge"')
rep('<div class="brand">سبزی منڈی</div>','<div class="brand" id="smSideBrand">سبزی منڈی</div>')
k=s.index('<span id="connStatusBadge"')
j=s.rfind('<img src="data:image/png;base64,',0,k)
s=s[:j]+'<img id="smTopLogo" '+s[j+5:]

# ---------- 7) رجسٹریشن فارم + برانڈنگ ----------
reg = r'''
<style>
  /* 🥬 ورژن نمبر — صرف مالک کی پہچان کے لیے، مدھم (دکاندار کی توجہ نہ کھینچے) */
  #loginVersionBadge{ background:#15803d !important; color:#fff !important; box-shadow:none !important; border:none !important;
    padding:3px 12px !important; border-radius:999px !important; font-family:Arial,sans-serif !important; font-size:12px !important; font-weight:700 !important; letter-spacing:.4px; }
</style>
<!-- 🥬 سبزی منڈی — پہلی بار: دکان کی رجسٹریشن -->
<div id="smRegOverlay" dir="rtl" style="display:none; position:fixed; inset:0; z-index:2147483000; background:linear-gradient(160deg,#065f46,#022c22); overflow:auto; font-family:'JameelNooriNastaleeqKasheeda','JameelNooriNastaleeq','Noto Nastaliq Urdu',serif;">
  <style>
    #smRegOverlay .smWrap{ min-height:100dvh; box-sizing:border-box; padding:14px; display:flex; align-items:center; justify-content:center; }
    #smRegOverlay .smCard{ box-sizing:border-box; width:100%; max-width:420px; background:#fff; border-radius:18px; padding:14px 16px; box-shadow:0 10px 30px rgba(0,0,0,.35); display:flex; flex-direction:column; gap:10px; }
    #smRegOverlay label.smL{ display:block; font-weight:800; color:#0f172a; font-size:14px; margin:2px 0 2px; }
    #smRegOverlay input.smI{ width:100%; box-sizing:border-box; padding:9px 10px; margin:0; border:2px solid #86efac; border-radius:10px; font-family:inherit; font-size:16px; }
    #smRegOverlay .smPics{ display:flex; gap:8px; }
    #smRegOverlay .smPic{ flex:1; display:flex; align-items:center; gap:8px; background:#f8fafc; border:1.5px dashed #cbd5e1; border-radius:12px; padding:6px 8px; cursor:pointer; }
    #smRegOverlay .smPic img{ width:40px; height:40px; object-fit:cover; background:#e2e8f0; flex:0 0 auto; }
    #smRegOverlay .smPic b{ display:block; font-size:13px; color:#1e3a8a; line-height:1.6; }
    #smRegOverlay .smPicBtn{ flex:1; text-align:center; padding:6px 2px; background:#eef2ff; color:#1e3a8a; border-radius:9px; font-size:12.5px; font-weight:800; cursor:pointer; border:1px solid #c7d2fe; }
    #smRegOverlay .smPic small{ display:block; font-size:10.5px; color:#64748b; line-height:1.5; }
  </style>
  <div class="smWrap"><div class="smCard">
    <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
      <img src="icons/icon-192.png" alt="" style="width:58px; height:58px; border-radius:14px; box-shadow:0 4px 10px rgba(0,0,0,.25); object-fit:cover;">
      <div style="text-align:right;">
        <div style="font-size:24px; font-weight:800; color:#065f46; line-height:1.5;">سبزی منڈی</div>
        <div style="font-size:13px; color:#475569; line-height:1.6;">اپنی دکان رجسٹر کریں</div>
      </div>
    </div>
    <div>
      <label class="smL">🏪 دکان کا نام *</label>
      <input id="smRegShop" class="smI" type="text" dir="rtl" placeholder="مثلاً رحمان سبزی منڈی">
    </div>
    <div>
      <label class="smL">👤 مالک کا نام *</label>
      <input id="smRegOwner" class="smI" type="text" dir="rtl" placeholder="مالک کا پورا نام">
    </div>
    <div>
      <label class="smL">📱 مالک کا موبائل نمبر *</label>
      <input id="smRegPhone" class="smI" type="tel" inputmode="numeric" dir="ltr" placeholder="03XXXXXXXXX" maxlength="13" style="font-family:'Arial Black',Arial,sans-serif; font-size:17px; text-align:center;">
    </div>
    <div>
      <label class="smL">🖼️ تصویریں <span style="font-size:11px; color:#64748b; font-weight:400;">(اختیاری)</span></label>
      <div class="smPics">
        <div class="smPic" style="cursor:default; flex-direction:column; align-items:stretch; gap:5px;">
          <div style="display:flex; align-items:center; gap:8px;"><img id="smRegLogoPrev" alt="" style="border-radius:10px;"><span><b>🏪 دکان کا لوگو</b><small>بل، رسید، رپورٹ</small></span></div>
          <div style="display:flex; gap:5px;">
            <label class="smPicBtn">📷 کیمرہ<input type="file" accept="image/*" capture="environment" style="display:none;" onchange="smRegPick(this,'Logo')"></label>
            <label class="smPicBtn">🖼️ گیلری<input type="file" accept="image/*" style="display:none;" onchange="smRegPick(this,'Logo')"></label>
          </div>
        </div>
        <div class="smPic" style="cursor:default; flex-direction:column; align-items:stretch; gap:5px;">
          <div style="display:flex; align-items:center; gap:8px;"><img id="smRegOwnerPrev" alt="" style="border-radius:50%;"><span><b>👤 مالک کی تصویر</b><small>اوپر ہیڈر میں</small></span></div>
          <div style="display:flex; gap:5px;">
            <label class="smPicBtn">📷 کیمرہ<input type="file" accept="image/*" capture="user" style="display:none;" onchange="smRegPick(this,'Owner')"></label>
            <label class="smPicBtn">🖼️ گیلری<input type="file" accept="image/*" style="display:none;" onchange="smRegPick(this,'Owner')"></label>
          </div>
        </div>
      </div>
    </div>
    <div>
      <button type="button" onclick="smRegSave()" style="width:100%; padding:10px; border:none; border-radius:12px; background:linear-gradient(135deg,#16a34a,#065f46); color:#fff; font-family:inherit; font-size:18px; font-weight:800; cursor:pointer; box-shadow:0 4px 0 rgba(0,0,0,.25);">✅ رجسٹر کریں</button>
      <div style="display:flex; align-items:center; justify-content:center; gap:10px; margin-top:8px; flex-wrap:wrap;">
        <span style="font-size:12px; color:#64748b;">ابتدائی پن: <b dir="ltr">1234</b></span>
        <a href="javascript:void(0)" onclick="smJoinAsStaff()" style="font-size:12.5px; color:#1d4ed8; font-weight:800;">📲 ملازم ہیں؟ دکان سے جڑیں</a>
        <span id="smRegVersion" dir="ltr" style="display:inline-block; background:#15803d; color:#fff; font-family:Arial,sans-serif; font-size:12px; font-weight:700; letter-spacing:.4px; padding:3px 12px; border-radius:999px;"></span>
      </div>
    </div>
  </div></div>
</div>
<script>
const smRegImgs = { Logo: '', Owner: '' };
// ---------- تصویر چھوٹی کر کے (256px) محفوظ — ایپ ہلکی رہے ----------
function smShrinkImage(file, cb){
  const r = new FileReader();
  r.onload = () => {
    const img = new Image();
    img.onload = () => {
      const M = 256, sc = Math.min(1, M / Math.max(img.width, img.height));
      const c = document.createElement('canvas'); c.width = Math.round(img.width * sc); c.height = Math.round(img.height * sc);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      cb(c.toDataURL('image/jpeg', 0.85));
    };
    img.src = r.result;
  };
  r.readAsDataURL(file);
}
function smRegPick(inp, kind){
  const f = inp.files && inp.files[0]; if(!f) return;
  smShrinkImage(f, d => { smRegImgs[kind] = d; document.getElementById('smReg' + kind + 'Prev').src = d; });
}
// ---------- بعد میں بدلنا: ہیڈر کی تصویر پر ٹیپ (صرف ایڈمن) → مالک کی تصویر؛ لوگو "My Account" سے ----------
function smChangeOwnerPhoto(){
  if(!document.body.classList.contains('role-admin')) return;
  const useCam = confirm('📷 کیمرے سے نئی تصویر لینی ہے؟\n\nOK = کیمرہ   •   Cancel = گیلری سے چنیں');
  const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
  if(useCam) inp.setAttribute('capture', 'user');
  inp.onchange = () => { const f = inp.files && inp.files[0]; if(!f) return;
    smShrinkImage(f, d => { AppState.settings.ownerPhoto = d; saveToStorage('settings', AppState.settings); smApplyBranding(); }); };
  inp.click();
}
function smApplyBranding(){
  const n = smBiz();
  document.title = n;
  const set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
  set('smRegVersion', (typeof APP_BUILD_VERSION !== 'undefined') ? APP_BUILD_VERSION : '');
  set('smPlanBadge', '📦 ' + smPlan() + ' • ' + (smIsCloudPlan() ? 'مالک + ' + SM_PLAN_STAFF[smPlan()] + ' ملازم (آن لائن)' : 'صرف مالک — اکیلا صارف (گوگل ڈرائیو)'));
  set('smTopTitle', n); set('smSideBrand', n); set('mobileBrandText', n); set('hbcBusinessName', n); set('smLoginShop', n);
  const st = AppState.settings;
  const im = document.getElementById('smTopLogo');
  if(im){ im.src = st.ownerPhoto || st.businessLogo || 'icons/icon-192.png'; im.style.objectFit = 'cover'; im.style.cursor = 'pointer'; im.onclick = smChangeOwnerPhoto; }
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
  if(smRegImgs.Logo) AppState.settings.businessLogo = smRegImgs.Logo;
  if(smRegImgs.Owner) AppState.settings.ownerPhoto = smRegImgs.Owner;
  AppState.settings.smRegistered = true;
  AppState.settings.smRegisteredAt = new Date().toISOString();
  if(!AppState.settings.smShopCode && !AppState.settings.smJoinedAsStaff) AppState.settings.smShopCode = smMakeShopCode(); // 🔐 دکان کا خفیہ کوڈ
  saveToStorage('settings', AppState.settings);
  try{
    const adm = usersData.find(u => u.role === 'admin');
    if(adm){ adm.name = owner; adm.phone = phone; saveToStorage('users', usersData); }
  }catch(e){}
  document.getElementById('smRegOverlay').style.display = 'none';
  smApplyBranding();
  setTimeout(() => location.reload(), 300); // دکان کا کلاؤڈ راستہ (موبائل نمبر) نئے سرے سے بنے
}
// ---------- 📲 ملازم کا فون: پہلے سے رجسٹر دکان سے جڑیں (مالک کا موبائل نمبر) ----------
async function smJoinAsStaff(){
  const raw = prompt('📋 مالک کا بھیجا ہوا پیغام (موبائل نمبر + کوڈ) کاپی کر کے یہاں پیسٹ کر دیں۔\n\n(واٹس ایپ میں پیغام پر دبا کر رکھیں ← Copy)');
  if(raw === null) return;
  let { mobile: m, code: c } = smParseJoinText(raw);
  if(!m){ m = (prompt('📲 مالک کا موبائل نمبر لکھیں (03XXXXXXXXX):') || '').replace(/[^0-9]/g, ''); }
  if(!/^03\d{9}$/.test(m)){ if(m) alert('درست موبائل نمبر نہیں ملا — مالک کا پورا پیغام کاپی کر کے پیسٹ کریں'); return; }
  if(!c || c.length !== 8){ c = (prompt('🔐 ملازم کا کوڈ لکھیں (مثلاً K7M2-9QXP):') || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); }
  if(c.length !== 8){ if(c) alert('کوڈ درست نہیں — 8 حروف/ہندسے ہونے چاہییں'); return; }
  const prev = { p: AppState.settings.businessPhone, c: AppState.settings.smShopCode, r: AppState.settings.smRegistered, j: AppState.settings.smJoinedAsStaff, pl: AppState.settings.smPlan };
  AppState.settings.businessPhone = m; AppState.settings.smShopCode = c; AppState.settings.smRegistered = true; AppState.settings.smJoinedAsStaff = true;
  AppState.settings.smPlan = 'P1+1';
  saveToStorage('settings', AppState.settings);
  const ok = await smPullLicenseMirror();
  if(!ok){
    alert('❌ نمبر یا کوڈ غلط ہے، یا مالک کا پیکج آن لائن (P1+1 یا اس سے اوپر) نہیں۔\n\nمالک کے فون پر "🔑 ملازمین" سکرین کھول کر "📋 نمبر + کوڈ کاپی" دبائیں اور وہی پیغام پیسٹ کریں۔');
    AppState.settings.businessPhone = prev.p; AppState.settings.smShopCode = prev.c; AppState.settings.smRegistered = prev.r; AppState.settings.smJoinedAsStaff = prev.j; AppState.settings.smPlan = prev.pl;
    saveToStorage('settings', AppState.settings); return;
  }
  // 🧑‍💼 SM210FR036: یہ فون اب ملازم کا — پرانی دکان کا "فون کا مالک"/یاد رکھا ایڈمن سیشن/فنگر پرنٹ صاف، تاکہ ایڈمن کا خانہ نہ کھلے
  try{ localStorage.removeItem('fm_phoneOwner'); }catch(e){}
  try{ localStorage.removeItem('fm_bioCred'); }catch(e){}
  try{ saveToStorage('rememberedSession', null); }catch(e){}
  location.reload();
}
// ---------- 🔁 لائسنس آئینہ: مالک کا فون پیکج/مدت دکان کے کلاؤڈ میں رکھتا ہے، ملازم کا فون وہیں سے لیتا ہے ----------
async function smPushLicenseMirror(){
  if(!smIsCloudPlan() || AppState.currentRole === 'salesman' || AppState.settings.smJoinedAsStaff) return;
  try{
    await authFirestoreFetch(`${smShopBase()}license?key=${FIREBASE_API_KEY}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields: { plan: { stringValue: smPlan() }, expiry: { stringValue: AppState.settings.subscriptionExpiry || '' }, shop: { stringValue: smBiz() }, owner: { stringValue: smOwner() }, updatedAt: { integerValue: String(Date.now()) } } }) });
  }catch(e){}
}
async function smPullLicenseMirror(){
  try{
    const res = await authFirestoreFetch(`${smShopBase()}license?key=${FIREBASE_API_KEY}`, { cache: 'no-store' });
    if(!res || !res.ok) return false;
    const d = await res.json(); const f = d.fields || {};
    const plan = f.plan?.stringValue, exp = f.expiry?.stringValue;
    const np = smNormPlan(plan); if(!np || !SM_PLAN_STAFF[np]) return false;
    AppState.settings.smPlan = np;
    if(exp){ AppState.settings.subscriptionExpiry = exp; AppState.settings.isOnFreeTrial = false; }
    if(f.shop?.stringValue) AppState.settings.businessName = f.shop.stringValue;
    if(f.owner?.stringValue) AppState.settings.ownerName = f.owner.stringValue;
    saveToStorage('settings', AppState.settings);
    return true;
  }catch(e){ return false; }
}
window.addEventListener('load', () => {
  setTimeout(() => { try{ if(AppState.settings.smJoinedAsStaff) smPullLicenseMirror().then(ok => { if(ok) smApplyBranding(); }); else smPushLicenseMirror(); }catch(e){} }, 6000);
});
window.addEventListener('DOMContentLoaded', () => {
  smApplyBranding();
  if(!AppState.settings.smRegistered) document.getElementById('smRegOverlay').style.display = 'block';
});
</script>
'''
k=s.rindex('</body>')
s=s[:k]+reg+s[k:]
# لاگ ان سکرین پر دکان کا نام
k=s.index('<div id="loginScreen">'); k2=s.index('>🥬</div>',k)
k1=s.rfind('<div style="width:56px;',k,k2)
s=s[:k1]+'<img src="icons/icon-192.png" alt="" style="display:block; width:64px; height:64px; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,.35); object-fit:cover; margin:0 auto 6px;">'+s[k2+len('>🥬</div>'):]
rep('    <div id="loginVersionBadge"','    <div id="smPlanBadge" style="text-align:center; color:#fde68a; font-size:12.5px; font-weight:800; margin:0 0 6px; font-family:Arial,sans-serif;"></div>\n    <div id="smLoginShop" style="text-align:center; color:#fff; font-size:22px; font-weight:800; margin:4px 0 8px; font-family:\'JameelNooriNastaleeqKasheeda\',\'JameelNooriNastaleeq\',serif; text-shadow:0 2px 4px rgba(0,0,0,.4);">سبزی منڈی</div>\n    <div id="loginVersionBadge"')

# ---------- 🔐🧹 SM110TH022 حفاظتی صفائی (ہر بلڈ پر خود لگتی ہے) ----------
# 1) ڈویلپر پاسورڈ: FM210FR276 سے دونوں ایپس میں ایک ہی ماسٹر ڈویلپر پاسورڈ — FM سے ہی آتا ہے، یہاں کچھ نہیں بدلنا
#    (پاسورڈ صرف مالک کے پاس — ریپو/نوٹس میں کبھی نہ لکھیں؛ کوڈ میں صرف ہیش)۔ ایڈمن PIN والا ڈویلپر بائی پاس FM میں ہی ختم ہو چکا
assert 'DEV_BYPASS_PIN = ' not in s, 'FM میں پرانا ڈویلپر بائی پاس واپس آ گیا'
# 2) URL سے ڈویلپر پاسورڈ ری سیٹ کا خفیہ لنک ختم (سورس میں سب کو نظر آتا تھا)
_a=s.find("if(p.get('devpwreset') === 'saddamFM19reset'){")
if _a!=-1:
    _b=s.find('}\n', s.find("400);", _a))
    s=s[:_a]+"/* devpwreset ہٹا دیا گیا */"+s[_b+1:]
# 3) گاہک کو جانے والے پیغامات/نام میں فروٹ منڈی نہیں
s=s.replace('میں فروٹ منڈی ایپ','میں سبزی منڈی ایپ')
s=s.replace('Fruit_Mandi_POS_ad_poster.png','Sabzi_Mandi_POS_ad_poster.png')
s=s.replace('https://username.github.io/FruitMandiPOS/','https://username.github.io/SM/')
# ---------- ☁️ SM110TH026: نیا گوگل ڈرائیو بیک اپ نظام (tools/sm_backup_v2.js) ----------
_old="setTimeout(checkScheduledAutoBackup, 8000);\nsetInterval(checkScheduledAutoBackup, 10 * 60 * 1000);"
if s.count(_old)==1: s=s.replace(_old,"/* پرانا شیڈولر بند — نیا نظام آخر میں */")
_js=open(_p.join(ROOT,'tools','sm_backup_v2.js'),encoding='utf-8').read()
_k=s.rindex('</body>')
s=s[:_k]+'<script>\n/* SM_BACKUP_V2_BEGIN */\n'+_js+'\n/* SM_BACKUP_V2_END */\n</script>\n'+s[_k:]
# ---------- SM110TH026: LEGACY_DEMO_CUSTOMERS کی تعریف (صفائی میں ہٹ جاتی تھی، کسٹمر سنک ایرر دیتا تھا) ----------
if 'const LEGACY_DEMO_CUSTOMERS' not in s:
    rep("function isLegacyDemoCustomer(c){\n  return !!c && LEGACY_DEMO_CUSTOMERS.some(", "const LEGACY_DEMO_CUSTOMERS = [];\nfunction isLegacyDemoCustomer(c){\n  return !!c && LEGACY_DEMO_CUSTOMERS.some(")
# ---------- SM110TH026: کسٹمر پروفائل میں Delete بٹن (tools/sm_customer_delete.js) ----------
rep("<span class=\"sideIcon\">📜</span><span class=\"sideLabel\">Transactions</span></button>\n  `;\n\n  renderCustomerMainContent(c.customer_id);",
    "<span class=\"sideIcon\">📜</span><span class=\"sideLabel\">Transactions</span></button>\n    ${AppState.currentRole === 'admin' ? `<button style=\"background:linear-gradient(155deg,#dc2626,#7f1d1d);\" onclick=\"deleteCustomerFromProfile(${c.customer_id})\"><span class=\"sideIcon\">🗑️</span><span class=\"sideLabel\">Delete</span></button>` : ''}\n  `;\n\n  renderCustomerMainContent(c.customer_id);")
_js2=open(_p.join(ROOT,'tools','sm_customer_delete.js'),encoding='utf-8').read()
_k2=s.rindex('</body>')
s=s[:_k2]+'<script>\n/* SM_CUSTOMER_DELETE_BEGIN */\n'+_js2+'\n/* SM_CUSTOMER_DELETE_END */\n</script>\n'+s[_k2:]
# ---------- 🧑‍💼 SM210FR036: ملازم کے طور پر جڑے فون پر لاگ ان میں صرف ملازم کا خانہ (ایڈمن کا نہیں) ----------
rep("function applyLoginDeviceLock(){", r"""function applyLoginDeviceLock(){
  _origApplyLoginDeviceLock();
  // 🧑‍💼 SM210FR036: جو فون "دکان سے جڑیں" سے ملازم بنا، اس پر ایڈمن کا خانہ نہیں — صرف ملازم کا (7 ٹیپ سے سب خانے پھر بھی کھل سکتے ہیں)
  try{
    if(!(AppState.settings && AppState.settings.smJoinedAsStaff) || _loginShowAll) return;
    const rows = document.querySelectorAll('#loginPinWrap > .loginRoleRow');
    const adminRow = rows[0], staffRow = rows[1];
    if(!adminRow || !staffRow) return;
    const o = _phoneOwnerUser();
    if(o && o.role === 'salesman') return; // پہلے سے اپنے نام پر لاک
    adminRow.style.display = 'none'; staffRow.style.display = '';
  }catch(e){}
}
function _origApplyLoginDeviceLock(){""")
# ---------- 🧑‍💼 SM210FR036: ملازم کے فون پر کبھی خودکار ایڈمن لاگ ان نہیں (نہ PIN Lock بند ہونے سے، نہ پرانے یاد رکھے سیشن سے) ----------
rep("  if(AppState.settings.pinLockEnabled === false){\n    const adminUser = usersData.find(u => u.role === 'admin' && u.is_active);",
    "  if(AppState.settings.pinLockEnabled === false && !AppState.settings.smJoinedAsStaff){ // 🧑‍💼 SM210FR036\n    const adminUser = usersData.find(u => u.role === 'admin' && u.is_active);")
rep("  try{ _migratePhoneOwner(); if(user && !isPhoneOwnerUser(user)){ saveToStorage('rememberedSession', null); return false; } }catch(e){}",
    "  if(user && user.role === 'admin' && AppState.settings.smJoinedAsStaff){ saveToStorage('rememberedSession', null); return false; } // 🧑‍💼 SM210FR036\n  try{ _migratePhoneOwner(); if(user && !isPhoneOwnerUser(user)){ saveToStorage('rememberedSession', null); return false; } }catch(e){}")
# ---------- 🧑‍💼 SM210FR037: ملازم فون پر پرانا "ایڈمن فون کا مالک" نہ رہے — ورنہ ملازم کا لاگ ان عارضی سمجھا جاتا اور ریفریش پر لاگ آؤٹ ہوتا ----------
rep("""function _migratePhoneOwner(){
  try{
    if(getPhoneOwner()) return;
    const users = (usersData || []).filter(u => u.is_active);
    const adminSign = !!(AppState.settings && (AppState.settings.lastGDriveBackupAt || AppState.settings.gdriveAccountEmail));
    if(adminSign){""", """function _migratePhoneOwner(){
  try{
    // 🧑‍💼 SM210FR037: "دکان سے جڑیں" والے ملازم فون پر پرانی دکان کا ایڈمن "فون کا مالک" نہ رہے
    if(AppState.settings && AppState.settings.smJoinedAsStaff){ const _o = getPhoneOwner(); if(_o && _o.role === 'admin'){ try{ localStorage.removeItem('fm_phoneOwner'); }catch(e){} } }
    if(getPhoneOwner()) return;
    const users = (usersData || []).filter(u => u.is_active);
    const adminSign = !!(AppState.settings && (AppState.settings.lastGDriveBackupAt || AppState.settings.gdriveAccountEmail)) && !(AppState.settings && AppState.settings.smJoinedAsStaff);
    if(adminSign){""")
open(f'{OUT}/index.html','w',encoding='utf-8').write(s)

# ---------- 8) sw.js ----------
w=open(f'{SRC}/sw.js',encoding='utf-8').read()
w=re.sub(r"const CACHE_VERSION = '[^']*';", f"const CACHE_VERSION = '{VERSION}';", w, count=1)
w=w.replace('saddam-fruit-mandi-','sabzi-mandi-general-')  # کیش کا نام اور صفائی — دونوں صرف سبزی منڈی کے اپنے
w=w.replace("// ---------- 🏷️ صدام فروٹ منڈی — Service Worker ----------","// ---------- 🥬 سبزی منڈی (جنرل ایپ) — Service Worker ----------")
for f in ['favicon-32.png','icon-180.png','icon-192.png','icon-512.png']:
    w=w.replace(f"'./{f}'", f"'./icons/{f}'")
for f in ['JameelNooriNastaleeq-Regular.ttf','JameelNooriNastaleeq-Kasheeda.ttf']:
    w=w.replace(f"'./{f}'", f"'./fonts/{f}'")
w=w.replace('صدام کی ہدایت','ہدایت').replace('صدام','مالک')
w=w.replace("if (req.method !== 'GET') return;", "if (req.method !== 'GET') return;\n  // SM110TH026: privacy/terms pages are plain pages, never served from the app cache\n  if (/\\/(privacy|terms)\\.html$/.test(new URL(req.url).pathname)) return;", 1)
open(f'{OUT}/sw.js','w',encoding='utf-8').write(w)

# ---------- 9) manifest ----------
man={"name":"سبزی منڈی","short_name":"سبزی منڈی","start_url":"./index.html","scope":"./","orientation":"portrait","description":"سبزی منڈی — بلنگ اور حساب کتاب","display":"standalone","background_color":"#065f46","theme_color":"#065f46","dir":"rtl","lang":"ur",
     "icons":[{"src":"icons/favicon-32.png","sizes":"32x32","type":"image/png"},{"src":"icons/icon-180.png","sizes":"180x180","type":"image/png","purpose":"any"},{"src":"icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},{"src":"icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}
open(f'{OUT}/manifest.json','w',encoding='utf-8').write(json.dumps(man,ensure_ascii=False,indent=2))
print('built', VERSION)
