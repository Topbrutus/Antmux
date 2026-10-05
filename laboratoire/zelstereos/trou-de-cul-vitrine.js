(()=>{
  'use strict';
  const API='/laboratoire/embryon-x72/api/gamezel/trou-de-cul/spectator';
  let timer=null;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));

  function css(){return `
    .tdc-vitrine{margin:10px 0 14px;padding:10px;border:1px solid #24465d;background:#02070c;border-radius:6px;box-shadow:inset 0 0 24px rgba(38,111,151,.08)}
    .tdc-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:8px;font:800 11px/1.2 ui-monospace,Consolas,monospace}
    .tdc-head strong{color:#dff6ff}.tdc-theme{color:#ffd86b}.tdc-live{color:#74c0fc}.tdc-live.ok{color:#69db7c}.tdc-live.err{color:#ff8787}
    .tdc-table{display:grid;grid-template-columns:minmax(165px,1fr) minmax(285px,1.45fr) minmax(165px,1fr);grid-template-rows:112px 180px 112px;gap:8px;align-items:center;min-height:420px;border:1px solid #102a3b;border-radius:18px;background:radial-gradient(circle at center,#092334 0,#05131d 52%,#02070c 100%);padding:10px;overflow:hidden}
    .tdc-seat{position:relative;min-width:0;text-align:center;color:#b8d5e6;font:800 10px/1.2 ui-monospace,Consolas,monospace}.tdc-seat-name{margin-bottom:4px}.tdc-seat.active .tdc-seat-name{color:#ffd86b;text-shadow:0 0 9px rgba(255,216,107,.45)}
    .tdc-seat-p1{grid-column:2;grid-row:1}.tdc-seat-p2{grid-column:3;grid-row:2}.tdc-seat-p3{grid-column:2;grid-row:3}.tdc-seat-p4{grid-column:1;grid-row:2}
    .tdc-hand{position:relative;height:82px;min-width:170px;margin:auto}.tdc-card{position:absolute;left:50%;bottom:0;width:52px;height:74px;border-radius:5px;border:1px solid #9fb0b9;background:#f5f1e7;color:#101820;box-shadow:0 2px 7px rgba(0,0,0,.45);transform-origin:50% 115%;transform:translate(calc(-50% + var(--x,0px)),var(--y,0px)) rotate(var(--r,0deg));transition:transform .16s ease,opacity .16s ease;font:900 12px/1 ui-monospace,Consolas,monospace;overflow:hidden}
    .tdc-card.red{color:#b3262e}.tdc-card.hidden{background:repeating-linear-gradient(45deg,#102b3c,#102b3c 5px,#183d54 5px,#183d54 10px);border-color:#315f78}.tdc-corner{position:absolute;top:4px;left:5px;display:flex;flex-direction:column;align-items:center;gap:1px}.tdc-corner .suit{font-size:11px}.tdc-card.hidden .tdc-corner{display:none}
    .tdc-center{grid-column:2;grid-row:2;align-self:stretch;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:50%;border:1px dashed #28506a;background:rgba(1,7,12,.42);min-width:210px}.tdc-center-title{font:900 10px/1 ui-monospace,Consolas,monospace;color:#6f94aa;margin-bottom:7px}.tdc-pile{position:relative;width:185px;height:92px}.tdc-pile .tdc-card{bottom:8px}.tdc-meta{margin-top:8px;text-align:center;color:#7898aa;font:800 9px/1.35 ui-monospace,Consolas,monospace}
    @media(max-width:900px){.tdc-table{grid-template-columns:1fr 1.2fr 1fr}.tdc-card{width:46px;height:66px}.tdc-hand{min-width:140px}.tdc-pile{width:155px}}
  `;}

  function board(){return `
    <div id="trouDeCulVitrine" class="tdc-vitrine" aria-label="Table du jeu Trou de cul">
      <div class="tdc-head">
        <strong>🃏 TROU DE CUL · TABLE VITRINE</strong>
        <span>THÈME : <b id="tdcTheme" class="tdc-theme">—</b></span>
        <span id="tdcLive" class="tdc-live">MOTEUR EN ATTENTE</span>
      </div>
      <div class="tdc-table">
        <div id="tdcSeatP1" class="tdc-seat tdc-seat-p1"><div class="tdc-seat-name">P1 · ASTRA</div><div id="tdcHandP1" class="tdc-hand"></div></div>
        <div id="tdcSeatP2" class="tdc-seat tdc-seat-p2"><div class="tdc-seat-name">P2 · MUSE</div><div id="tdcHandP2" class="tdc-hand"></div></div>
        <div class="tdc-center"><div class="tdc-center-title">CARTES SUR LA TABLE</div><div id="tdcPile" class="tdc-pile"></div><div id="tdcCenterMeta" class="tdc-meta">AUCUNE CARTE JOUÉE</div></div>
        <div id="tdcSeatP3" class="tdc-seat tdc-seat-p3"><div class="tdc-seat-name">P3 · GROK</div><div id="tdcHandP3" class="tdc-hand"></div></div>
        <div id="tdcSeatP4" class="tdc-seat tdc-seat-p4"><div class="tdc-seat-name">P4 · ANTIGRAVITY</div><div id="tdcHandP4" class="tdc-hand"></div></div>
      </div>
      <div id="tdcMeta" class="tdc-meta">MANCHE — · TOUR — · VITRINE LECTURE SEULE</div>
    </div>`;}

  function card(card,index,total,hidden,pile){
    const d=index-(total-1)/2;
    const x=(d*(pile?25:18)).toFixed(1);
    const y=(Math.abs(d)*(pile?1.3:.7)).toFixed(1);
    const r=(d*(pile?4:2.2)).toFixed(1);
    const style=`--x:${x}px;--y:${y}px;--r:${r}deg;z-index:${index+1}`;
    if(hidden)return `<div class="tdc-card hidden" style="${style}"></div>`;
    const s=card?.suit_symbol||'';
    const red=(s==='♥'||s==='♦')?' red':'';
    return `<div class="tdc-card${red}" title="${esc(card?.formula_slot||card?.id||'')}" style="${style}"><div class="tdc-corner"><span>${esc(card?.rank||'?')}</span><span class="suit">${esc(s)}</span></div></div>`;
  }

  function hand(pid,state){
    const el=document.getElementById('tdcHand'+pid);
    if(!el)return;
    const hidden=!!state?.hidden;
    const cards=hidden?Array.from({length:Number(state?.count||0)},()=>null):(state?.cards||[]);
    el.innerHTML=cards.map((c,i)=>card(c,i,cards.length,hidden,false)).join('');
  }

  function render(s){
    if(!s||typeof s!=='object')return;
    for(const pid of ['P1','P2','P3','P4']){
      hand(pid,s.hands?.[pid]||{hidden:true,count:0,cards:[]});
      document.getElementById('tdcSeat'+pid)?.classList.toggle('active',s.currentPlayerId===pid);
    }
    const pile=Array.isArray(s.lastPlay)?s.lastPlay:[];
    document.getElementById('tdcPile').innerHTML=pile.map((c,i)=>card(c,i,pile.length,false,true)).join('');
    document.getElementById('tdcCenterMeta').textContent=pile.length?`${pile.length} CARTE${pile.length>1?'S':''} · ${s.lastPlayPlayerId||'—'}`:'AUCUNE CARTE JOUÉE';
    document.getElementById('tdcTheme').textContent=s.theme||'—';
    document.getElementById('tdcMeta').textContent=`MANCHE ${s.round??'—'} · TOUR ${s.currentPlayerId||'—'} · ${s.active?'EN COURS':'EN ATTENTE'} · VITRINE LECTURE SEULE`;
    const live=document.getElementById('tdcLive');
    live.textContent='TABLE LIVE';
    live.className='tdc-live ok';
  }

  async function poll(){
    try{
      const r=await fetch(API,{credentials:'same-origin',cache:'no-store'});
      if(!r.ok)throw new Error('HTTP '+r.status);
      render(await r.json());
    }catch(_){
      const live=document.getElementById('tdcLive');
      if(live){live.textContent='MOTEUR EN ATTENTE';live.className='tdc-live err';}
    }finally{
      clearTimeout(timer);
      timer=setTimeout(poll,800);
    }
  }

  function mount(){
    if(document.getElementById('trouDeCulVitrine'))return;
    const style=document.createElement('style');
    style.textContent=css();
    document.head.appendChild(style);
    const target=document.getElementById('speechReceptorBay3')||document.getElementById('PANEL_3');
    if(!target)return;
    const holder=document.createElement('div');
    holder.innerHTML=board();
    target.parentNode.insertBefore(holder.firstElementChild,target);
    poll();
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
