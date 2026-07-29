/* Startseite: Abschnitte erscheinen beim Heranscrollen.
 *
 * Bewusst sparsam: nur Deckkraft und eine kleine Verschiebung, beides ueber
 * transform und opacity, damit der Browser nichts neu berechnen muss. Wer
 * Bewegung abgestellt hat, bekommt die Inhalte sofort und ohne Animation —
 * das entscheidet das Stylesheet, nicht dieses Skript.
 *
 * Ohne JavaScript bleibt die Seite vollstaendig lesbar: die Klasse wird erst
 * hier vergeben, vorher ist nichts versteckt.
 */
(function () {
  "use strict";

  var ziele = document.querySelectorAll(
    ".hero .showcase, .kennzahlen, .wrap > .grid > .card, .wrap > section, .laufband"
  );
  if (!ziele.length) { return; }

  // Ohne Beobachter (sehr alte Browser) bleibt alles sichtbar.
  if (!("IntersectionObserver" in window)) { return; }

  var ruhig = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (ruhig) { return; }

  Array.prototype.forEach.call(ziele, function (knoten) {
    knoten.classList.add("auftritt");
  });

  var beobachter = new IntersectionObserver(function (eintraege) {
    eintraege.forEach(function (eintrag) {
      if (!eintrag.isIntersecting) { return; }
      eintrag.target.classList.add("auftritt-fertig");
      beobachter.unobserve(eintrag.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

  Array.prototype.forEach.call(ziele, function (knoten) {
    beobachter.observe(knoten);
  });

  // Sicherheitsnetz: sollte der Beobachter fuer einen Abschnitt nie ausloesen,
  // wird nach vier Sekunden alles sichtbar gemacht. Ein Gestaltungseffekt darf
  // niemals dazu fuehren, dass Inhalte unerreichbar bleiben.
  window.setTimeout(function () {
    Array.prototype.forEach.call(ziele, function (knoten) {
      knoten.classList.add("auftritt-fertig");
    });
  }, 4000);
})();
