"use strict";

const path = require("path");

global.window = {};
require(path.join(__dirname, "..", "frontend", "emotion_map.js"));

const map = global.window.X72EmotionMap;
const checks = [];

function check(name, condition) {
  if (!condition) throw new Error(name);
  checks.push({name, ok:true});
}

check("emotion map exists and validates", Boolean(map) && map.validate());
check("four groups are exposed", map.groups.length === 4);
check("each group is a triad", map.groups.every(group => group.states.length === 3));
check(
  "twelve unique states are exposed",
  new Set(map.groups.flatMap(group => group.states.map(state => state.id))).size === 12
);
const asleep = map.blend({endormi:1});
const meditate = map.blend({meditatif:1});
const awake = map.blend({reveille:1});
check("asleep emphasizes gray over blue", asleep.gray_filter > asleep.blue_second);
check("meditation emphasizes mauve", meditate.mauve_third > meditate.yellow_outer);
check("awake emphasizes blue", awake.blue_second > awake.mauve_third);

const excited = map.blend({excite:1});
check(
  "excited state raises rose and blue together",
  excited.rose_inner > 0.7 && excited.blue_second > 0.4
);

const angry = map.blend({fache:1});
check(
  "angry state uses red overlay plus yellow protection channel",
  angry.red_tint > 0.9 && angry.yellow_outer > 0.8
);
const combined = map.blend({determine:1, excite:1, curieux:.5});
check(
  "multiple states combine without suppressing native channels",
  combined.yellow_outer > 0
  && combined.blue_second > 0
  && combined.rose_inner > 0
);
check(
  "all blended values stay bounded",
  Object.values(combined).every(value => value >= 0 && value <= 1)
);

const zero = map.blend({});
check(
  "neutral preview keeps optical baseline only",
  zero.yellow_outer === 0
  && zero.blue_second === 0
  && zero.mauve_third === 0
  && zero.rose_inner === 0
  && zero.white_reflection === .35
  && zero.black_stripes === .20
);
console.log(JSON.stringify({
  schema:"ANTMUX-X72-EMOTION-MAP-TEST-v0.1",
  checks_total:checks.length,
  checks_passed:checks.length,
  checks
}));
