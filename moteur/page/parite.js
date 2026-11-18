const fs = require("fs");
const client = require("./client.js");

const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const erreurs = [];
payload.vecteurs.forEach((vecteur) => {
  const obtenu = client.rejouer(payload.config, vecteur.tics, vecteur.anomalieDes);
  const attendu = vecteur.attendu;
  Object.keys(attendu).forEach((cle) => {
    if (obtenu[cle] !== attendu[cle]) {
      erreurs.push(vecteur.tics + " " + cle + " obtenu=" + obtenu[cle] + " attendu=" + attendu[cle]);
    }
  });
});
payload.base39.forEach((cas) => {
  const texte = client.encoder(cas.brut);
  if (texte !== cas.texte) erreurs.push("base39 " + texte + " != " + cas.texte);
  const retour = client.decoder(texte);
  if (retour.join(",") !== cas.brut.join(",")) erreurs.push("retour base39");
});
const mauvais = JSON.parse(JSON.stringify(payload.config));
mauvais.canal.frequence_hz = -3;
const refus = client.valider(mauvais, payload.schema);
if (!refus.length) erreurs.push("invalid non rejeté");
const defautErreurs = client.valider(payload.config, payload.schema);
if (defautErreurs.length) erreurs.push("défaut rejeté " + defautErreurs.join(" | "));
const labels = client.libelles(payload.schemaFactice);
if (labels.indexOf("Note factice") < 0) erreurs.push("libellé factice absent");
if (client.convergence(payload.config.six_roues.roues, 273) !== 273) erreurs.push("convergence");
const vite = JSON.parse(JSON.stringify(payload.config));
vite.six_roues.roues.forEach((roue) => { roue.vitesse = 7; });
if (client.convergence(vite.six_roues.roues, 273) !== 39) erreurs.push("convergence 39");
if (payload.empreinte) {
  const vue0 = client.rejouer(payload.config, 0, null);
  const graine = client.graineDe(payload.config, vue0);
  if (graine.empreinte !== payload.empreinte) erreurs.push("empreinte " + graine.empreinte + " != " + payload.empreinte);
  if (graine.base39 !== payload.graine39) erreurs.push("graine39");
}
if (erreurs.length) {
  console.error(erreurs.join("\n"));
  process.exit(1);
}
console.log("ok");
