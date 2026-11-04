'use strict';
(()=>{
 const form=document.getElementById('amazon-search-form');if(!form)return;
 const $=id=>document.getElementById(id),runtime=window.NEXO_RUNTIME;
 const local=!!(runtime?.localToken&&['127.0.0.1','localhost'].includes(location.hostname));
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const money=n=>Number.isFinite(n)?new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(n):'Sin precio';
 let products=[],last=null;
 function connection(){ $('connection-dialog').showModal();$('connection-form').hidden=!local;$('connection-local-note').hidden=local;}
 $('connection-open').addEventListener('click',connection);
 async function post(path,data){
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),60000);
  try{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Nexo-Local':runtime.localToken},body:JSON.stringify(data),credentials:'same-origin',signal:controller.signal});const payload=await response.json();if(!response.ok){const error=new Error(payload.message||({'authentication_required':'La clave no ha sido aceptada por el proveedor.','provider_rejected_request':'El proveedor no pudo completar esta consulta.','local_request_budget_reached':'Has alcanzado el límite local de 20 búsquedas de este arranque.','rate_limited':'El proveedor pide esperar antes de consultar de nuevo.','network_error':'No se ha podido recibir una respuesta del proveedor.','payment_or_plan_required':'El proveedor indica que la prueba o plan no permite esta consulta.'}[payload.error])||'No se ha podido completar la consulta.');throw error;}return payload;}finally{clearTimeout(timeout);}
 }
 $('connection-form').addEventListener('submit',async e=>{e.preventDefault();if(!local)return;const key=$('rainforest-key').value.trim();$('rainforest-key').value='';try{const data=await post('/api/settings/rainforest',{key});$('connection-feedback').textContent=data.note;$('discovery-status').textContent='Clave guardada localmente. Escribe un producto y pulsa Buscar para verificar la conexión.';$('connection-open').innerHTML='<span></span>Clave configurada';}catch(err){$('connection-feedback').textContent=err.message;}});
 function render(){
  const max=$('discovery-max-price').value,category=$('discovery-category').value;
  const visible=products.filter(p=>(!max||Number.isFinite(p.price)&&p.price<=Number(max))&&(category==='all'||p.categories?.some(c=>c.name===category)));
  $('discovery-grid').innerHTML=visible.length?visible.map(p=>`<article class="discovered-product"><a class="discovered-image" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${p.image_url?`<img src="${esc(p.image_url)}" alt="${esc(p.title)}" loading="lazy" referrerpolicy="no-referrer">`:'<span>Imagen no disponible</span>'}${p.sponsored?'<span class="sponsored-label">Patrocinado</span>':''}</a><div class="discovered-body"><small>${esc(p.asin)} · ${esc(p.provider)}</small><h3><a href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.title)}</a></h3><strong class="discovered-price">${money(p.price)}</strong><div class="discovered-metrics"><span>Valoración <strong>${p.rating===null?'—':esc(p.rating)+' / 5'}</strong></span><span>Opiniones <strong>${p.reviews===null?'—':esc(p.reviews)}</strong></span><span>BSR <strong>${p.ranks?.[0]?esc(p.ranks[0].rank):'—'}</strong></span><span>Ventas / 30 días <strong>Sin calcular</strong></span></div>${p.ranks?.[0]?`<p class="rank-scope">Ranking en ${esc(p.ranks[0].category||'categoría no indicada')}</p>`:''}<a class="listing-link" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">Ver publicación en Amazon ↗</a></div></article>`).join(''):'<div class="discovery-empty">No hay productos con estos filtros. Prueba otra búsqueda o amplía el precio máximo.</div>';
  $('discovery-meta').textContent=`${visible.length} de ${products.length} productos recibidos · ${last?.provider||''} · ${last?.stored_snapshot?'búsqueda guardada':last?.cached?'copia reciente de la misma búsqueda':'consulta por API'} · ${last?.queried_at?new Date(last.queried_at).toLocaleString('es-MX'):''}`;
 }
 function showResults(data){
  if(!Array.isArray(data.products)||data.marketplace!=='amazon.com.mx')throw Error('Respuesta del proveedor no válida.');
  last=data;products=data.products;$('discovery-results').hidden=false;
  $('discovery-category').innerHTML='<option value="all">Todas las recibidas</option>'+[...new Set(products.flatMap(p=>p.categories||[]).map(c=>c.name).filter(Boolean))].sort().map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');$('discovery-max-price').value='';render();
 }
 form.addEventListener('submit',async e=>{
  e.preventDefault();if(!local){connection();$('connection-feedback').textContent='Para buscar productos nuevos necesitas abrir Nexo con su servidor local y configurar una clave. El catálogo de muestra continúa funcionando.';return;}
  const button=$('amazon-search-button'),query=$('amazon-query').value.trim();if(!query)return;
  button.disabled=true;button.textContent='Buscando…';$('discovery-status').textContent='Consultando Amazon México mediante la API. Puede tardar unos segundos.';
  try{const data=await post('/api/search',{query});showResults(data);
   $('discovery-status').textContent=data.products.length?`Búsqueda completada. ${data.products.length} productos recibidos${data.cached?' desde caché, sin otra consulta al proveedor':''}.`:'La API no devolvió productos para esta búsqueda.';
  }catch(err){$('discovery-status').textContent=err.name==='AbortError'?'La consulta ha tardado demasiado. Revisa el proveedor antes de repetirla.':err.message;}finally{button.disabled=false;button.innerHTML='Buscar en Amazon <span aria-hidden="true">↗</span>';}
 });
 $('discovery-category').addEventListener('change',render);$('discovery-max-price').addEventListener('input',render);
 if(local)fetch('/api/discovery/latest',{cache:'no-store'}).then(r=>r.json()).then(data=>{if(data.result&&!last){showResults(data.result);$('discovery-status').textContent='Última búsqueda guardada: '+data.result.products.length+' productos. Se conserva su fecha de consulta; no se ha gastado otra petición.';}}).catch(()=>{});
 if(local)fetch('/api/health',{cache:'no-store'}).then(r=>r.json()).then(s=>{if(s.discovery?.configured){$('connection-open').innerHTML='<span></span>API configurada';if(!last)$('discovery-status').textContent='Fuente configurada: '+s.discovery.provider+'. La búsqueda verificará el acceso; hasta entonces se conserva la muestra.';}}).catch(()=>{});
})();
