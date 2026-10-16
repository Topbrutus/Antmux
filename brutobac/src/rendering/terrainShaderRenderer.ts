/**
 * Custom WebGL Fragment Shader Renderer for Subterranean Soil Grid.
 * Renders visually distinct, procedural textures for Clay, Rock, Mineral, Humus,
 * Crystals, Abyssal Bedrock, and excavated caverns using GLSL procedural noise,
 * fractional Brownian motion (fbm), cellular Voronoi, and distance fields.
 */

import { GRID_WIDTH, GRID_HEIGHT, TILE_SIZE } from '../simulation/grid';
import { MaterialType, TerrainCell } from '../types/terrain';

// Vertex shader: Full-screen quad
const VERTEX_SHADER_SOURCE = `
attribute vec2 a_position;
varying vec2 v_uv;

void main() {
  v_uv = (a_position + 1.0) * 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

// Fragment shader: Procedural subterranean textures based on soil material types
const FRAGMENT_SHADER_SOURCE = `
precision highp float;

varying vec2 v_uv;

uniform vec2 u_resolution;
uniform vec2 u_camera;
uniform float u_zoom;
uniform float u_dpr;
uniform float u_tileSize;
uniform vec2 u_gridSize;
uniform float u_time;
uniform float u_seed;
uniform sampler2D u_gridTexture;
uniform int u_depthViewMode; // 0 = volume, 1 = single
uniform float u_selectedZLayer;
uniform float u_volumeOpacity;

// --- Procedural Noise & Hash Functions ---
float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21) + u_seed * 0.013);
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float hash3D(vec3 p) {
  p = fract(p * vec3(123.34, 456.21, 789.53) + u_seed * 0.017);
  p += dot(p, p + 45.32);
  return fract(p.x * p.y * p.z);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
    u.y
  );
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  vec2 shift = vec2(100.0);
  mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
  for (int i = 0; i < 4; ++i) {
    v += a * noise(p);
    p = rot * p * 2.0 + shift;
    a *= 0.5;
  }
  return v;
}

// 2D Cellular / Voronoi for mineral granules & crystal facets
vec2 voronoi(vec2 p) {
  vec2 n = floor(p);
  vec2 f = fract(p);
  float minDist = 8.0;
  float id = 0.0;
  for (int j = -1; j <= 1; j++) {
    for (int i = -1; i <= 1; i++) {
      vec2 g = vec2(float(i), float(j));
      vec2 o = vec2(hash(n + g), hash(n + g + vec2(13.1, 71.7)));
      vec2 r = g - f + (0.5 + 0.45 * sin(u_time * 0.4 + 6.2831 * o));
      float d = dot(r, r);
      if (d < minDist) {
        minDist = d;
        id = hash(n + g);
      }
    }
  }
  return vec2(sqrt(minDist), id);
}

// Diamond flare star
float diamondStar(vec2 p, float size) {
  p = abs(p);
  float d = (p.x + p.y) - size;
  return smoothstep(0.02, 0.0, d);
}

void main() {
  // Screen space in CSS pixels (inverting Y because WebGL gl_FragCoord.y starts at bottom)
  vec2 screenPos = vec2(gl_FragCoord.x / u_dpr, u_resolution.y - (gl_FragCoord.y / u_dpr));
  // Convert screen coordinates to world pixel space
  vec2 worldPos = (screenPos - u_resolution * 0.5) / u_zoom + u_camera;

  // Grid coordinates
  vec2 gridCoord = worldPos / u_tileSize;
  vec2 cellIndex = floor(gridCoord);
  vec2 cellFract = fract(gridCoord);

  // Bounds check: outside subterranean boundaries
  if (cellIndex.x < 0.0 || cellIndex.x >= u_gridSize.x || cellIndex.y < 0.0 || cellIndex.y >= u_gridSize.y) {
    gl_FragColor = vec4(0.027, 0.031, 0.051, 1.0);
    return;
  }

  // Sample grid state texture (UV coordinates in [0..1])
  vec2 texCoord = (cellIndex + 0.5) / u_gridSize;
  vec4 cellData = texture2D(u_gridTexture, texCoord);

  // Decode cell properties:
  // R: Material ID (0=SURFACE, 1=SOFT_SOIL, 2=HUMUS, 3=CLAY, 4=COMPACT_CLAY, 5=ROCK, 6=MINERAL_ROCK, 7=CRYSTAL_BEARING_ROCK, 8=DEEP_ROCK, 9=CAVITY)
  // G: Excavated (1.0 = AIR/Excavated, 0.0 = Solid)
  // B: Discovered / Revealed (1.0 = Revealed, 0.0 = Fog)
  // A: Hardness / Vein Type (0=normal, 0.25=crystal, 0.5=mineral, 0.75=resin, 1.0=fossil)
  float matId = floor(cellData.r * 255.0 + 0.5);
  bool isExcavated = cellData.g > 0.5;
  bool isRevealed = cellData.b > 0.5;
  float veinType = cellData.a;

  // Neighbor inspection for cavern ambient occlusion and rounded rock contours
  vec4 upData = texture2D(u_gridTexture, (cellIndex + vec2(0.0, -1.0) + 0.5) / u_gridSize);
  vec4 downData = texture2D(u_gridTexture, (cellIndex + vec2(0.0, 1.0) + 0.5) / u_gridSize);
  vec4 leftData = texture2D(u_gridTexture, (cellIndex + vec2(-1.0, 0.0) + 0.5) / u_gridSize);
  vec4 rightData = texture2D(u_gridTexture, (cellIndex + vec2(1.0, 0.0) + 0.5) / u_gridSize);

  bool upAir = upData.g > 0.5;
  bool downAir = downData.g > 0.5;
  bool leftAir = leftData.g > 0.5;
  bool rightAir = rightData.g > 0.5;

  // Micro coordinate inside the specific rock block
  vec2 blockPos = worldPos * 0.45;
  vec3 col = vec3(0.1);

  // ========================================================
  // 1. SURFACE ZONE (Sky, Fertile Topsoil & Turf)
  // ========================================================
  if (cellIndex.y < 7.0) {
    float skyT = clamp(cellIndex.y / 7.0, 0.0, 1.0);
    vec3 skyTop = vec3(0.231, 0.510, 0.965); // #3b82f6
    vec3 skyMid = vec3(0.576, 0.773, 0.992); // #93c5fd
    vec3 skyHaze = vec3(0.749, 0.859, 0.996); // #bfdbfe
    col = mix(mix(skyTop, skyMid, skyT), skyHaze, pow(skyT, 2.2));

    // Sunbeams / crepuscular atmospheric lighting
    float sunBeam = sin((worldPos.x - worldPos.y * 0.6) * 0.04 + u_time * 0.1) * 0.5 + 0.5;
    col += vec3(0.12, 0.11, 0.06) * pow(sunBeam, 4.0);

    // Surface mound slope shadow
    float distToEntrance = abs(worldPos.x - 41.5 * u_tileSize);
    if (distToEntrance < 64.0 && cellIndex.y >= 5.0) {
      col = mix(col, vec3(0.08, 0.05, 0.03), (64.0 - distToEntrance) / 64.0 * 0.75);
    }
  }
  // ========================================================
  // 2. EXCAVATED CAVERN / AIR / SUBTERRANEAN TUNNEL
  // ========================================================
  else if (isExcavated) {
    // Rich dark cavernous floor & ambient occlusion
    vec3 cavityBase = vec3(0.09, 0.065, 0.045); // Deep earthen void #17100b
    float cavityNoise = fbm(worldPos * 0.2);
    col = cavityBase + vec3(0.015, 0.01, 0.005) * cavityNoise;

    // Ambient occlusion drop shadow along top solid rock ceiling
    if (!upAir) {
      float ceilingShadow = smoothstep(0.0, 0.45, cellFract.y);
      col *= mix(0.35, 1.0, ceilingShadow);
    }
    // Packed ant trail pavement along floor
    if (!downAir) {
      float floorShade = smoothstep(1.0, 0.7, cellFract.y);
      col = mix(col, vec3(0.28, 0.17, 0.09), floorShade * 0.35);
    }
    // Subtle lateral rim occlusion
    if (!leftAir) {
      col *= mix(0.55, 1.0, smoothstep(0.0, 0.25, cellFract.x));
    }
    if (!rightAir) {
      col *= mix(0.55, 1.0, smoothstep(1.0, 0.75, cellFract.x));
    }
  }
  // ========================================================
  // 3. SOLID PROCEDURAL SOIL TYPES (CLAY vs ROCK vs MINERAL vs HUMUS vs DEEP)
  // ========================================================
  else {
    // --- Material A: CLAY / COMPACT_CLAY (Wavy silt sedimentation & terracotta sheen) ---
    if (matId == 3.0 || matId == 4.0) {
      // Sinusoidal ductile shear wave turbulence
      float siltWave = sin(worldPos.y * 0.38 + fbm(worldPos * 0.09) * 5.2);
      float microSilt = sin(worldPos.y * 1.8 + worldPos.x * 0.35) * 0.15;
      float clayBlend = clamp(siltWave * 0.5 + 0.5 + microSilt, 0.0, 1.0);

      // Terracotta gradient: warm ochre #b46738 to burnt terracotta #9a3412 to rich sienna #c2410c
      vec3 clayLight = vec3(0.706, 0.404, 0.220); // #b46738
      vec3 clayDark  = vec3(0.604, 0.204, 0.071); // #9a3412
      vec3 clayDeep  = vec3(0.761, 0.255, 0.047); // #c2410c

      if (matId == 4.0) {
        // Compact clay: higher density iron oxide banding
        clayLight = vec3(0.620, 0.240, 0.080);
        clayDark  = vec3(0.480, 0.140, 0.040);
        clayDeep  = vec3(0.850, 0.350, 0.080);
      }

      col = mix(clayLight, clayDark, clayBlend);
      col = mix(col, clayDeep, pow(fbm(worldPos * 0.18), 2.0) * 0.45);

      // Ductile silky clay sheen highlight on block edges
      float edgeHighlight = smoothstep(0.05, 0.0, cellFract.y) * 0.18;
      col += vec3(edgeHighlight);
    }
    // --- Material B: ROCK / METAMORPHIC SLATE (Schist cleavage, quartz veins & mica glints) ---
    else if (matId == 5.0) {
      // Angular cleavage planes: sharp metamorphic schist fissures
      float schistAngle = (worldPos.y * 0.28 + worldPos.x * 0.12) + fbm(worldPos * 0.14) * 2.8;
      float schistGrain = abs(sin(schistAngle));
      float fractureLine = smoothstep(0.08, 0.0, abs(fract(schistAngle * 0.5) - 0.5));

      // Slate palette: charcoal #334155, steel slate #475569, ash mineral #64748b
      vec3 slateDark  = vec3(0.18, 0.21, 0.28);
      vec3 slateMid   = vec3(0.28, 0.33, 0.41);
      vec3 slateLight = vec3(0.40, 0.46, 0.54);

      col = mix(slateDark, slateMid, schistGrain);
      col = mix(col, slateLight, fbm(worldPos * 0.22) * 0.6);
      col -= vec3(0.12) * fractureLine; // Fracture shadow cracks

      // Quartz & mica crystalline flakes (sparkling high-frequency specks)
      float micaSparkle = step(0.94, hash(floor(worldPos * 0.85)));
      col += vec3(0.35, 0.38, 0.45) * micaSparkle;
    }
    // --- Material C: MINERAL_ROCK (Metallic ore nuggets, brassy pyrite & hematite veins) ---
    else if (matId == 6.0 || veinType > 0.35 && veinType < 0.65) {
      // Dark graphite base rock
      vec3 baseRock = vec3(0.16, 0.18, 0.22);
      float oreNoise = fbm(worldPos * 0.25);
      col = mix(baseRock, vec3(0.25, 0.28, 0.35), oreNoise);

      // Metallic cellular ore pockets (Voronoi cellular metallic luster)
      vec2 v = voronoi(worldPos * 0.4);
      float cellBorder = smoothstep(0.05, 0.25, v.x);

      // Pyrite brass gold #d97706 and silver hematite #cbd5e1 ore streaks
      vec3 pyriteGold   = vec3(0.85, 0.68, 0.22);
      vec3 silverGalena = vec3(0.82, 0.86, 0.92);

      float oreMix = fbm(worldPos * 0.3 + 17.4);
      vec3 metallicColor = mix(pyriteGold, silverGalena, step(0.5, oreMix));

      // Specular directional metallic glint
      vec2 glintDir = normalize(vec2(1.0, 1.0));
      float glint = pow(max(0.0, dot(normalize(cellFract - 0.5), glintDir)), 8.0) * 0.6;

      if (v.x < 0.45) {
        col = mix(metallicColor + vec3(glint), col, cellBorder);
      }
    }
    // --- Material D: CRYSTAL_BEARING_ROCK (Multi-faceted prismatic spires & bioluminescent glow) ---
    else if (matId == 7.0 || veinType > 0.15 && veinType < 0.35) {
      // Dark crystalline slate bedrock
      bool isAmethyst = cellIndex.y > 90.0;
      vec3 crystalBase = isAmethyst ? vec3(0.11, 0.08, 0.18) : vec3(0.07, 0.12, 0.22);
      col = mix(crystalBase, vec3(0.03, 0.04, 0.08), fbm(worldPos * 0.15));

      // Hexagonal / Prismatic crystal facet distance field
      vec2 v = voronoi(worldPos * 0.5);
      float facetEdge = smoothstep(0.02, 0.12, v.x);

      // Bioluminescent crystal colors
      vec3 gemCyanCore  = vec3(0.22, 0.74, 0.97); // #38bdf8
      vec3 gemCyanGleam = vec3(0.88, 0.96, 1.00); // #e0f2fe
      vec3 gemPurpleCore  = vec3(0.75, 0.52, 0.99); // #c084fc
      vec3 gemPurpleGleam = vec3(0.95, 0.90, 1.00); // #f3e8ff

      vec3 coreCol  = isAmethyst ? gemPurpleCore : gemCyanCore;
      vec3 gleamCol = isAmethyst ? gemPurpleGleam : gemCyanGleam;

      // Pulsing internal refraction caustics
      float pulse = sin(u_time * 2.5 + worldPos.x * 0.4 + worldPos.y * 0.6) * 0.25 + 0.75;
      coreCol *= pulse;

      // Render crystal facet
      if (v.x < 0.55) {
        col = mix(coreCol, col, facetEdge * 0.75);
        // Diamond reflection facet line
        if (v.x < 0.18) {
          col = mix(col, gleamCol, 0.85);
        }
      }

      // Rotating diamond sparkle flare on crystal center
      vec2 centerDelta = cellFract - vec2(0.5, 0.45);
      float flare = diamondStar(centerDelta * 3.5, 0.45 * pulse);
      col += gleamCol * flare * 0.9;
    }
    // --- Material E: HUMUS / SOFT_SOIL (Rich organic loam, roots & mulch granularity) ---
    else if (matId == 1.0 || matId == 2.0 || matId == 0.0) {
      // Organic crumbly soil multi-octave FBM
      float earthNoise = fbm(worldPos * 0.35);
      float fineCrumb  = hash(floor(worldPos * 1.5)) * 0.22;

      // Rich humus tones #54361e to dark mulch #3d2412
      vec3 humusLight = vec3(0.33, 0.21, 0.12);
      vec3 humusDark  = vec3(0.22, 0.14, 0.07);

      col = mix(humusLight, humusDark, earthNoise) + vec3(fineCrumb);

      // Fine organic rootlets winding through the soil
      float rootlet = abs(sin(worldPos.x * 0.3 + fbm(worldPos * 0.2) * 4.0));
      if (rootlet < 0.08) {
        col = mix(col, vec3(0.48, 0.32, 0.16), 0.6);
      }
    }
    // --- Material F: DEEP_ROCK / ABYSSAL BEDROCK (Pitch obsidian with glowing energy cracks) ---
    else {
      // Dark volcanic obsidian matrix
      vec3 obsidianBase = vec3(0.045, 0.040, 0.075);
      col = mix(obsidianBase, vec3(0.02, 0.015, 0.035), fbm(worldPos * 0.12));

      // Deep cooling micro-cracks
      vec2 v = voronoi(worldPos * 0.28);
      float crack = smoothstep(0.04, 0.0, v.x);

      // Deep magmatic purple/electric violet energy pulsing in fractures
      float energyPulse = sin(u_time * 1.8 + worldPos.y * 0.25) * 0.35 + 0.65;
      vec3 fissureGlow = vec3(0.45, 0.20, 0.95) * energyPulse;
      col = mix(col, fissureGlow, crack * 0.85);
    }

    // 3D Block Bevel / Chipped edge relief bordering excavated air
    if (upAir) {
      col += vec3(0.08); // Top edge rim highlight
    }
    if (downAir) {
      col *= 0.65; // Bottom edge shadow
    }
    if (leftAir || rightAir) {
      col *= 0.85;
    }
  }

  // ========================================================
  // 4. SUBTERRANEAN DEPTH VOLUMETRIC OPACITY & STRATIFICATION
  // ========================================================
  if (cellIndex.y >= 7.0) {
    if (u_depthViewMode == 1) {
      // Single Layer Slice mode: isolate selected Z layer
      float depthDiff = abs(cellIndex.y - u_selectedZLayer);
      if (depthDiff > 0.5) {
        float dimFactor = min(0.88, 0.35 + depthDiff * 0.14);
        col *= (1.0 - dimFactor);
      } else {
        // Highlight active layer slice
        col += vec3(0.12, 0.09, 0.02);
      }
    } else {
      // Volume mode: depth-based optical attenuation
      float depthRatio = clamp((cellIndex.y - 7.0) / 84.0, 0.0, 1.0);
      float depthDim = depthRatio * 0.38 * u_volumeOpacity;
      col *= (1.0 - depthDim);
    }
  }

  // ========================================================
  // 6. POST-PROCESSING: DEPTH SATURATION GRADIENT & LITHIC COLOR GRADING
  // ========================================================
  if (cellIndex.y >= 7.0 && isRevealed) {
    float totalSubDepth = max(1.0, u_gridSize.y - 7.0);
    float depthRatio = clamp((cellIndex.y - 7.0) / totalSubDepth, 0.0, 1.0);

    // Standard perceptual luminance (Rec. 709)
    float lum = dot(col, vec3(0.299, 0.587, 0.114));

    // Continuous depth saturation curve:
    // - Top soils (0.0 to 0.22): warm, vibrant organic earth (saturation up to 1.25)
    // - Mid depths (0.22 to 0.65): cool mineral desaturation (down to 0.72) for harsh stone
    // - Deep strata (0.65 to 1.0): dark obsidian rock with high-contrast glowing veins
    float baseSat = mix(1.22, 0.70, smoothstep(0.12, 0.60, depthRatio));

    // Selective vibrancy boost for precious minerals and bioluminescent crystals
    bool isLuminousMaterial = (matId == 7.0 || matId == 6.0 || (veinType > 0.15 && veinType < 0.65));
    if (isLuminousMaterial) {
      // Keep crystals and gold/silver veins hyper-saturated and vibrant even in the darkest abyss
      baseSat = mix(baseSat, 1.48, 0.85);
    }

    // Apply saturation gradient
    col = mix(vec3(lum), col, baseSat);

    // Depth-based lithic atmospheric color grading (abyssal cool tint)
    vec3 deepLithicTint = vec3(0.015, 0.025, 0.055) * pow(depthRatio, 1.6);
    col += deepLithicTint;
  }

  // ========================================================
  // 7. DEEP MINERAL DUST PARTICLES (PROCEDURAL FLOATING MOTES)
  // ========================================================
  // Visible in excavated chambers, galleries, and fissures below the upper soil layers
  if (cellIndex.y > 22.0 && isExcavated && isRevealed) {
    float deepDustFactor = clamp((cellIndex.y - 22.0) / 65.0, 0.0, 1.0);

    // Swirling dust coordinate field driven by time and micro-currents
    vec2 dustField = worldPos * 0.18 + vec2(
      sin(u_time * 0.35 + worldPos.y * 0.08) * 1.6,
      -u_time * 0.42 + cos(u_time * 0.25 + worldPos.x * 0.06) * 0.8
    );
    vec2 dCell = floor(dustField);
    vec2 dFract = fract(dustField);
    float dRand = hash(dCell);

    // Spawn floating mineral dust specks (top 20% of hash cells)
    if (dRand > 0.80) {
      vec2 speckOffset = vec2(hash(dCell + 1.37), hash(dCell + 2.89));
      float distToSpeck = length(dFract - speckOffset);
      float speckRadius = 0.038 + 0.045 * hash(dCell + 5.17);
      float speckGlow = smoothstep(speckRadius, 0.0, distToSpeck);

      // Shimmering twinkle animation
      float twinkle = sin(u_time * 3.4 + dRand * 38.0) * 0.45 + 0.55;

      // Geological dust composition based on depth and proximity to crystal/mineral strata:
      // - Upper rock (y: 22-60): gold pyrite & quartz mica glints (#f59e0b to #e2e8f0)
      // - Deep & abyssal rock (y: 60-124): cyan/violet bioluminescent crystal dust (#38bdf8 to #c084fc)
      vec3 goldMicaDust = vec3(0.96, 0.82, 0.42);
      vec3 deepCrystalDust = (cellIndex.y > 88.0) ? vec3(0.82, 0.52, 1.0) : vec3(0.32, 0.85, 1.0);
      vec3 dustColor = mix(goldMicaDust, deepCrystalDust, smoothstep(0.35, 0.85, deepDustFactor));

      col += dustColor * speckGlow * twinkle * deepDustFactor * 0.95;
    }
  }

  // ========================================================
  // 8. FOG OF WAR / DISCOVERY VEIL
  // ========================================================
  if (!isRevealed && cellIndex.y >= 7.0) {
    // Smooth obscurity with faint ambient crystal bleed
    vec3 fogColor = vec3(0.020, 0.022, 0.035);
    // If adjacent to crystal, subtle tantalizing bioluminescent shimmer leaks through
    if (veinType > 0.15 && veinType < 0.35) {
      float shimmer = sin(u_time * 2.0 + worldPos.x + worldPos.y) * 0.04 + 0.05;
      fogColor += vec3(0.02, 0.06, 0.09) * shimmer;
    }
    col = fogColor;
  }

  gl_FragColor = vec4(col, 1.0);
}
`;

export interface TerrainShaderRendererOptions {
  worldSeed?: number;
}

export class TerrainShaderRenderer {
  private gl: WebGLRenderingContext | null = null;
  private program: WebGLProgram | null = null;
  private quadBuffer: WebGLBuffer | null = null;
  private gridTexture: WebGLTexture | null = null;
  private textureData: Uint8Array;
  private startTime: number = performance.now();
  private isSupported: boolean = true;

  // Uniform locations
  private uResolution: WebGLUniformLocation | null = null;
  private uCamera: WebGLUniformLocation | null = null;
  private uZoom: WebGLUniformLocation | null = null;
  private uDpr: WebGLUniformLocation | null = null;
  private uTileSize: WebGLUniformLocation | null = null;
  private uGridSize: WebGLUniformLocation | null = null;
  private uTime: WebGLUniformLocation | null = null;
  private uSeed: WebGLUniformLocation | null = null;
  private uGridTexture: WebGLUniformLocation | null = null;
  private uDepthViewMode: WebGLUniformLocation | null = null;
  private uSelectedZLayer: WebGLUniformLocation | null = null;
  private uVolumeOpacity: WebGLUniformLocation | null = null;

  constructor(options: TerrainShaderRendererOptions = {}) {
    this.textureData = new Uint8Array(GRID_WIDTH * GRID_HEIGHT * 4);
  }

  public init(canvas: HTMLCanvasElement, worldSeed: number = 3861): boolean {
    try {
      this.gl =
        canvas.getContext('webgl', {
          alpha: false,
          depth: false,
          stencil: false,
          antialias: false,
          preserveDrawingBuffer: false,
        }) ||
        (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);

      if (!this.gl) {
        this.isSupported = false;
        return false;
      }

      const gl = this.gl;

      // Compile Shaders
      const vertShader = this.compileShader(gl.VERTEX_SHADER, VERTEX_SHADER_SOURCE);
      const fragShader = this.compileShader(gl.FRAGMENT_SHADER, FRAGMENT_SHADER_SOURCE);

      if (!vertShader || !fragShader) {
        this.isSupported = false;
        return false;
      }

      this.program = gl.createProgram();
      if (!this.program) return false;

      gl.attachShader(this.program, vertShader);
      gl.attachShader(this.program, fragShader);
      gl.linkProgram(this.program);

      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
        console.error('Shader program link failed:', gl.getProgramInfoLog(this.program));
        this.isSupported = false;
        return false;
      }

      gl.useProgram(this.program);

      // Setup Full-Screen Quad Buffer
      this.quadBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, this.quadBuffer);
      const quadVertices = new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0,
      ]);
      gl.bufferData(gl.ARRAY_BUFFER, quadVertices, gl.STATIC_DRAW);

      const aPosition = gl.getAttribLocation(this.program, 'a_position');
      gl.enableVertexAttribArray(aPosition);
      gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0);

      // Uniform Locations
      this.uResolution = gl.getUniformLocation(this.program, 'u_resolution');
      this.uCamera = gl.getUniformLocation(this.program, 'u_camera');
      this.uZoom = gl.getUniformLocation(this.program, 'u_zoom');
      this.uDpr = gl.getUniformLocation(this.program, 'u_dpr');
      this.uTileSize = gl.getUniformLocation(this.program, 'u_tileSize');
      this.uGridSize = gl.getUniformLocation(this.program, 'u_gridSize');
      this.uTime = gl.getUniformLocation(this.program, 'u_time');
      this.uSeed = gl.getUniformLocation(this.program, 'u_seed');
      this.uGridTexture = gl.getUniformLocation(this.program, 'u_gridTexture');
      this.uDepthViewMode = gl.getUniformLocation(this.program, 'u_depthViewMode');
      this.uSelectedZLayer = gl.getUniformLocation(this.program, 'u_selectedZLayer');
      this.uVolumeOpacity = gl.getUniformLocation(this.program, 'u_volumeOpacity');

      // Setup Grid Data Texture
      this.gridTexture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, this.gridTexture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);

      // Initialize empty texture
      gl.texImage2D(
        gl.TEXTURE_2D,
        0,
        gl.RGBA,
        GRID_WIDTH,
        GRID_HEIGHT,
        0,
        gl.RGBA,
        gl.UNSIGNED_BYTE,
        this.textureData
      );

      this.isSupported = true;
      return true;
    } catch (err) {
      console.warn('WebGL Terrain Shader initialization fallback:', err);
      this.isSupported = false;
      return false;
    }
  }

  public getIsSupported(): boolean {
    return this.isSupported;
  }

  /**
   * Updates the GPU texture with the latest state of the subterranean grid cells.
   */
  public updateGridData(
    cellsOrTiles: TerrainCell[][] | string[][],
    revealed?: boolean[][],
    hardness?: number[][]
  ) {
    if (!this.gl || !this.gridTexture || !this.isSupported) return;

    const isTerrainCellGrid =
      Array.isArray(cellsOrTiles) &&
      cellsOrTiles.length > 0 &&
      cellsOrTiles[0]?.length > 0 &&
      typeof cellsOrTiles[0][0] === 'object' &&
      cellsOrTiles[0][0] !== null &&
      'material_type' in (cellsOrTiles[0][0] as any);

    for (let y = 0; y < GRID_HEIGHT; y++) {
      for (let x = 0; x < GRID_WIDTH; x++) {
        const idx = (y * GRID_WIDTH + x) * 4;
        let matId = 2; // Default HUMUS
        let isExcavated = 0;
        let isRev = revealed?.[y]?.[x] || false;
        let veinCode = 0;

        if (isTerrainCellGrid) {
          const cell = (cellsOrTiles as TerrainCell[][])[y]?.[x];
          if (cell) {
            isExcavated = cell.excavated ? 255 : 0;
            isRev = cell.discovered || isRev;
            switch (cell.material_type) {
              case 'SURFACE':
                matId = 0;
                break;
              case 'SOFT_SOIL':
                matId = 1;
                break;
              case 'HUMUS':
                matId = 2;
                break;
              case 'CLAY':
                matId = 3;
                break;
              case 'COMPACT_CLAY':
                matId = 4;
                break;
              case 'ROCK':
                matId = 5;
                break;
              case 'MINERAL_ROCK':
                matId = 6;
                veinCode = 128;
                break;
              case 'CRYSTAL_BEARING_ROCK':
                matId = 7;
                veinCode = 64;
                break;
              case 'DEEP_ROCK':
                matId = 8;
                break;
              case 'NATURAL_CAVITY':
                matId = 9;
                isExcavated = 255;
                break;
              default:
                matId = 2;
                break;
            }
            if (cell.resource_type === 'crystal') {
              veinCode = 64;
            } else if (cell.resource_type === 'mineral') {
              veinCode = 128;
            } else if (cell.resource_type === 'resin') {
              veinCode = 192;
            } else if (cell.resource_type === 'dirt') {
              veinCode = 32;
            }
          }
        } else {
          const tile = (cellsOrTiles as string[][])[y]?.[x] || 'DIRT_HUMUS';
          if (tile === 'SURFACE_AIR' || (y < 7 && tile === 'AIR')) {
            matId = 0;
            isExcavated = 255;
          } else if (tile === 'AIR') {
            matId = 9; // Natural Cavity / Carved Air
            isExcavated = 255;
          } else if (tile === 'SURFACE_GRASS') {
            matId = 0;
          } else if (tile === 'DIRT_HUMUS') {
            matId = y <= 16 ? 1 : 2; // 1 = SOFT_SOIL, 2 = HUMUS
          } else if (tile === 'CLAY_DENSE') {
            matId = y <= 42 ? 3 : 4; // 3 = CLAY, 4 = COMPACT_CLAY
          } else if (tile === 'STONE_MINERAL') {
            matId = 5; // ROCK
          } else if (tile === 'DEEP_CRYSTAL_SLATE') {
            matId = 7; // CRYSTAL_BEARING_ROCK
            veinCode = 64; // Crystal presence
          } else if (tile === 'ABYSSAL_BEDROCK') {
            matId = 8; // DEEP_ROCK
          } else if (tile === 'VEIN_CRYSTAL') {
            matId = 7; // CRYSTAL_BEARING_ROCK
            veinCode = 64; // Crystal
          } else if (tile === 'VEIN_MINERAL') {
            matId = 6; // MINERAL_ROCK
            veinCode = 128; // Mineral
          } else if (tile === 'VEIN_ORGANIC') {
            matId = 2; // Humus organic
            veinCode = 192; // Resin
          } else if (tile === 'VEIN_FOSSIL') {
            matId = 8; // Deep fossil
            veinCode = 255; // Fossil
          }
        }

        // RGBA Texture Channels:
        this.textureData[idx] = matId; // R: Material Type ID
        this.textureData[idx + 1] = isExcavated; // G: Excavated flag (255 = Air, 0 = Solid)
        this.textureData[idx + 2] = isRev ? 255 : 0; // B: Revealed flag (255 = Revealed, 0 = Fog)
        this.textureData[idx + 3] = veinCode; // A: Vein / Resource code
      }
    }

    const gl = this.gl;
    gl.bindTexture(gl.TEXTURE_2D, this.gridTexture);
    gl.texSubImage2D(
      gl.TEXTURE_2D,
      0,
      0,
      0,
      GRID_WIDTH,
      GRID_HEIGHT,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      this.textureData
    );
  }

  /**
   * Renders the subterranean procedural soil grid via GLSL fragment shader.
   */
  public render(
    canvas: HTMLCanvasElement,
    camera: { x: number; y: number; zoom: number },
    dpr: number,
    depthViewMode: 'volume' | 'single',
    selectedZLayer: number,
    volumeOpacity: number,
    worldSeed: number = 3861
  ) {
    if (!this.gl || !this.program || !this.isSupported) return;

    const gl = this.gl;
    const clientW = canvas.clientWidth;
    const clientH = canvas.clientHeight;
    const targetW = Math.floor(clientW * dpr);
    const targetH = Math.floor(clientH * dpr);

    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }

    gl.viewport(0, 0, targetW, targetH);
    gl.useProgram(this.program);

    // Update Uniforms
    gl.uniform2f(this.uResolution, clientW, clientH);
    gl.uniform2f(this.uCamera, camera.x, camera.y);
    gl.uniform1f(this.uZoom, camera.zoom);
    gl.uniform1f(this.uDpr, dpr);
    gl.uniform1f(this.uTileSize, TILE_SIZE);
    gl.uniform2f(this.uGridSize, GRID_WIDTH, GRID_HEIGHT);

    const currentTime = (performance.now() - this.startTime) / 1000.0;
    gl.uniform1f(this.uTime, currentTime);
    gl.uniform1f(this.uSeed, worldSeed);

    gl.uniform1i(this.uDepthViewMode, depthViewMode === 'single' ? 1 : 0);
    gl.uniform1f(this.uSelectedZLayer, selectedZLayer);
    gl.uniform1f(this.uVolumeOpacity, volumeOpacity);

    // Bind texture unit 0
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.gridTexture);
    gl.uniform1i(this.uGridTexture, 0);

    // Draw full-screen quad
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  }

  private compileShader(type: number, source: string): WebGLShader | null {
    if (!this.gl) return null;
    const shader = this.gl.createShader(type);
    if (!shader) return null;

    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);

    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', this.gl.getShaderInfoLog(shader));
      this.gl.deleteShader(shader);
      return null;
    }

    return shader;
  }

  public destroy() {
    if (!this.gl) return;
    if (this.program) this.gl.deleteProgram(this.program);
    if (this.quadBuffer) this.gl.deleteBuffer(this.quadBuffer);
    if (this.gridTexture) this.gl.deleteTexture(this.gridTexture);
    this.gl = null;
  }
}
