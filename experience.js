'use strict';
(()=>{
 const stage=document.getElementById('radar-stage');if(!stage)return;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const products=[2,5,3].map(key=>(window.NEXO_CATALOG||[]).find(p=>p.key===key)).filter(Boolean);let active=0,paused=false,keyboardFocus=false;
 const money=n=>new Intl.NumberFormat('es-MX',{maximumFractionDigits:2}).format(n);
 stage.innerHTML=products.map((p,i)=>`<article class="signal-card radar-card" data-radar="${i}"><div class="signal-top"><span class="signal-live"></span> EN TU RADAR <span>0${i+1} / 03</span></div><div class="signal-image"><img src="${p.image}" alt="${esc(p.name)}" width="220" height="220"><span class="signal-category">${esc(p.category+' / '+p.brand)}</span></div><div class="signal-name"><div><small>UN PRODUCTO. DOS MERCADOS.</small><h2>${esc(p.name)}</h2></div><a href="app.html?asin=${p.markets.amazon.id}&v=20261104-research-3" aria-label="Explorar ${esc(p.name)}">↗</a></div><div class="signal-prices"><div><span>Amazon</span><strong>$${money(p.markets.amazon.price)}<span> MXN</span></strong></div><div><span>Mercado Libre</span><strong>$${money(p.markets.meli.price)}<span> MXN</span></strong></div></div><p class="signal-date">Muestra real · precios consultados el 28 oct. 2026</p></article>`).join('');
 function update(){stage.querySelectorAll('.radar-card').forEach((card,i)=>{const position=(i-active+products.length)%products.length;card.dataset.position=position;card.inert=position!==0;card.setAttribute('aria-hidden',String(position!==0));});document.getElementById('radar-position').textContent=`0${active+1} / 03`;document.getElementById('radar-pause').textContent=paused?'▶':'Ⅱ';document.getElementById('radar-pause').setAttribute('aria-label',paused?'Reanudar rotación':'Pausar rotación');}
 function move(delta){active=(active+delta+products.length)%products.length;update();}
 document.getElementById('radar-prev').onclick=()=>move(-1);document.getElementById('radar-next').onclick=()=>move(1);document.getElementById('radar-pause').onclick=()=>{paused=!paused;stage.closest('.radar-carousel').dataset.autoplay=String(!paused);update();};
 const region=stage.closest('.radar-carousel');region.dataset.autoplay='true';region.addEventListener('focusin',e=>{keyboardFocus=e.target.matches(':focus-visible');});region.addEventListener('focusout',()=>{keyboardFocus=false;});
 setInterval(()=>{if(!paused&&!keyboardFocus&&document.visibilityState==='visible')move(1);},3600);update();
 // Sections remain visible without scripting; animate only inside their approach to view.
 const sections=document.querySelectorAll('.section,.method-section,.closing,.market-strip');
 if(!matchMedia('(prefers-reduced-motion:reduce)').matches&&'IntersectionObserver'in window){sections.forEach(s=>s.classList.add('reveal-section'));const io=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target);}});},{threshold:.08});sections.forEach(s=>io.observe(s));}
})();
