'use strict';
(()=>{
 const stage=document.getElementById('radar-stage');if(!stage)return;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const products=[2,5,3].map(key=>(window.NEXO_CATALOG||[]).find(p=>p.key===key)).filter(Boolean);
 if(!products.length)return;
 const money=n=>new Intl.NumberFormat('es-MX',{maximumFractionDigits:2}).format(n);
 stage.innerHTML=products.map((p,i)=>`<article class="signal-card radar-card" data-radar="${i}"><div class="signal-top"><span class="signal-live"></span> EN TU RADAR</div><div class="signal-image"><img src="${p.image}" alt="${esc(p.name)}" width="220" height="220"><span class="signal-category">${esc(p.category+' / '+p.brand)}</span></div><div class="signal-name"><div><small>UN PRODUCTO. DOS MERCADOS.</small><h2>${esc(p.name)}</h2></div><a href="app.html?asin=${p.markets.amazon.id}&v=20261104-research-3" aria-label="Explorar ${esc(p.name)}">↗</a></div><div class="signal-prices"><div><span>Amazon</span><strong>$${money(p.markets.amazon.price)}<span> MXN</span></strong></div><div><span>Mercado Libre</span><strong>$${money(p.markets.meli.price)}<span> MXN</span></strong></div></div><p class="signal-date">Muestra real · precios consultados el 28 oct. 2026</p></article>`).join('');
 const cards=[...stage.children],region=stage.closest('.radar-carousel'),toggle=document.getElementById('radar-motion-toggle'),reduced=matchMedia('(prefers-reduced-motion:reduce)');
 let angle=0,lastTime=null,lastPaint=0,paused=reduced.matches,keyboardFocus=false;
 const turn=Math.PI*2,period=19000;
 function state(){region.dataset.autoplay=String(!paused);toggle.textContent=paused?'Reanudar animación':'Pausar animación';toggle.setAttribute('aria-pressed',String(paused));}
 function paint(){
  const radius=Math.min(134,stage.clientWidth*.19);
  cards.forEach((card,i)=>{
   const a=angle+i*turn/cards.length,depth=Math.cos(a),front=(depth+1)/2;
   const crossing=Math.sin(a*2),x=Math.sin(a)*radius*1.05,y=crossing*46;
   card.style.transform=`translate3d(calc(-50% + ${x.toFixed(2)}px),${y.toFixed(2)}px,${(depth*36).toFixed(2)}px) rotateY(${(crossing*10).toFixed(2)}deg) rotateZ(${(crossing*6).toFixed(2)}deg) scale(${(.9+front*.1).toFixed(4)})`;
   card.style.zIndex=String(Math.round(1000+depth*360));
  });
 }
 function frame(now){
  if(lastTime!==null&&!paused&&!keyboardFocus&&document.visibilityState==='visible')angle=(angle+Math.min(now-lastTime,80)/period*turn)%turn;
  lastTime=now;
  if(now-lastPaint>32&&!paused&&!keyboardFocus){paint();lastPaint=now;}
  requestAnimationFrame(frame);
 }
 toggle.onclick=()=>{paused=!paused;state();};
 region.addEventListener('focusin',event=>{keyboardFocus=event.target.matches(':focus-visible');const card=event.target.closest('[data-radar]');if(keyboardFocus&&card){angle=-Number(card.dataset.radar)*turn/cards.length;paint();}});
 region.addEventListener('focusout',()=>{keyboardFocus=false;});
 reduced.addEventListener('change',event=>{paused=event.matches;state();paint();});
 addEventListener('resize',paint);state();paint();requestAnimationFrame(frame);
 // Sections remain visible without scripting; animate only inside their approach to view.
 const sections=document.querySelectorAll('.section,.method-section,.closing,.market-strip');
 if(!matchMedia('(prefers-reduced-motion:reduce)').matches&&'IntersectionObserver'in window){sections.forEach(s=>s.classList.add('reveal-section'));const io=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target);}});},{threshold:.08});sections.forEach(s=>io.observe(s));}
})();
