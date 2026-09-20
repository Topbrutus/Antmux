(() => {
  "use strict";

  const CHANNELS = [
    "yellow_outer","blue_second","mauve_third","rose_inner",
    "red_tint","gray_filter","white_reflection","black_stripes"
  ];

  const groups = [
    {
      id:"conscience",
      label:"CONSCIENCE",
      status:"CONFIRMED_LABELS",
      states:[
        {id:"endormi",label:"Endormi",weights:{gray_filter:.55,mauve_third:.24,white_reflection:.12}},
        {id:"meditatif",label:"Méditatif",weights:{mauve_third:.72,blue_second:.20,gray_filter:.12,white_reflection:.30}},
        {id:"reveille",label:"Réveillé",weights:{blue_second:.66,yellow_outer:.24,white_reflection:.50}}
      ]
    },
    {
      id:"engagement",
      label:"ENGAGEMENT",
      status:"CANDIDATE_LABELS",
      states:[
        {id:"indifferent",label:"Indifférent",weights:{gray_filter:.24,white_reflection:.18}},
        {id:"curieux",label:"Curieux",weights:{blue_second:.72,mauve_third:.24,white_reflection:.46}},
        {id:"excite",label:"Excité",weights:{rose_inner:.82,blue_second:.46,white_reflection:.62}}
      ]
    },
    {
      id:"regulation",
      label:"RÉGULATION",
      status:"CANDIDATE_LABELS",
      states:[
        {id:"calme",label:"Calme",weights:{blue_second:.34,mauve_third:.30,gray_filter:.08,white_reflection:.30}},
        {id:"concentre",label:"Concentré",weights:{blue_second:.86,yellow_outer:.16,white_reflection:.54}},
        {id:"enerve",label:"Énervé",weights:{yellow_outer:.66,rose_inner:.54,black_stripes:.36,white_reflection:.52}}
      ]
    },
    {
      id:"temperament",
      label:"TEMPÉRAMENT",
      status:"CONFIRMED_LABELS",
      states:[
        {id:"apaise",label:"Apaisé",weights:{blue_second:.24,mauve_third:.36,gray_filter:.08,white_reflection:.28}},
        {id:"determine",label:"Déterminé",weights:{yellow_outer:.76,blue_second:.62,white_reflection:.56,black_stripes:.24}},
        {id:"fache",label:"Fâché",weights:{yellow_outer:.86,rose_inner:.24,red_tint:.96,black_stripes:.58,white_reflection:.48}}
      ]
    }
  ];

  const stateIndex = new Map();
  groups.forEach(group=>{
    group.states.forEach(state=>stateIndex.set(state.id,{...state,group_id:group.id}));
  });

  function clamp01(value){
    return Math.max(0,Math.min(1,Number(value)||0));
  }
  function emptyOutput(){
    return {
      yellow_outer:0, blue_second:0, mauve_third:0, rose_inner:0,
      red_tint:0, gray_filter:0, white_reflection:0, black_stripes:0
    };
  }

  function blend(strengths={}){
    const out=emptyOutput();
    for(const channel of CHANNELS){
      let remaining=1;
      for(const [stateId,rawStrength] of Object.entries(strengths)){
        const state=stateIndex.get(stateId);
        if(!state) continue;
        const strength=clamp01(rawStrength);
        const weight=clamp01(state.weights?.[channel]||0);
        remaining *= (1-strength*weight);
      }
      out[channel]=1-remaining;
    }
    out.white_reflection=Math.max(.35,out.white_reflection);
    out.black_stripes=Math.max(.20,out.black_stripes);
    return out;
  }

  function defaults(){
    const values={};
    groups.forEach(group=>group.states.forEach(state=>{values[state.id]=0;}));
    return values;
  }
  function validate(){
    if(groups.length!==4) return false;
    if(groups.some(group=>group.states.length!==3)) return false;
    const ids=new Set();
    for(const group of groups){
      for(const state of group.states){
        if(ids.has(state.id)) return false;
        ids.add(state.id);
        for(const [channel,value] of Object.entries(state.weights||{})){
          if(!CHANNELS.includes(channel)) return false;
          if(!Number.isFinite(value)||value<0||value>1) return false;
        }
      }
    }
    return ids.size===12;
  }

  window.X72EmotionMap={
    schema:"ANTMUX-X72-EMOTION-MAP-v0.1",
    status:"CANDIDATE_TUNABLE",
    authority:"VISUAL_ONLY",
    groups,
    channels:[...CHANNELS],
    defaults,
    blend,
    validate
  };
})();
