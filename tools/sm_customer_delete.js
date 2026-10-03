/* SM110TH026 — کسٹمر پروفائل سے ڈیلیٹ (صرف ایڈمن): تصدیق 1 → تصدیق 2 → ایڈمن PIN → حذف
   build_general.py اسے index.html کے آخر میں خود لگاتا ہے؛ بٹن openCustomerProfile کے سائیڈ کالم میں سب سے نیچے */
async function deleteCustomerFromProfile(customerId){
  if(AppState.currentRole !== 'admin'){ alert('صرف ایڈمن کسٹمر ڈیلیٹ کر سکتا ہے'); return; }
  const c = customersData.find(x => x.customer_id === customerId);
  if(!c) return;
  const due = c.total_receivable || 0;
  const wal = c.wallet_balance || 0;
  const bills = (typeof invoicesData !== 'undefined' ? invoicesData : []).filter(i => i.customer_id === customerId).length;
  let info = `کسٹمر: ${c.name}`;
  if(due > 0) info += `\nاس سے آپ نے Rs. ${due.toLocaleString()} لینے ہیں`;
  if(wal > 0) info += `\nاس کا والٹ (ایڈوانس) Rs. ${wal.toLocaleString()} ہے`;
  if(bills > 0) info += `\nاس کے ${bills} بل ہیں`;
  // ---------- تصدیق 1 ----------
  if(!confirm(`⚠️ تصدیق 1/3\n\n${info}\n\nکیا آپ واقعی اس کسٹمر کو ڈیلیٹ کرنا چاہتے ہیں؟`)) return;
  // ---------- تصدیق 2 ----------
  if(!confirm(`❗ تصدیق 2/3\n\n"${c.name}" مکمل ڈیلیٹ ہو جائے گا اور دوبارہ واپس نہیں آئے گا۔${due > 0 ? '\n\n⚠️ اس کا بقایہ بھی ساتھ ختم ہو جائے گا۔' : ''}\n\nپکا ڈیلیٹ کرنا ہے؟`)) return;
  // ---------- تصدیق 3: ایڈمن پن ----------
  if(!(await confirmAdminPinForDelete(c.name))) return;
  // حفاظتی نقل: آخری 20 ڈیلیٹ شدہ کسٹمر فون میں رہتے ہیں (صرف ڈویلپر کی ریکوری کے لیے)
  try{
    const log = loadFromStorage('smDeletedCustomersLog', []) || [];
    log.push({ at: new Date().toISOString(), customer: JSON.parse(JSON.stringify(c, (k, v) => k === 'photo' ? undefined : v)) });
    saveToStorage('smDeletedCustomersLog', log.slice(-20));
  }catch(e){}
  try{ idbDeleteImage('customer_' + customerId); }catch(e){}
  customersData = customersData.filter(x => x.customer_id !== customerId);
  persistAllData();
  try{ pushCustomersToCloud(); }catch(e){}
  try{ pauseCloudPolling(20000); }catch(e){}
  closeProfileModal();
  try{ renderPartyList(document.getElementById('partySearchInput')?.value || ''); }catch(e){}
  alert(`🗑️ "${c.name}" ڈیلیٹ ہو گیا۔`);
}
