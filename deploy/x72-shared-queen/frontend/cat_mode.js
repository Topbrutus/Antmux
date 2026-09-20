(() => {
  "use strict";

  const COLORS = {
    bg:"#05070C", grid:"#172333", text:"#F2F5F8", muted:"#8795A8",
    yellow:"#F6B94A", blue:"#39D8FF", mauve:"#8B5CFF",
    rose:"#E65BFF", white:"#FFFFFF", red:"#FF557A"
  };

  function clamp01(value){
    return Math.max(0,Math.min(1,Number(value)||0));
  }

  function seeded(seed){
    let t=seed>>>0;
    return ()=>{
      t += 0x6D2B79F5;
      let r=Math.imul(t^(t>>>15),1|t);
      r ^= r + Math.imul(r^(r>>>7),61|r);
      return ((r^(r>>>14))>>>0)/4294967296;
    };
  }
  function serverRender(state){
    return state?.z3_runtime?.latest?.eye_render || null;
  }

  function emotionMix(cal){
    if(!window.X72EmotionMap?.blend) return {};
    return window.X72EmotionMap.blend(cal?.emotions || {});
  }

  function mergedBoosts(state,cal){
    const native=serverRender(state)?.native_boosts || {};
    const preview=cal?.boosts || {};
    const emotion=emotionMix(cal);
    return {
      yellow_outer:Math.max(clamp01(native.yellow_outer),clamp01(preview.yellow_outer),clamp01(emotion.yellow_outer)),
      blue_second:Math.max(clamp01(native.blue_second),clamp01(preview.blue_second),clamp01(emotion.blue_second)),
      mauve_third:Math.max(clamp01(native.mauve_third),clamp01(preview.mauve_third),clamp01(emotion.mauve_third)),
      rose_inner:Math.max(clamp01(native.rose_inner),clamp01(preview.rose_inner),clamp01(emotion.rose_inner))
    };
  }

  function overlayValues(state,cal){
    const overlays=serverRender(state)?.overlays || {};
    const emotion=emotionMix(cal);
    return {
      red_tint:Math.max(clamp01(overlays.red_tint),clamp01(emotion.red_tint)),
      gray_filter:Math.max(clamp01(overlays.gray_filter),clamp01(emotion.gray_filter)),
      white_reflection:Math.max(clamp01(overlays.white_reflection ?? .35),clamp01(emotion.white_reflection)),
      black_stripes:Math.max(clamp01(overlays.black_stripes ?? .20),clamp01(emotion.black_stripes))
    };
  }

  function rgba(hex,alpha){
    const raw=hex.replace("#","");
    const n=parseInt(raw,16);
    const r=(n>>16)&255,g=(n>>8)&255,b=n&255;
    return "rgba("+r+","+g+","+b+","+clamp01(alpha)+")";
  }
  function drawRing(ctx,radius,width,color,base,boost){
    const alpha=Math.min(1,base+boost*.72);
    ctx.save();
    ctx.shadowColor=color;
    ctx.shadowBlur=4+boost*24;
    ctx.strokeStyle=rgba(color,alpha);
    ctx.lineWidth=width*(1+boost*.32);
    ctx.beginPath();
    ctx.arc(0,0,radius,0,Math.PI*2);
    ctx.stroke();
    ctx.restore();
  }

  function drawWeb(ctx,radius,color,boost,mirror){
    const alpha=.20+boost*.70;
    ctx.save();
    ctx.strokeStyle=rgba(color,alpha);
    ctx.lineWidth=1+boost*1.6;
    ctx.shadowColor=color;
    ctx.shadowBlur=boost*12;
    const points=12;
    for(let i=0;i<points;i++){
      const a=i*Math.PI*2/points;
      const b=((i*5)%points)*Math.PI*2/points;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a)*radius,Math.sin(a)*radius);
      ctx.lineTo(Math.cos(b)*radius*(mirror?.94:1),Math.sin(b)*radius);
      ctx.stroke();
    }
    ctx.restore();
  }
  function drawCrystals(ctx,radius,color,boost,seed){
    const rnd=seeded(seed);
    ctx.save();
    ctx.strokeStyle=rgba(color,.18+boost*.75);
    ctx.shadowColor=color;
    ctx.shadowBlur=3+boost*16;
    for(let i=0;i<10;i++){
      const a=rnd()*Math.PI*2;
      const rr=radius*(.55+rnd()*.50);
      const x=Math.cos(a)*rr,y=Math.sin(a)*rr;
      const s=2+boost*5+rnd()*3;
      ctx.beginPath();
      ctx.moveTo(x,y-s);
      ctx.lineTo(x+s*.55,y);
      ctx.lineTo(x,y+s);
      ctx.lineTo(x-s*.55,y);
      ctx.closePath();
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawBreathingStripes(ctx,radius,phase,strength){
    if(strength<=0) return;
    const breath=.55+.45*Math.sin(phase*2.2);
    ctx.save();
    ctx.strokeStyle="rgba(0,0,0,"+(.10+strength*.48*breath)+")";
    ctx.lineWidth=1.2+strength*2;
    for(let i=-3;i<=3;i++){
      const x=i*radius*.17;
      const h=radius*(.62-Math.abs(i)*.055);
      ctx.beginPath();
      ctx.moveTo(x,-h);
      ctx.quadraticCurveTo(x+radius*.08,0,x,h);
      ctx.stroke();
    }
    ctx.restore();
  }
  function drawReflection(ctx,radius,strength){
    if(strength<=0) return;
    ctx.save();
    ctx.fillStyle=rgba(COLORS.white,.22+strength*.68);
    ctx.shadowColor=COLORS.white;
    ctx.shadowBlur=4+strength*12;
    ctx.beginPath();
    ctx.ellipse(-radius*.34,-radius*.30,radius*.17,radius*.09,-.4,0,Math.PI*2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(-radius*.12,-radius*.36,radius*.045,0,Math.PI*2);
    ctx.fill();
    ctx.restore();
  }

  function drawEye(ctx,cx,cy,radius,rotation,mirror,boosts,overlays,phase,seed){
    ctx.save();
    ctx.translate(cx,cy);
    ctx.scale(mirror?-1:1,1);
    ctx.rotate(rotation);
    ctx.save();
    ctx.scale(1.46,.88);
    drawCrystals(ctx,radius*1.02,COLORS.yellow,boosts.yellow_outer,seed+11);
    drawCrystals(ctx,radius*.86,COLORS.blue,boosts.blue_second,seed+29);
    drawRing(ctx,radius,6,COLORS.yellow,.42,boosts.yellow_outer);
    drawRing(ctx,radius*.78,5,COLORS.blue,.30,boosts.blue_second);
    drawWeb(ctx,radius*.72,COLORS.blue,boosts.blue_second,mirror);
    drawRing(ctx,radius*.56,4,COLORS.mauve,.24,boosts.mauve_third);
    drawRing(ctx,radius*.34,3,COLORS.rose,.18,boosts.rose_inner);
    if(overlays.red_tint>0){
      ctx.fillStyle=rgba(COLORS.red,overlays.red_tint*.20);
      ctx.beginPath();ctx.arc(0,0,radius*.92,0,Math.PI*2);ctx.fill();
    }
    if(overlays.gray_filter>0){
      ctx.fillStyle="rgba(190,196,205,"+(overlays.gray_filter*.15)+")";
      ctx.beginPath();ctx.arc(0,0,radius*.92,0,Math.PI*2);ctx.fill();
    }

    drawBreathingStripes(ctx,radius*.70,phase,overlays.black_stripes);
    ctx.fillStyle="rgba(0,0,0,.82)";
    ctx.beginPath();
    ctx.ellipse(0,0,radius*.075,radius*.48,0,0,Math.PI*2);
    ctx.fill();
    drawReflection(ctx,radius,overlays.white_reflection);
    ctx.restore();

    ctx.strokeStyle="rgba(255,255,255,.15)";
    ctx.lineWidth=1;
    ctx.beginPath();
    ctx.ellipse(0,0,radius*1.50,radius*.92,0,0,Math.PI*2);
    ctx.stroke();
    ctx.restore();
  }

  function drawGrid(ctx,w,h){
    ctx.fillStyle=COLORS.bg;
    ctx.fillRect(0,0,w,h);
    ctx.strokeStyle=COLORS.grid;
    ctx.lineWidth=1;
    for(let x=0;x<w;x+=40){
      ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();
    }
    for(let y=0;y<h;y+=40){
      ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();
    }
  }

  function draw(ctx,w,h,state,cal,connected=true){
    drawGrid(ctx,w,h);
    const visualTick=Number(state?._visualTick ?? state?.tick_count ?? 0);
    const phase=visualTick*.012;
    const scale=Math.max(.55,Math.min(1.75,Number(cal?.scale)||1));
    const spacing=Math.max(.65,Math.min(1.45,Number(cal?.spacing)||1));
    const dx=Number(cal?.x)||0,dy=Number(cal?.y)||0;
    const cx=w*.5+dx,cy=h*.48+dy;
    const baseR=Math.min(w,h)*.145*scale;
    const eyeGap=Math.min(w,h)*.205*spacing;
    const boosts=mergedBoosts(state,cal);
    const overlays=overlayValues(state,cal);
    const render=serverRender(state);

    const leftRotation=Number.isFinite(Number(render?.left_eye?.rotation_rad))
      ? Number(render.left_eye.rotation_rad)
      : -phase;
    const rightRotation=Number.isFinite(Number(render?.right_eye?.rotation_rad))
      ? Number(render.right_eye.rotation_rad)
      : phase;

    drawEye(ctx,cx-eyeGap,cy,baseR,leftRotation,false,boosts,overlays,phase,72);
    drawEye(ctx,cx+eyeGap,cy,baseR,rightRotation,true,boosts,overlays,phase,144);
    ctx.fillStyle=COLORS.text;
    ctx.font="bold 18px Georgia";
    ctx.textAlign="center";
    ctx.fillText("MODE CHAT — CALIBRATION OCULAIRE",cx,54);
    ctx.fillStyle=COLORS.muted;
    ctx.font="11px Consolas";
    ctx.fillText("Deux animations stéréo • couleur bilatérale • rendu visuel uniquement",cx,74);

    ctx.fillStyle=COLORS.yellow;
    ctx.font="bold 10px Consolas";
    const boostText="Y "+Math.round(boosts.yellow_outer*100)
      +"  B "+Math.round(boosts.blue_second*100)
      +"  M "+Math.round(boosts.mauve_third*100)
      +"  R "+Math.round(boosts.rose_inner*100);
    ctx.fillText(boostText,cx,h-46);

    ctx.fillStyle=COLORS.muted;
    const coordText="X "+dx.toFixed(1)
      +"  Y "+dy.toFixed(1)
      +"  SCALE "+scale.toFixed(3)
      +"  ESP "+spacing.toFixed(3)
      +(cal?.locked?"  • LOCK":"");
    ctx.fillText(coordText,cx,h-28);

    if(!connected){
      ctx.fillStyle="rgba(5,7,12,.62)";
      ctx.fillRect(0,0,w,h);
      ctx.fillStyle=COLORS.red;
      ctx.font="700 22px system-ui";
      ctx.fillText("CORE DISCONNECTED",cx,cy);
    }
  }

  window.X72CatMode={draw};
})();
