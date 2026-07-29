/* Kopierfunktion fuer die Markdown-Vorschau. */

(function () {
  "use strict";

  var button = document.getElementById("copy-button");
  var source = document.getElementById("markdown-source");
  var status = document.getElementById("copy-status");
  if (!button || !source) { return; }

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
        ? "Markdown in die Zwischenablage kopiert."
        : "Kopieren hat nicht geklappt. Bitte den Text markieren und manuell kopieren.";
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
