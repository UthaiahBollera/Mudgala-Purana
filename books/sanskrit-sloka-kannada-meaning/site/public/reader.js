"use strict";
(async () => {
 const key=new URLSearchParams(location.search).get("khanda");
 if(!/^[1-9]$/.test(key||"")) return;
 const status=document.getElementById("load-status"),frame=document.getElementById("reader");
 status.textContent="Loading Khanda "+key+"…";
 document.getElementById("reader-title").textContent="ಖಂಡ "+key.replace(/[0-9]/g,d=>"೦೧೨೩೪೫೬೭೮೯"[Number(d)]);
 try {
   const res=await fetch("khanda-"+key+".html.gz");
   if(!res.ok||!res.body) throw Error("reader response");
   const decoded=await new Response(res.body.pipeThrough(new DecompressionStream("gzip"))).text();
   if(!decoded.includes('lang="kn"')) throw Error("Khanda check");
   frame.srcdoc=decoded;
   frame.hidden=false;
   status.textContent="";
 } catch {
   status.textContent="Couldn’t load this khanda. Try reloading in a current browser.";
 }
})();