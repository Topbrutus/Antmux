const ROLES = ['Fourmi','Abeille','Scarabée','Papillon','Mante','Libellule','Termite'];

async function sha256Bytes(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return new Uint8Array(digest);
}

function first64(bytes) {
  let n = 0n;
  for (let i = 0; i < 8; i += 1) n = (n << 8n) | BigInt(bytes[i]);
  return n;
}

self.onmessage = async (event) => {
  const { seed, roleIndex, worldZ, timePhase } = event.data;
  const role = ROLES[roleIndex] || `Worker-${roleIndex}`;
  const material = `${seed}|${roleIndex}|${role}|Z${worldZ}|T${timePhase}|273|2401|637|571429`;
  const bytes = await sha256Bytes(material);
  const n = first64(bytes);

  const raw = Number(n % 1_000_000n) + 1;
  const phaseOffset = Number(n % 273n);
  const address = Number((n / 273n) % 2401n);
  const lane = Number((n / 2401n) % 637n);

  self.postMessage({ roleIndex, role, raw, phaseOffset, address, lane });
};
