/* Kopierfunktion fuer die Markdown-Vorschau. */

(function () {
  "use strict";

  var button = document.getElementById("copy-button");
  var source = document.getElementById("markdown-source");
  var status = document.getElementById("copy-status");
  if (!button || !source) { return; }

  // Die beiden Rueckmeldungen stehen als Datenblock in der Seite: Inline-Skript
  // verbietet die Inhaltsrichtlinie, und die Sprache steht erst zur Laufzeit fest.
  var daten = document.getElementById("i18n-daten");
  var TEXTE = {};
  try { TEXTE = JSON.parse(daten.getAttribute("data-strings")); } catch (fehler) { TEXTE = {}; }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (error) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  button.addEventListener("click", function () {
    var text = source.textContent;
    var done = function (ok) {
      status.textContent = ok
        ? (TEXTE["copied"] || "")
        : (TEXTE["copy_failed"] || "");
      setTimeout(function () { status.textContent = ""; }, 4000);
    };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { done(true); },
                                              function () { done(fallbackCopy(text)); });
    } else {
      done(fallbackCopy(text));
    }
  });
})();
