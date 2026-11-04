'use strict';
const BASE='http://127.0.0.1:8787';
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(sender.id!==chrome.runtime.id||!sender.tab?.url)return false;
 let url;try{url=new URL(sender.tab.url);}catch(_){return false;}
 if(url.hostname!=='www.amazon.com.mx'||!['peek','product'].includes(message.action)||!/^[A-Z0-9]{10}$/.test(message.asin))return false;
 const pathAsin=url.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})(?:\/|$)/i)?.[1]?.toUpperCase();
 if(pathAsin!==message.asin)return false;
 (async()=>{
  try{
   if(message.action==='peek'){const r=await fetch(BASE+'/api/discovery/product/'+message.asin,{signal:AbortSignal.timeout(8000)});const d=await r.json();reply({ok:r.ok,product:d.product});return;}
   const configText=await(await fetch(BASE+'/runtime-config.js',{signal:AbortSignal.timeout(8000)})).text();const config=JSON.parse(configText.replace(/^window\.NEXO_RUNTIME\s*=\s*/,'').replace(/;\s*$/,''));
   const r=await fetch(BASE+'/api/product',{method:'POST',headers:{'Content-Type':'application/json','X-Nexo-Local':config.localToken},body:JSON.stringify({asin:message.asin}),signal:AbortSignal.timeout(60000)});const d=await r.json();reply({ok:r.ok,product:d.product,error:r.ok?null:'La ficha no se ha recibido. Revisa la cuota y el servidor Nexo.'});
  }catch(_){reply({ok:false,error:'Abre el servidor local de Nexo en el puerto 8787 y vuelve a intentarlo.'});}
 })();return true;
});
