'use strict';
(() => {
  const ASIN = /\/(?:dp|gp\/product)\/([A-Z0-9]{10})(?:\/|$)/i;
  const readAsin = () => location.pathname.match(ASIN)?.[1]?.toUpperCase();
  if (!readAsin() || document.getElementById('nexo-extension-host')) return;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => Number.isFinite(value) ? value.toLocaleString('es-MX') : '';
  const money = value => Number.isFinite(value) ? '$' + number(value) : '';
  const style = `
    :host{all:initial;display:block;clear:both;scroll-margin-top:100px;width:100%;min-width:0;margin:16px 0 24px;color:#172c42;font:13px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color-scheme:light}
    *,*::before,*::after{box-sizing:border-box} [hidden]{display:none!important}
    section{background:#fff;border:1px solid #d9e1e8;border-radius:8px;overflow:hidden;text-align:left}
    button,a{font:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #0593c6;outline-offset:3px}
    button{color:#33485f;background:white;border:1px solid #d9e1e8;border-radius:5px;padding:7px 12px;line-height:1.25}
    button:hover{background:#f1f7fb}button:disabled{opacity:.55;cursor:wait}a{color:#087fa8;text-decoration:none}a:hover{text-decoration:underline}
    header{display:flex;align-items:center;gap:14px;padding:11px 18px;border-bottom:1px solid #e5eaf0;background:linear-gradient(100deg,#f2fafd,#faf6fb)}
    .brand{font-size:25px;font-weight:750;line-height:1;letter-spacing:-1.7px;color:#19364d}.brand span{color:#b52c83}.eyebrow{font-size:10px;letter-spacing:1.3px;font-weight:600;color:#52657a}.spacer{flex:1}.explore{display:inline-flex;align-items:center;gap:5px;font-size:11px;white-space:nowrap}.explore svg{width:16px;height:16px}.meta{font-size:11px;color:#607085}.subtle{border:0;background:transparent;padding:6px}
    .summary{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));padding:18px 5px 16px}.metric{padding:0 18px;min-width:0;border-right:1px solid #e6ebef}.metric:last-child{border:0}.metric span{display:block;font-size:11px;color:#5a6b7e}.metric strong{display:block;min-height:33px;margin-top:6px;font-size:24px;line-height:1.3;font-weight:600;color:#15334b;font-variant-numeric:tabular-nums}.metric small{display:block;min-height:15px;font-size:10px;color:#687b8e;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .foot{padding:9px 18px;border-top:1px solid #e8edf1;display:flex;align-items:center;gap:15px;flex-wrap:wrap;font-size:10px;color:#617285}.foot a{font-size:11px}.foot output{margin-right:auto}
    .toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:17px 20px 0;flex-wrap:wrap}.tabs,.periods{display:flex;gap:4px;flex-wrap:wrap}.tabs button{border:0;border-radius:0;padding:9px 12px 12px;font-size:12px;border-bottom:2px solid transparent}.tabs button[aria-selected=true]{border-color:#058cb9;color:#00739e;font-weight:650}.periods button{font-size:11px;padding:5px 10px}.periods button[aria-pressed=true]{background:#eaf5fa;border-color:#82c3d9;color:#006c93}
    .analysis{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:24px;padding:18px 20px 22px}.chart-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:12px}.chart-heading h3{font-size:13px;margin:0;font-weight:600}.legend{display:flex;gap:15px;font-size:10px;color:#586f83}.legend span::before{content:'';display:inline-block;width:7px;height:7px;background:#0593c6;border-radius:50%;margin-right:5px}.legend .pink::before{background:#bc3d8e}
    .plot{height:210px;margin:14px 3px 0 30px;border-left:1px solid #dce4ec;border-bottom:1px solid #dce4ec;background:repeating-linear-gradient(0deg,transparent,transparent calc(25% - 1px),#e9eef3 calc(25% - 1px),#e9eef3 25%),repeating-linear-gradient(90deg,transparent,transparent calc(20% - 1px),#f0f3f6 calc(20% - 1px),#f0f3f6 20%)}
    .axis{display:flex;justify-content:space-between;margin:9px 3px 0 30px;font-size:10px;color:#768697}.caption{font-size:10px;color:#68798b;margin:14px 0 0 30px}.facts{border-left:1px solid #e8edf1;padding-left:23px}.facts h3{font-size:12px;margin:0 0 14px}.fact{margin-bottom:15px}.fact span{display:block;font-size:10px;color:#63768a}.fact strong{display:block;min-height:19px;margin-top:3px;font-size:12px;font-weight:550;overflow-wrap:anywhere}.fact .big{font-size:22px}.facts small{display:block;font-size:10px;color:#67798c;margin-top:3px}.bars{padding:12px 0;min-height:238px}.rating-row{display:grid;grid-template-columns:28px minmax(0,1fr) 38px;align-items:center;gap:14px;margin-bottom:20px;font-size:12px}.track{height:10px;background:#edf1f5;border-radius:3px;overflow:hidden}.track i{display:block;height:100%;background:linear-gradient(90deg,#0593c6,#ad5097)}.details-title{font-size:13px;font-weight:600}.status-dot{width:6px;height:6px;border-radius:50%;background:#1c9b89;display:inline-block;margin-right:6px}
    @media(max-width:1000px){.metric{padding:0 12px}.metric strong{font-size:21px}.analysis{grid-template-columns:minmax(0,1fr) 190px;gap:18px}.eyebrow{letter-spacing:.7px}}
    @media(max-width:700px){header{padding:12px;flex-wrap:wrap;gap:10px}.eyebrow{display:none}.summary{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:18px}.metric:nth-child(3){border:0}.metric strong{font-size:20px}.analysis{grid-template-columns:1fr;padding:15px}.facts{border-left:0;border-top:1px solid #e8edf1;padding:18px 0 0;display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.facts h3{grid-column:1/-1}.toolbar{padding:12px 12px 0;gap:10px}.tabs button{padding:9px 7px;font-size:11px}.meta{font-size:10px}.plot{height:170px}.legend{gap:8px}.foot{padding:10px 12px;gap:10px}}
  `;
  const summaryHost = document.createElement('div');
  summaryHost.id = 'nexo-extension-host';
  const summaryRoot = summaryHost.attachShadow({mode:'open'});
  const detailHost = document.createElement('div');
  detailHost.id = 'nexo-extension-analysis';
  const detailRoot = detailHost.attachShadow({mode:'open'});
  let asin = readAsin(), product = null, activeTab = 'history', days = 30, folded = false, revision = 0;
  const metric = (label, value, hint = '') => `<div class="metric"><span>${escape(label)}</span><strong>${escape(value)}</strong><small>${escape(hint)}</small></div>`;
  const fact = (label, value, big = false) => `<div class="fact"><span>${escape(label)}</span><strong class="${big?'big':''}">${escape(value)}</strong></div>`;
  summaryRoot.innerHTML = `<style>${style}</style><section aria-label="Resumen Nexo del producto"><header><b class="brand">ne<span>x</span>o</b><span class="eyebrow">INTELIGENCIA DE PRODUCTO</span><span class="spacer"></span><span class="meta" id="identity"></span><a class="explore" href="http://127.0.0.1:8787/app.html?focus=search" target="_blank" rel="noopener noreferrer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>Explorar productos</a><button id="evolution">Ver evolución</button><button class="subtle" id="fold" aria-label="Plegar resumen Nexo" aria-expanded="true">Ocultar</button></header><div id="metrics" class="summary"></div><div class="foot"><output id="state" role="status">Conectando con Nexo local…</output><a id="full" target="_blank" rel="noopener noreferrer">Análisis completo ↗</a><button id="query">Actualizar ficha</button></div></section>`;
  detailRoot.innerHTML = `<style>${style}</style><section aria-label="Evolución y datos Nexo"><header><b class="brand">ne<span>x</span>o</b><span class="details-title">Evolución del producto</span><span class="spacer"></span><span class="meta">Amazon México · MXN</span></header><div class="toolbar"><div class="tabs" role="tablist" aria-label="Datos del producto"><button role="tab" id="tab-history" data-tab="history" aria-controls="chart-content">Precio y BSR</button><button role="tab" id="tab-sales" data-tab="sales" aria-controls="chart-content">Ventas e ingresos</button><button role="tab" id="tab-reviews" data-tab="reviews" aria-controls="chart-content">Opiniones</button></div><div class="periods" role="group" aria-label="Periodo">${[7,30,90].map(d=>`<button data-days="${d}" aria-pressed="${d===days}">${d} días</button>`).join('')}</div></div><div class="analysis"><div id="chart-content" role="tabpanel"></div><div id="facts" class="facts"></div></div><div class="foot"><span>Los campos sin datos permanecen vacíos.</span><span id="queried"></span></div></section>`;
  const state = summaryRoot.getElementById('state');
  function paintChart(){
    detailRoot.querySelectorAll('[data-tab]').forEach(button=>{const selected=button.dataset.tab===activeTab;button.setAttribute('aria-selected',selected);button.tabIndex=selected?0:-1;});
    detailRoot.querySelectorAll('[data-days]').forEach(button=>button.setAttribute('aria-pressed',Number(button.dataset.days)===days));
    detailRoot.querySelector('.periods').hidden = activeTab==='reviews';
    const chart=detailRoot.getElementById('chart-content');chart.setAttribute('aria-labelledby','tab-'+activeTab);
    if(activeTab==='reviews'){
      chart.innerHTML=`<div class="chart-heading"><h3>Distribución de opiniones</h3><span class="meta">${escape(number(product?.reviews))}${Number.isFinite(product?.reviews)?' opiniones':''}</span></div><div class="bars">${[5,4,3,2,1].map(stars=>{const row=product?.rating_distribution?.find(r=>r.stars===stars),valid=Number.isFinite(row?.percentage);return `<div class="rating-row"><span>${stars} ★</span><div class="track">${valid?`<i style="width:${Math.max(0,Math.min(100,row.percentage))}%"></i>`:''}</div><span>${valid?escape(row.percentage)+'%':''}</span></div>`;}).join('')}</div>`;
    }else{
      const sales=activeTab==='sales';
      chart.innerHTML=`<div class="chart-heading"><h3>${sales?'Ventas e ingresos':'Histórico de precio y ranking'}</h3><div class="legend"><span>${sales?'Ventas':'Precio MXN'}</span><span class="pink">${sales?'Ingresos MXN':'BSR'}</span></div></div><div class="plot" role="img" aria-label="Gráfica vacía: ${sales?'estimaciones todavía no disponibles':'histórico todavía no disponible'}"></div><div class="axis"><span>Hace ${days} días</span><span>Hoy</span></div><p class="caption">${sales?'Serie pendiente del estimador.':'Todavía no hay una serie histórica conectada a esta gráfica.'}</p>`;
    }
  }
  function paint(){
    const rank=product?.ranks?.[0];
    summaryRoot.getElementById('identity').textContent='ASIN '+asin;
    summaryRoot.getElementById('full').href='http://127.0.0.1:8787/app.html?analyze='+asin;
    summaryRoot.getElementById('metrics').innerHTML=metric('Precio actual',money(product?.price),'MXN')+metric('BSR',Number.isFinite(rank?.rank)?'#'+number(rank.rank):'',rank?.category?.split(' (')[0]||'')+metric('Ventas · 30 días','','Estimación')+metric('Ingresos · 30 días','','MXN · estimación')+metric('Valoración',Number.isFinite(product?.rating)?number(product.rating)+' / 5':'','')+metric('Opiniones',number(product?.reviews),'');
    detailRoot.getElementById('facts').innerHTML='<h3>Datos de la publicación</h3>'+fact('Compras públicas · mes pasado',Number.isFinite(product?.monthly_units_min)?number(product.monthly_units_min)+'+':'',true)+(product?.monthly_units_min?'<small>Umbral publicado; no son ventas exactas.</small>':'')+fact('Categoría',rank?.category?.split(' (')[0]||'')+fact('ASIN padre',product?.parent_asin||'')+fact('Vendedores observados',product?.seller_names?.length?number(product.seller_names.length):'');
    detailRoot.getElementById('queried').textContent=product?.queried_at?'Última consulta: '+new Date(product.queried_at).toLocaleString('es-MX'):'';
    paintChart();
  }
  summaryRoot.getElementById('fold').onclick=()=>{folded=!folded;summaryRoot.getElementById('metrics').hidden=folded;const button=summaryRoot.getElementById('fold');button.textContent=folded?'Mostrar':'Ocultar';button.setAttribute('aria-expanded',!folded);button.setAttribute('aria-label',(folded?'Desplegar':'Plegar')+' resumen Nexo');};
  summaryRoot.getElementById('evolution').onclick=()=>detailHost.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
  detailRoot.querySelectorAll('[data-tab]').forEach(button=>{
    button.onclick=()=>{activeTab=button.dataset.tab;paintChart();};
    button.onkeydown=event=>{const tabs=[...detailRoot.querySelectorAll('[data-tab]')],index=tabs.indexOf(button);let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;if(event.key==='Home')next=0;if(event.key==='End')next=tabs.length-1;if(next!==undefined){event.preventDefault();tabs[next].click();tabs[next].focus();}};
  });
  detailRoot.querySelectorAll('[data-days]').forEach(button=>button.onclick=()=>{days=Number(button.dataset.days);paintChart();});
  function request(action){
    const requestedAsin=asin,requestRevision=++revision,button=summaryRoot.getElementById('query');
    if(action==='product'){button.disabled=true;state.textContent='Actualizando ficha…';}
    chrome.runtime.sendMessage({action,asin:requestedAsin},response=>{
      const error=chrome.runtime.lastError;
      if(requestedAsin!==asin||requestRevision!==revision)return;
      button.disabled=false;
      if(error||!response?.ok){state.textContent=response?.error||'Nexo local no está disponible. Los campos siguen vacíos.';return;}
      product=response.product||null;paint();
      state.textContent=product?'Ficha guardada · los datos pendientes quedan vacíos.':'Sin ficha guardada. Actualizar puede consumir una consulta de tu API.';
    });
  }
  summaryRoot.getElementById('query').onclick=()=>request('product');
  // These anchors only position our blocks; product data still comes from the API.
  function mount(){
    const current=readAsin();
    if(!current){summaryHost.remove();detailHost.remove();return;}
    const productArea=document.getElementById('ppd');
    if(!productArea?.parentElement)return;
    if(productArea.previousElementSibling!==summaryHost)productArea.before(summaryHost);
    if(productArea.nextElementSibling!==detailHost)productArea.after(detailHost);
    if(current!==asin){asin=current;product=null;paint();request('peek');}
  }
  paint();mount();request('peek');
  let scheduled=false;
  new MutationObserver(()=>{if(scheduled)return;scheduled=true;setTimeout(()=>{scheduled=false;mount();},180);}).observe(document.body,{childList:true,subtree:true});
  addEventListener('popstate',mount);
})();
