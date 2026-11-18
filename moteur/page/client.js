/* Client du moteur : mêmes règles entières que le module Python.
   La page ne fait qu'afficher et éditer. Aucun accès serveur. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.MoteurClient = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_.";

  function pgcd(a, b) {
    a = Math.abs(a); b = Math.abs(b);
    while (b) { const t = b; b = a % b; a = t; }
    return a;
  }
  function ppcm(a, b) {
    if (a === 0 || b === 0) return 0;
    return Math.abs((a / pgcd(a, b)) * b);
  }
  function ppcmListe(valeurs) {
    return valeurs.reduce((acc, v) => ppcm(acc, v), 1);
  }
  function periode(vitesse, anneau) {
    return anneau / pgcd(anneau, vitesse);
  }
  function convergence(roues, anneau) {
    const actifs = roues.filter((r) => r.actif).map((r) => r.vitesse);
    if (!actifs.length) return null;
    return ppcmListe(actifs.map((v) => periode(v, anneau)));
  }
  function positionRoue(roue, tic, anneau) {
    const depart = roue.depart % anneau;
    if (!roue.actif) return depart;
    return (depart + roue.vitesse * tic) % anneau;
  }
  function quorum(roues, tic, anneau) {
    const actifs = roues.filter((r) => r.actif);
    if (!actifs.length) return false;
    return actifs.every((r) => positionRoue(r, tic, anneau) === r.depart % anneau);
  }

  function creer(config) {
    return {
      config: config,
      tic: 0,
      phase: config.horloge.phase_depart,
      reste: config.horloge.reste_depart,
      cycles: 0,
      cristaux: 0,
      piles: [],
      anomalie: false,
      dernierPas: null,
    };
  }
  function reduire(etat, niveau) {
    const regle = etat.config.cristallisation;
    if (niveau >= regle.niveau_max) return;
    const file = etat.piles[niveau];
    while (file.length >= regle.seuil) {
      const lot = file.slice(0, regle.seuil);
      const gardes = lot.slice(0, regle.promus);
      if (new Set(gardes).size !== 1) break;
      file.splice(0, regle.seuil, ...lot.slice(regle.promus));
      etat.piles[niveau + 1].push(gardes[0]);
      etat.cristaux += 1;
      reduire(etat, niveau + 1);
    }
  }
  function pas(etat) {
    const h = etat.config.horloge;
    const total = etat.reste + h.phases_par_tour;
    const avance = Math.floor(total / h.frequence_logique_hz);
    etat.reste = total % h.frequence_logique_hz;
    etat.phase = (etat.phase + avance) % h.phases_par_tour;
    etat.dernierPas = avance;
    etat.tic += 1;
    const regle = etat.config.cristallisation;
    while (etat.piles.length <= regle.niveau_max) etat.piles.push([]);
    etat.piles[0].push(etat.anomalie ? "anomalie" : "sain");
    reduire(etat, 0);
    const anneau = etat.config.six_roues.anneau;
    if (etat.tic % anneau === 0 && !etat.anomalie) etat.cycles += 1;
  }
  function rejouer(config, tics, anomalieDes) {
    const etat = creer(config);
    for (let i = 0; i < tics; i += 1) {
      etat.anomalie = anomalieDes != null && etat.tic + 1 >= anomalieDes;
      pas(etat);
    }
    return vue(etat);
  }
  function vue(etat) {
    const config = etat.config;
    const roues = config.six_roues.roues;
    const anneau = config.six_roues.anneau;
    const roches = config.stonehenge.roches;
    const courant = config.stonehenge.courant_amplificateur;
    const cote = config.temple.cote;
    const echo = (roche) => (roche.etat === "installee" ? roche.gain * courant : 0);
    return {
      tic: etat.tic,
      phase: etat.phase,
      reste: etat.reste,
      evolution: Math.floor(etat.tic / anneau),
      cycles_sains: etat.cycles,
      quorum: quorum(roues, etat.tic, anneau),
      convergence: convergence(roues, anneau),
      roche: etat.tic % roches.length,
      pos0: positionRoue(roues[0], etat.tic, anneau),
      cristaux: etat.cristaux,
      resonance: etat.anomalie ? "dissonant" : "harmonieux",
      echo0: echo(roches[0]),
      index_temple: etat.tic % (cote * cote),
      canal: config.canal.frequence_hz,
      fourmi: config.canal.frequence_fourmi_brutus_hz,
      positions: roues.map((r) => positionRoue(r, etat.tic, anneau)),
      dernierPas: etat.dernierPas,
    };
  }

  function encoder(octets) {
    if (!octets.length) return "";
    let zeros = 0;
    while (zeros < octets.length && octets[zeros] === 0) zeros += 1;
    let valeur = 0n;
    for (let i = zeros; i < octets.length; i += 1) valeur = valeur * 256n + BigInt(octets[i]);
    if (valeur === 0n) return ALPHABET[0].repeat(zeros);
    let chiffres = "";
    while (valeur > 0n) {
      chiffres = ALPHABET[Number(valeur % 39n)] + chiffres;
      valeur /= 39n;
    }
    return ALPHABET[0].repeat(zeros) + chiffres;
  }
  function decoder(texte) {
    if (texte === "") return [];
    const index = {};
    for (let i = 0; i < ALPHABET.length; i += 1) index[ALPHABET[i]] = i;
    let zeros = 0;
    while (zeros < texte.length && texte[zeros] === ALPHABET[0]) zeros += 1;
    let valeur = 0n;
    for (let i = zeros; i < texte.length; i += 1) {
      if (index[texte[i]] == null) throw new Error("symbole hors alphabet");
      valeur = valeur * 39n + BigInt(index[texte[i]]);
    }
    const corps = [];
    if (valeur > 0n) {
      while (valeur > 0n) {
        corps.push(Number(valeur % 256n));
        valeur /= 256n;
      }
      corps.reverse();
    }
    return Array(zeros).fill(0).concat(corps);
  }

  function valider(config, schema) {
    return verifier(config, schema, "config");
  }
  function verifier(valeur, regle, chemin) {
    const type = regle.type;
    if (type === "int") {
      if (typeof valeur !== "number" || !Number.isInteger(valeur)) return [chemin + " : entier attendu"];
      if (valeur < regle.min || valeur > regle.max) {
        return [chemin + " : entier hors bornes (" + regle.min + ".." + regle.max + "), reçu " + valeur];
      }
      return [];
    }
    if (type === "bool") return typeof valeur === "boolean" ? [] : [chemin + " : booléen attendu"];
    if (type === "str") {
      if (typeof valeur !== "string") return [chemin + " : texte attendu"];
      if (regle.enum && regle.enum.indexOf(valeur) < 0) return [chemin + " : valeur non autorisée"];
      if (valeur.length < (regle.min_len || 0) || valeur.length > (regle.max_len || 1e6)) {
        return [chemin + " : longueur de texte hors bornes"];
      }
      return [];
    }
    if (type === "null_ou_str") {
      if (valeur == null) return [];
      if (typeof valeur !== "string") return [chemin + " : texte ou vide attendu"];
      if (valeur.length > (regle.max_len || 200)) return [chemin + " : texte trop long"];
      return [];
    }
    if (type === "liste") {
      if (!Array.isArray(valeur)) return [chemin + " : liste attendue"];
      const erreurs = [];
      if (valeur.length < regle.min || valeur.length > regle.max) {
        erreurs.push(chemin + " : nombre d'éléments hors bornes (" + regle.min + ".." + regle.max + "), reçu " + valeur.length);
      }
      valeur.forEach((el, i) => erreurs.push(...verifier(el, regle.item, chemin + "[" + i + "]")));
      if (regle.cle_unique && !erreurs.length) {
        const ids = valeur.map((el) => el[regle.cle_unique]);
        if (new Set(ids).size !== ids.length) erreurs.push(chemin + " : identifiants en double");
      }
      return erreurs;
    }
    if (type === "objet") return verifierObjet(valeur, regle, chemin);
    return [chemin + " : type de schéma inconnu"];
  }
  function verifierObjet(valeur, regle, chemin) {
    if (valeur == null || typeof valeur !== "object" || Array.isArray(valeur)) return [chemin + " : objet attendu"];
    const erreurs = [];
    Object.keys(valeur).forEach((cle) => {
      if (!regle.champs[cle]) erreurs.push(chemin + "." + cle + " : champ inconnu");
    });
    Object.keys(regle.champs).forEach((cle) => {
      if (!(cle in valeur)) erreurs.push(chemin + "." + cle + " : champ manquant");
      else erreurs.push(...verifier(valeur[cle], regle.champs[cle], chemin + "." + cle));
    });
    if (erreurs.length) return erreurs;
    (regle.regles || []).forEach((spec) => erreurs.push(...regleMetier(spec, valeur, chemin)));
    return erreurs;
  }
  function regleMetier(spec, objet, chemin) {
    if (spec.type === "inferieur") {
      return objet[spec.champ] >= objet[spec.borne]
        ? [chemin + "." + spec.champ + " : doit être strictement inférieur à " + spec.borne]
        : [];
    }
    if (spec.type === "somme") {
      return objet[spec.a] + objet[spec.b] !== objet[spec.egal]
        ? [chemin + " : " + spec.a + " + " + spec.b + " doit égaler " + spec.egal]
        : [];
    }
    if (spec.type === "depart_dans_anneau") {
      const anneau = objet[spec.anneau];
      const erreurs = [];
      objet[spec.liste].forEach((roue, i) => {
        if (roue.depart >= anneau) {
          erreurs.push(chemin + "." + spec.liste + "[" + i + "].depart : doit être < " + anneau + " (taille de l'anneau)");
        }
      });
      return erreurs;
    }
    if (spec.type === "indices_ordonnes") {
      const erreurs = [];
      objet[spec.liste].forEach((roche, i) => {
        if (roche.index !== i) erreurs.push(chemin + "." + spec.liste + "[" + i + "].index : doit valoir " + i);
      });
      return erreurs;
    }
    return [chemin + " : règle inconnue"];
  }
  function libelles(schema) {
    const sortie = [];
    function marcher(regle) {
      if (!regle) return;
      if (regle.label) sortie.push(regle.label);
      if (regle.champs) Object.keys(regle.champs).forEach((cle) => marcher(regle.champs[cle]));
      if (regle.item) marcher(regle.item);
    }
    marcher(schema);
    return sortie;
  }

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
  function sha256(octets) {
    const K = new Uint32Array([
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]);
    const bytes = Uint8Array.from(octets);
    const bitLen = bytes.length * 8;
    const withPad = new Uint8Array(((bytes.length + 9 + 63) >> 6) << 6);
    withPad.set(bytes);
    withPad[bytes.length] = 0x80;
    const view = new DataView(withPad.buffer);
    const hi = Math.floor(bitLen / 0x100000000);
    view.setUint32(withPad.length - 8, hi, false);
    view.setUint32(withPad.length - 4, bitLen >>> 0, false);
    let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a;
    let h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;
    const w = new Uint32Array(64);
    for (let i = 0; i < withPad.length; i += 64) {
      for (let t = 0; t < 16; t += 1) w[t] = view.getUint32(i + t * 4, false);
      for (let t = 16; t < 64; t += 1) {
        const s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        const s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
      }
      let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
      for (let t = 0; t < 64; t += 1) {
        const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        const ch = (e & f) ^ (~e & g);
        const temp1 = (h + S1 + ch + K[t] + w[t]) >>> 0;
        const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        const maj = (a & b) ^ (a & c) ^ (b & c);
        const temp2 = (S0 + maj) >>> 0;
        h = g; g = f; f = e; e = (d + temp1) >>> 0; d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
      }
      h0 = (h0 + a) >>> 0; h1 = (h1 + b) >>> 0; h2 = (h2 + c) >>> 0; h3 = (h3 + d) >>> 0;
      h4 = (h4 + e) >>> 0; h5 = (h5 + f) >>> 0; h6 = (h6 + g) >>> 0; h7 = (h7 + h) >>> 0;
    }
    const out = new Uint8Array(32);
    const dv = new DataView(out.buffer);
    [h0, h1, h2, h3, h4, h5, h6, h7].forEach((v, i) => dv.setUint32(i * 4, v, false));
    return Array.from(out);
  }
  function canonique(valeur) {
    if (valeur === null || typeof valeur !== "object") return JSON.stringify(valeur);
    if (Array.isArray(valeur)) return "[" + valeur.map(canonique).join(",") + "]";
    const cles = Object.keys(valeur).sort();
    return "{" + cles.map((cle) => JSON.stringify(cle) + ":" + canonique(valeur[cle])).join(",") + "}";
  }

  function octetsUtf8(texte) {
    if (typeof TextEncoder !== "undefined") return Array.from(new TextEncoder().encode(texte));
    const octets = [];
    for (let i = 0; i < texte.length; i += 1) {
      const code = texte.charCodeAt(i);
      if (code < 128) octets.push(code);
      else if (code < 2048) octets.push(192 | (code >> 6), 128 | (code & 63));
      else octets.push(224 | (code >> 12), 128 | ((code >> 6) & 63), 128 | (code & 63));
    }
    return octets;
  }
  function empreinteDe(payload) {
    return encoder(sha256(octetsUtf8(canonique(payload))));
  }
  function graineDe(config, vue) {
    const payload = {
      version: config.version,
      tic: vue.tic,
      evolution: vue.evolution,
      config: config,
    };
    const empreinte = empreinteDe(payload);
    const graine = {
      version: payload.version,
      tic: payload.tic,
      evolution: payload.evolution,
      config: config,
      empreinte: empreinte,
    };
    return { graine: graine, empreinte: empreinte, base39: encoder(octetsUtf8(canonique(graine))) };
  }

  return {
    ALPHABET: ALPHABET,
    graineDe: graineDe,
    pgcd: pgcd,
    convergence: convergence,
    rejouer: rejouer,
    creer: creer,
    pas: pas,
    vue: vue,
    encoder: encoder,
    decoder: decoder,
    valider: valider,
    libelles: libelles,
    sha256: sha256,
    canonique: canonique,
  };
});
