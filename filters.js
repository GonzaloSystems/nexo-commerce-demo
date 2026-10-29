/* Product filters share one contract across local catalog and future API records. */
(function(root){
 'use strict';
 const ranges=[['minPrice','maxPrice','price'],['minReviews','maxReviews','reviewCount'],['minBsr','maxBsr','bsr']];
 function numeric(v){if(v===null||v===undefined||String(v).trim()==='')return null;const n=Number(v);return Number.isFinite(n)?n:NaN;}
 function parseIds(text,market){const ids=[...new Set(String(text||'').toUpperCase().split(/[\s,;]+/).filter(Boolean))];const pattern=market==='amazon'?/^[A-Z0-9]{10}$/:/^MLM-?\d+$/;if(ids.length>100)throw Error('Introduce como máximo 100 identificadores.');if(ids.some(id=>!pattern.test(id)))throw Error(market==='amazon'?'Cada ASIN debe tener 10 letras o números.':'Usa identificadores de Mercado Libre como MLM25302803.');return ids.map(id=>id.replace('-',''));}
 function normalize(raw,market){const f={...raw,query:String(raw.query||'').trim().toLocaleLowerCase('es'),ids:parseIds(raw.ids,market)};
  for(const key of ['minPrice','maxPrice','minReviews','maxReviews','minBsr','maxBsr','rating','minUnits','minRevenue','maxSellers']){f[key]=numeric(raw[key]);if(f[key]!==null&&(!Number.isFinite(f[key])||f[key]<0))throw Error('Los límites deben ser números positivos o cero.');}
  for(const [min,max] of ranges)if(f[min]!==null&&f[max]!==null&&f[min]>f[max])throw Error('El mínimo no puede ser mayor que el máximo.');
  if(market!=='amazon'){f.minBsr=f.maxBsr=null;}
  return f;
 }
 function bounded(value,min,max){if(min===null&&max===null)return true;return typeof value==='number'&&Number.isFinite(value)&&(min===null||value>=min)&&(max===null||value<=max);}
 function matches(p,f){return (!f.query||`${p.name} ${p.brand} ${p.model} ${p.id}`.toLocaleLowerCase('es').includes(f.query))&&(!f.ids.length||f.ids.includes(p.id.replace('-','')))&&(!f.category||f.category==='all'||p.category===f.category)&&(!f.brand||f.brand==='all'||p.brand===f.brand)&&(!f.format||f.format==='all'||p.format===f.format)&&ranges.every(([min,max,field])=>bounded(p[field],f[min],f[max]))&&bounded(p.rating,f.rating,null)&&bounded(p.units,f.minUnits,null)&&bounded(p.revenue,f.minRevenue,null)&&bounded(p.sellerCount,null,f.maxSellers);}
 const api={normalize,matches,parseIds};if(typeof module==='object'&&module.exports)module.exports=api;else root.NexoFilters=api;
})(typeof window==='undefined'?globalThis:window);
