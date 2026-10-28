/* Published model family: Q = A * rank^b, fitted to aligned observed quantities.
   No universal coefficients are supplied for Mexico, audio, or Mercado Libre.
   Reference: Brynjolfsson, Hu & Smith (2003), Management Science 49(11).
   Historical US-book coefficients are deliberately not used for Mexican audio. */
(function(root){
 'use strict';
 function fit(rows){
  if(!Array.isArray(rows)||rows.length<3)throw Error('Se necesitan al menos tres referencias completas para ejecutar el ajuste; esto no demuestra precisión.');
  const segment=rows[0]; const ids=new Set();const periods=new Set();
  for(const r of rows){
   if(r.marketplace!=='amazon'||r.country!=='MX'||r.source_kind!=='observed'||r.sales_scope!=='product_total')throw Error('Usa referencias observadas de Amazon México con ventas totales del producto. Mercado Libre necesita otro modelo.');
   if(!r.category||r.category!==segment.category)throw Error('Ajusta una categoría de ranking por archivo.');
   if(!(Number.isFinite(r.bsr_geomean)&&r.bsr_geomean>0&&Number.isFinite(r.units_30d)&&r.units_30d>0))throw Error('El ranking medio y las unidades deben ser positivos. No se aceptan valores inventados o incompletos.');
   const start=Date.parse(r.period_start),end=Date.parse(r.period_end);
   if(!Number.isFinite(start)||!Number.isFinite(end)||(end-start)/86400000!==29)throw Error('Cada referencia debe cubrir exactamente 30 días, con ranking de esas mismas fechas.');
   const key=r.product_id+'|'+r.period_start+'|'+r.period_end;if(!r.product_id||ids.has(key))throw Error('Identificador ausente o referencia duplicada.');ids.add(key);periods.add(r.period_start+'|'+r.period_end);
  }
  const xs=rows.map(r=>Math.log(r.bsr_geomean)),ys=rows.map(r=>Math.log(r.units_30d));
  const mx=xs.reduce((a,b)=>a+b)/xs.length,my=ys.reduce((a,b)=>a+b)/ys.length;
  const denom=xs.reduce((s,x)=>s+(x-mx)**2,0);if(denom<1e-8)throw Error('Se necesitan rankings distintos para ajustar la fórmula.');
  const b=xs.reduce((s,x,i)=>s+(x-mx)*(ys[i]-my),0)/denom;
  if(b>=0)throw Error('La muestra no produce una relación inversa entre ranking y ventas; revisa los datos.');
  const a=my-b*mx;
  if(!Number.isFinite(a)||!Number.isFinite(b))throw Error('No se pudo ajustar el modelo.');
  return {type:'rank-power-law',a,b,marketplace:'amazon',country:'MX',category:segment.category,source_kind:'observed',n:rows.length,minRank:Math.min(...rows.map(r=>r.bsr_geomean)),maxRank:Math.max(...rows.map(r=>r.bsr_geomean)),validation:'not_established',periods:[...periods]};
 }
 function predict(model,input){
  if(!model)return {status:'missing_calibration',units:null};
  if(input.marketplace!==model.marketplace||input.country!==model.country||input.category!==model.category)return {status:'outside_segment',units:null};
  if(!Number.isFinite(input.bsr_geomean)||input.bsr_geomean<=0)return {status:'missing_rank',units:null};
  if(input.bsr_geomean<model.minRank||input.bsr_geomean>model.maxRank)return {status:'outside_rank_range',units:null};
  const units=Math.exp(model.a+model.b*Math.log(input.bsr_geomean));
  return Number.isFinite(units)?{status:'calculated_unvalidated',units:Math.round(units)}:{status:'invalid_result',units:null};
 }
 const api={fit,predict};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NexoEstimator=api;
})(typeof window!=='undefined'?window:globalThis);
