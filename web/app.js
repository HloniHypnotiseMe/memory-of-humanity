const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function get(path){const r=await fetch(path);const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}

async function bootstrap(){
 const id=$('contributor').value.trim();
 const existing=await get('/api/identities');
 if(!existing.identities.some(x=>x.id===id))await post('/api/identities',{id,kind:'person',display_name:'Local contributor'});
 const consents=await get('/api/consents').catch(()=>({consents:[]}));
 if(!consents.consents?.some(x=>x.subject_id===id&&x.status==='granted'))
   await post('/api/consents',{subject_id:id,scope:['memory_submission','federation_public'],status:'granted'});
}

function timeValue(){
 const start=$('timeStart').value.trim(), end=$('timeEnd').value.trim();
 if(!start&&!end)return null;
 return {type:end&&end!==start?'range':'instant',start:start||end,end:end||start,precision:(start||end).length===4?'year':'day'};
}

async function search(){
 const q=$('search').value.trim();
 if(!q){$('results').innerHTML='<div class="muted">Search for a memory, person, place, story or phrase.</div>';return}
 const j=await get('/api/search?q='+encodeURIComponent(q));
 $('results').innerHTML=j.results.map(x=>'<article class="result"><div><span class="pill">'+esc(x.record_type)+'</span><span class="pill">'+esc(x.epistemic_status)+'</span></div><p>'+esc(x.record.content.text)+'</p><small>'+esc(x.id)+' · contributor '+esc(x.record.provenance.contributor_id)+(x.record.place_id?' · '+esc(x.record.place_id):'')+'</small></article>').join('')||'<div class="muted">No matching public memories.</div>';
}

async function albums(){
 const j=await get('/api/albums');
 $('albums').innerHTML=j.albums.map(a=>'<article class="result clickable" data-album="'+esc(a.id)+'"><h3>'+esc(a.title)+'</h3><p>'+esc(a.description||'No description yet.')+'</p><small>'+esc(a.id)+' · '+a.items.length+' item(s)</small></article>').join('')||'<div class="muted">No public albums yet.</div>';
 document.querySelectorAll('[data-album]').forEach(el=>el.onclick=()=>exploreAlbum(el.dataset.album));
}
async function exploreAlbum(id){
 try{
  const j=await get('/api/albums/'+encodeURIComponent(id)+'/explore');
  $('albumExplorer').innerHTML='<div class="result"><h3>'+esc(j.album.title)+'</h3><p>'+esc(j.album.description||'')+'</p><p><b>Records:</b> '+j.records.length+' · <b>Media:</b> '+j.media.length+' · <b>People:</b> '+j.people.length+' · <b>Places:</b> '+j.places.length+'</p><small>'+j.notes.map(esc).join(' · ')+'</small></div>';
 }catch(e){$('albumExplorer').textContent=e.message}
}

async function loadHistory(){
 const place=$('historyPlace').value.trim(); if(!place)return;
 const params=new URLSearchParams({place_id:place});
 if($('historyStart').value.trim())params.set('start',$('historyStart').value.trim());
 if($('historyEnd').value.trim())params.set('end',$('historyEnd').value.trim());
 try{
  const j=await get('/api/place-history?'+params);
  $('history').innerHTML=j.layers.map(layer=>'<article class="history-period"><h3>'+esc(layer.period)+'</h3>'+Object.entries(layer.layers).map(([name,ids])=>'<div><span class="pill">'+esc(name)+'</span> '+ids.length+' item(s) <small>'+ids.map(esc).join(', ')+'</small></div>').join('')+'</article>').join('')||'<div class="muted">No public memories found for this place and period.</div>';
 }catch(e){$('history').textContent=e.message}
}

$('save').onclick=async()=>{
 const text=$('memory').value.trim(); if(!text)return;
 $('saveState').textContent=' Preserving…';
 try{
  await bootstrap();
  const visibility=$('visibility').value;
  const body={contributor_id:$('contributor').value.trim(),record_type:$('recordType').value,epistemic_status:$('status').value,text};
  if($('placeId').value.trim())body.place_id=$('placeId').value.trim();
  const time=timeValue(); if(time)body.time=time;
  body.permissions={visibility,allow_annotation:true,allow_derivatives:false,allow_federation:visibility==='public',allow_export:visibility==='public',sealed_until:null,retention:null,notes:null};
  const j=await post('/api/memories',body);
  $('memory').value=''; $('saveState').textContent=' Preserved '+j.id; await search(); await loadHistory();
 }catch(e){$('saveState').textContent=' '+e.message}
};

$('albumCreate').onclick=async()=>{
 $('albumState').textContent=' Creating…';
 try{
  await bootstrap();
  const body={title:$('albumTitle').value.trim(),description:$('albumDescription').value.trim()||null,contributor_id:$('contributor').value.trim(),items:[],people:[],places:$('albumPlace').value.trim()?[$('albumPlace').value.trim()]:[],permissions:{visibility:'public',allow_annotation:true,allow_derivatives:false,allow_federation:true,allow_export:true}};
  const j=await post('/api/albums',body); $('albumState').textContent=' Created '+j.id; $('albumTitle').value=''; await albums();
 }catch(e){$('albumState').textContent=' '+e.message}
};

$('mediaUpload').onclick=async()=>{
 const file=$('mediaFile').files[0]; if(!file)return;
 $('mediaState').textContent=' Preserving…';
 try{
  if(file.size>25*1024*1024)throw Error('File exceeds the 25 MiB reference-node limit');
  await bootstrap();
  const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file)});
  const j=await post('/api/media',{contributor_id:$('contributor').value.trim(),media_type:$('mediaType').value,mime_type:file.type,data_base64:data});
  $('mediaState').textContent=' Preserved '+j.id+' · '+j.content_hash.slice(0,12);
 }catch(e){$('mediaState').textContent=' '+e.message}
};

$('search').oninput=()=>{clearTimeout(window._t);window._t=setTimeout(search,220)};
$('albumsRefresh').onclick=albums;$('historyLoad').onclick=loadHistory;
$('refresh').onclick=()=>location.reload();
$('discover').onclick=async()=>{try{$('federation').textContent=JSON.stringify(await get('/api/discovery'),null,2)}catch(e){$('federation').textContent=e.message}};
$('syncPeer').onclick=async()=>{
 const peer=$('peerUrl').value.trim();
 if(!peer)return;
 try{
  const discovery=await fetch(peer.replace(/\/$/,'')+'/federation/discovery').then(r=>r.json());
  const body={peer_url:peer,request_id:'moh:sync-request:'+crypto.randomUUID(),protocol:'memory-of-humanity',peer_instance_id:discovery.instance_id,since_cursor:'0',limit:100,visibility:['public'],known_ids:[]};
  const result=await post('/federation/sync-peer',body);
  $('federation').textContent=JSON.stringify(result,null,2);
  await albums(); await search();
 }catch(e){$('federation').textContent=e.message}
};
bootstrap().catch(()=>{});albums().catch(()=>{});