(()=>{
"use strict";
const EXACT_TEXT="240.10000000005764801000001384128720100332329305696089";
const NOMINAL_TEXT="240.1";
const DUST_TEXT="0.00000000005764801000001384128720100332329305696089";
const EXACT_HZ=Number(EXACT_TEXT);
const CYCLE_LCM=546;
const state={startedAt:performance.now(),gain:1e9,audio:null,osc:null,amp:null,audioOn:false,raf:0};

function q(id){return document.getElementById(id)}
function setText(id,value){const e=q(id);if(e)e.textContent=value}
function fmtResidue(v,n){return String(v).padStart(String(n-1).length,"0")+"/"+String(n-1)}
function marker(id,turn){
  const e=q(id);if(!e)return;
  const a=turn*Math.PI*2-Math.PI/2,r=Number(e.dataset.radius)||70;
  e.setAttribute("cx",(120+Math.cos(a)*r).toFixed(3));
  e.setAttribute("cy",(120+Math.sin(a)*r).toFixed(3));
}
function render(now){
  const elapsed=Math.max(0,(now-state.startedAt)/1000);
  const ticks=elapsed*EXACT_HZ;
  const beat=Math.floor(ticks);
  const frac=ticks-beat;
  const r6=beat%6,r7=beat%7,r13=beat%13,phase=beat%CYCLE_LCM;
  marker("lifeClockDot6",((r6+frac)/6)%1);
  marker("lifeClockDot7",((r7+frac)/7)%1);
  marker("lifeClockDot13",((r13+frac)/13)%1);
  setText("lifeClockPhase",String(phase).padStart(3,"0")+"/545");
  setText("lifeClockR6",fmtResidue(r6,6));
  setText("lifeClockR7",fmtResidue(r7,7));
  setText("lifeClockR13",fmtResidue(r13,13));
  setText("lifeClockTicks",beat.toLocaleString("fr-CA"));
  const dust=Number(DUST_TEXT)*state.gain;
  setText("lifeClockDustGain","×10^"+Math.round(Math.log10(state.gain)));
  setText("lifeClockDustVisual",dust.toExponential(8));
  const bar=q("lifeClockDustBar");
  if(bar){
    const p=Math.max(0,Math.min(100,Math.log10(1+Math.abs(dust))*18));
    bar.style.width=p.toFixed(2)+"%";
  }
  state.raf=requestAnimationFrame(render);
}
function updateGain(g){
  state.gain=g;
  document.querySelectorAll("[data-life-dust-gain]").forEach(b=>b.classList.toggle("active",Number(b.dataset.lifeDustGain)===g));
}
async function startAudio(){
  if(state.audioOn)return;
  const AC=window.AudioContext||window.webkitAudioContext;
  if(!AC){setText("lifeClockAudioState","AUDIO NON SUPPORTÉ");return}
  try{
    if(!state.audio)state.audio=new AC();
    await state.audio.resume();
    const osc=state.audio.createOscillator(),amp=state.audio.createGain();
    osc.type="sine";osc.frequency.setValueAtTime(EXACT_HZ,state.audio.currentTime);
    amp.gain.setValueAtTime(0.028,state.audio.currentTime);
    osc.connect(amp);amp.connect(state.audio.destination);osc.start();
    state.osc=osc;state.amp=amp;state.audioOn=true;
    setText("lifeClockAudioState","SON · ON · 240,1 Hz");
    q("lifeClockAudioStart")?.classList.add("active");
  }catch(err){setText("lifeClockAudioState","AUDIO ERROR")}
}
function stopAudio(){
  if(state.osc){try{state.osc.stop()}catch(_){};try{state.osc.disconnect()}catch(_){}}
  if(state.amp){try{state.amp.disconnect()}catch(_){}}
  state.osc=null;state.amp=null;state.audioOn=false;
  setText("lifeClockAudioState","SON · OFF");
  q("lifeClockAudioStart")?.classList.remove("active");
}
function init(){
  if(!q("LIFE-CLOCK-13-7-6-01"))return;
  setText("lifeClockExact",EXACT_TEXT+" Hz");
  setText("lifeClockNominal",NOMINAL_TEXT+" Hz");
  setText("lifeClockDust",DUST_TEXT+" Hz");
  q("lifeClockAudioStart")?.addEventListener("click",startAudio);
  q("lifeClockAudioStop")?.addEventListener("click",stopAudio);
  document.querySelectorAll("[data-life-dust-gain]").forEach(b=>b.addEventListener("click",()=>updateGain(Number(b.dataset.lifeDustGain))));
  updateGain(1e9);
  state.startedAt=performance.now();
  state.raf=requestAnimationFrame(render);
}
addEventListener("beforeunload",()=>{stopAudio();if(state.raf)cancelAnimationFrame(state.raf)});
if(document.readyState==="loading")addEventListener("DOMContentLoaded",init,{once:true});else init();
})();