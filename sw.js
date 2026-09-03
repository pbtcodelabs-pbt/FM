// ======================================================================
// 🔄 Fruit Mandi POS — Service Worker
// مقصد: (1) آف لائن بھی ایپ کھلے اور کام کرے (2) Home Screen پر Add
// کرنے پر یہ ایک اصلی PWA کی طرح برتاؤ کرے (3) نیا ورژن اپلوڈ ہونے پر
// یوزر کو اپڈیٹ کا ٹوسٹ نظر آئے (یہ index.html میں پہلے سے موجود ہے)
//
// ⚠️ ضروری: جب بھی آپ index.html (یا کوئی اور فائل) میں تبدیلی کر کے
// دوبارہ اپلوڈ کریں، نیچے دیا گیا CACHE_VERSION نمبر ایک بڑھا دیں
// (v1 → v2 → v3...) — ورنہ براؤزر یہ نہیں سمجھ پائے گا کہ نیا ورژن آیا
// ہے، اور صارف کو پرانی، کیش شدہ فائل ہی ملتی رہے گی۔
// ======================================================================

// ⚠️ ضروری: یہ ورژن نمبر ہمیشہ index.html کے اندر موجود APP_BUILD_VERSION
// کے بالکل برابر ہونا چاہیے (اور فائل کے نام کے ساتھ بھی ملتا ہو، مثلاً
// FM318MO13.html) — جب بھی نئی فائل بھیجیں، یہاں بھی وہی نیا نمبر ڈال دیں۔
// اسی ایک تبدیلی سے براؤزر خود بخود سمجھ جائے گا کہ نیا ورژن آیا ہے،
// پرانی کیش صاف کر دے گا، اور صارف کو اپڈیٹ کا ٹوسٹ نظر آئے گا۔
//
// 📌 قاعدہ (ہر نئی چیٹ میں بھی یہی فالو کریں): فارمیٹ FM{تاریخ}{مہینہ}{دن کوڈ}{سیریل}
// — اسی دن کے اندر ہر نئی فائل پر سیریل نمبر ایک آگے بڑھائیں (12 → 13 → 14...)،
// اور جیسے ہی نئی تاریخ شروع ہو تو سیریل واپس 01 سے شروع کریں۔ مکمل تفصیل index.html
// میں APP_BUILD_VERSION کے اوپر والے کمنٹ میں موجود ہے۔

const CACHE_VERSION = 'FM3SEPTH25';
const CACHE_NAME = `fruit-mandi-pos-${CACHE_VERSION}`;

// ---------- یہ فائلیں انسٹال کے وقت ہی محفوظ کر لی جائیں گی — آف لائن پہلی بار کھلنے کے لیے ضروری ----------
const PRECACHE_URLS = [
  './',
  './index.html',
  './manifest.json',
  './favicon-32.png',
  './icon-180.png',
  './icon-192.png',
  './icon-512.png',
  './JameelNooriNastaleeq-Regular.ttf',
  './JameelNooriNastaleeq-Kasheeda.ttf',
  './PDMS_Multan_Regular.ttf'
];

// ---------- 📦 INSTALL: بنیادی فائلیں کیش میں رکھ دیں — ہر فائل الگ سے، تاکہ اگر کوئی ایک فائل
// (مثلاً کوئی فونٹ ابھی سرور پر اپلوڈ نہ ہوئی ہو) نہ ملے تو باقی ساری کیشنگ پھر بھی چلتی رہے ----------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(
        PRECACHE_URLS.map((url) =>
          cache.add(url).catch((err) => console.warn('[SW] precache میں یہ فائل نہیں ملی، نظرانداز کر دی:', url, err))
        )
      )
    )
  );
  // ---------- نوٹ: یہاں خود بخود skipWaiting نہیں بلاتے — index.html کا اپنا
  // "Update" ٹوسٹ سسٹم صارف کی مرضی سے (بٹن دبانے پر) نیا ورژن فعال کرتا ہے ----------
});

// ---------- 🧹 ACTIVATE: پرانے ورژن کی کیشز صاف کریں ----------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------- 📡 FETCH: HTML کے لیے "Network First" (آن لائن ہو تو ہمیشہ تازہ ترین)،
// باقی فائلوں (آئیکنز/manifest) کے لیے "Cache First" (تیز اور کم ڈیٹا خرچ) ----------
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if(req.method !== 'GET') return; // ---------- POST/PUT وغیرہ (جیسے Firestore کالز) کبھی کیش نہ ہوں ----------

  const url = new URL(req.url);
  // ---------- صرف اسی اوریجن کی فائلیں ہینڈل کریں — Firestore/گوگل فونٹس وغیرہ باہر جانے دیں (نیٹ ورک پر ہی چھوڑ دیں) ----------
  if(url.origin !== self.location.origin){
    return;
  }

  const isHTML = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');

  if(isHTML){
    // ---------- Network First: آن لائن ہو تو تازہ index.html لائیں اور کیش بھی اپڈیٹ کر دیں؛
    // آف لائن ہو تو کیش سے دکھا دیں (ایپ بند نہیں ہوگی) ----------
    event.respondWith(
      fetch(req)
        .then((res) => {
          const resClone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
          return res;
        })
        .catch(() => caches.match(req).then((cached) => cached || caches.match('./index.html')))
    );
    return;
  }

  // ---------- باقی سب (icons, manifest, وغیرہ): پہلے کیش، نہ ملے تو نیٹ ورک سے لا کر کیش کر لیں ----------
  event.respondWith(
    caches.match(req).then((cached) => {
      if(cached) return cached;
      return fetch(req).then((res) => {
        const resClone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
        return res;
      }).catch(() => cached);
    })
  );
});

// ---------- ⏭️ index.html میں موجود "ابھی اپڈیٹ کریں" بٹن یہی پیغام بھیجتا ہے ----------
self.addEventListener('message', (event) => {
  if(event.data === 'SKIP_WAITING'){
    self.skipWaiting();
  }
});
