/* Klartext — Dashboard.
   Kein Framework, kein externer Code, keine Inline-Handler (strenge CSP).
   Es wird ausschließlich Text gesetzt, nie HTML aus Serverdaten. */

(function () {
  "use strict";

  var form = document.getElementById("upload-form");
  if (!form) { return; }

  var input       = document.getElementById("file-input");
  var dropzone    = document.getElementById("dropzone");
  var fileList    = document.getElementById("file-list");
  var uploadBtn   = document.getElementById("upload-button");
  var clearBtn    = document.getElementById("clear-button");
  var messageBox  = document.getElementById("upload-message");
  var jobList     = document.getElementById("job-list");
  var usageLine   = document.getElementById("usage-line");
  var zipButton   = document.getElementById("zip-button");
  var csrf        = form.querySelector("input[name=csrf]").value;

  var selected = [];
  var pollTimer = null;
  var pollDelay = 2000;

  // ---------------------------------------------------------------- Hilfen

  function formatSize(bytes) {
    if (bytes < 1024) { return bytes + " B"; }
    if (bytes < 1024 * 1024) { return (bytes / 1024).toFixed(0) + " KB"; }
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
  }

  function formatTime(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) { return ""; }
    return d.toLocaleString("de-DE", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"
    });
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  function showMessage(text, kind) {
    messageBox.textContent = "";
    if (!text) { return; }
    var box = el("div", "notice notice-" + (kind || "error"), text);
    messageBox.appendChild(box);
  }

  // ---------------------------------------------------------------- Auswahl

  function renderSelection() {
    fileList.textContent = "";
    if (selected.length === 0) {
      fileList.hidden = true;
      uploadBtn.disabled = true;
      clearBtn.hidden = true;
      return;
    }
    selected.forEach(function (file) {
      var row = el("li");
      row.appendChild(el("span", null, file.name));
      row.appendChild(el("span", "muted nowrap", formatSize(file.size)));
      fileList.appendChild(row);
    });
    fileList.hidden = false;
    uploadBtn.disabled = false;
    clearBtn.hidden = false;
  }

  function setFiles(fileArray) {
    selected = Array.prototype.slice.call(fileArray);
    // FileList des Inputs mit der tatsächlichen Auswahl synchron halten
    var transfer = new DataTransfer();
    selected.forEach(function (file) { transfer.items.add(file); });
    input.files = transfer.files;
    showMessage("");
    renderSelection();
  }

  input.addEventListener("change", function () { setFiles(input.files); });

  clearBtn.addEventListener("click", function () {
    input.value = "";
    setFiles([]);
  });

  ["dragenter", "dragover"].forEach(function (name) {
    dropzone.addEventListener(name, function (event) {
      event.preventDefault();
      dropzone.classList.add("is-over");
    });
  });

  ["dragleave", "drop"].forEach(function (name) {
    dropzone.addEventListener(name, function (event) {
      event.preventDefault();
      if (name === "dragleave" && dropzone.contains(event.relatedTarget)) { return; }
      dropzone.classList.remove("is-over");
    });
  });

  dropzone.addEventListener("drop", function (event) {
    if (event.dataTransfer && event.dataTransfer.files.length) {
      setFiles(event.dataTransfer.files);
    }
  });

  // ---------------------------------------------------------------- Upload

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (selected.length === 0) { return; }

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Wird hochgeladen ...";
    clearBtn.disabled = true;
    showMessage("");

    var data = new FormData();
    data.append("csrf", csrf);
    selected.forEach(function (file) { data.append("files", file, file.name); });

    var bar = showUploadProgress(0);

    // XMLHttpRequest statt fetch: nur damit gibt es echte Fortschrittsereignisse.
    var request = new XMLHttpRequest();
    request.open("POST", "/app/upload", true);
    request.withCredentials = true;
    request.setRequestHeader("Accept", "application/json");

    request.upload.addEventListener("progress", function (progressEvent) {
      if (!progressEvent.lengthComputable) { return; }
      var percent = Math.round(progressEvent.loaded / progressEvent.total * 100);
      bar.set(percent);
      if (percent >= 100) {
        bar.label("Hochgeladen — wird geprüft ...");
        bar.indeterminate();
      }
    });

    function finish() {
      uploadBtn.textContent = "Konvertierung starten";
      clearBtn.disabled = false;
      uploadBtn.disabled = selected.length === 0;
    }

    request.addEventListener("load", function () {
      var payload = {};
      try { payload = JSON.parse(request.responseText); } catch (error) { payload = {}; }
      hideUploadProgress();
      if (request.status >= 200 && request.status < 300) {
        input.value = "";
        setFiles([]);
        showMessage("Upload angenommen. Die Verarbeitung läuft.", "success");
        pollDelay = 1000;
        refreshJobs();
      } else if (request.status === 401) {
        window.location.href = "/anmelden";
      } else {
        showMessage(payload.error || "Der Upload wurde abgelehnt.", "error");
      }
      finish();
    });

    request.addEventListener("error", function () {
      hideUploadProgress();
      showMessage("Die Verbindung wurde unterbrochen. Bitte erneut versuchen.", "error");
      finish();
    });

    request.addEventListener("abort", function () {
      hideUploadProgress();
      finish();
    });

    request.send(data);
  });


  // ---------------------------------------------------------------- Fortschritt

  var uploadProgress = null;

  function showUploadProgress(startPercent) {
    hideUploadProgress();

    var wrap  = el("div", "progress-block");
    var label = el("div", "progress-label", "Wird hochgeladen ...");
    var track = el("div", "progress");
    var fill  = el("div", "progress-fill");
    var value = el("span", "progress-value", startPercent + " %");

    track.setAttribute("role", "progressbar");
    track.setAttribute("aria-valuemin", "0");
    track.setAttribute("aria-valuemax", "100");
    track.setAttribute("aria-valuenow", String(startPercent));
    track.setAttribute("aria-label", "Fortschritt des Uploads");
    fill.style.width = startPercent + "%";

    track.appendChild(fill);
    label.appendChild(value);
    wrap.appendChild(label);
    wrap.appendChild(track);
    // Bewusst nicht in die aria-live-Meldungszone: sonst wuerde jede
    // Prozentaenderung vorgelesen. Der Balken sitzt direkt davor.
    messageBox.parentNode.insertBefore(wrap, messageBox);

    uploadProgress = wrap;
    return {
      set: function (percent) {
        fill.style.width = percent + "%";
        track.setAttribute("aria-valuenow", String(percent));
        value.textContent = percent + " %";
      },
      label: function (text) {
        label.textContent = text;
      },
      indeterminate: function () {
        track.classList.add("progress-running");
        track.removeAttribute("aria-valuenow");
        fill.style.width = "100%";
      }
    };
  }

  function hideUploadProgress() {
    if (uploadProgress && uploadProgress.parentNode) {
      uploadProgress.parentNode.removeChild(uploadProgress);
    }
    uploadProgress = null;
  }

  function elapsedText(isoStart) {
    var start = new Date(isoStart);
    if (isNaN(start.getTime())) { return ""; }
    var seconds = Math.max(0, Math.round((Date.now() - start.getTime()) / 1000));
    if (seconds < 60) { return seconds + " s"; }
    var minutes = Math.floor(seconds / 60);
    return minutes + " min " + (seconds % 60) + " s";
  }

  // Laufende Konvertierung: es gibt von der Engine keinen echten Prozentwert.
  // Statt einen zu erfinden, laeuft ein unbestimmter Balken plus verstrichene Zeit.
  function jobProgress(job) {
    var wrap = el("div", "progress-block");

    // Der Zustand steht schon im Schild daneben — hier nur die Zusatzinfo,
    // damit nichts doppelt dasteht.
    var text;
    if (job.status === "queued") {
      text = job.ahead > 0
        ? (job.ahead === 1 ? "1 Auftrag davor" : job.ahead + " Aufträge davor")
        : "als Nächstes an der Reihe";
    } else {
      text = "seit " + elapsedText(job.started_at || job.created_at);
    }
    wrap.appendChild(el("div", "progress-label", text));

    var track = el("div", "progress progress-running"
      + (job.status === "queued" ? " progress-waiting" : ""));
    track.setAttribute("role", "progressbar");
    track.setAttribute("aria-label", text);
    track.appendChild(el("div", "progress-fill"));
    wrap.appendChild(track);
    return wrap;
  }


  // Verbrauchszeile mitziehen. Wortlaut muss mit dashboard.html uebereinstimmen,
  // sonst springt der Text beim ersten Aktualisieren sichtbar um.
  function updateUsage(usage, limits) {
    if (!usageLine || !usage || !limits) { return; }
    var text = "Heute " + usage.jobs_day + "/" + limits.jobs_per_day + " Konvertierungen · "
             + usage.pages_day + "/" + limits.pages_per_day + " Seiten";
    if (usage.active || usage.queued) {
      text += " · " + usage.active + " in Arbeit, " + usage.queued + " wartend";
    }
    usageLine.textContent = text;
  }

  // ---------------------------------------------------------------- Auftragsliste

  var STATUS_TEXT = {
    queued:     "In Warteschlange",
    processing: "Wird verarbeitet",
    done:       "Fertig",
    error:      "Fehler"
  };

  // Selbst gezeichnete Symbole auf 24er-Raster — der Zustand hängt nie nur an der Farbe.
  var STATUS_PATHS = {
    queued:     ["M12 3.5a8.5 8.5 0 1 1 0 17 8.5 8.5 0 0 1 0-17Z", "M12 7.4V12l3.1 2.1"],
    processing: ["M20.2 12a8.2 8.2 0 1 1-2.6-6", "M20.6 4.4V9.6h-5.2"],
    done:       ["M12 3.5a8.5 8.5 0 1 1 0 17 8.5 8.5 0 0 1 0-17Z", "m8.4 12.2 2.5 2.5 4.7-5"],
    error:      ["M12 4.2 21 19.2H3L12 4.2Z", "M12 10v3.6", "M12 16.6h.01"]
  };

  function statusIcon(status) {
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    (STATUS_PATHS[status] || []).forEach(function (d) {
      var path = document.createElementNS(ns, "path");
      path.setAttribute("d", d);
      svg.appendChild(path);
    });
    return svg;
  }


  function binIcon() {
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    ["M4 7h16", "M10 7V5.2a1.2 1.2 0 0 1 1.2-1.2h1.6A1.2 1.2 0 0 1 14 5.2V7",
     "M6 7l.8 12.2A1.8 1.8 0 0 0 8.6 21h6.8a1.8 1.8 0 0 0 1.8-1.8L18 7",
     "M10.5 11v6", "M13.5 11v6"].forEach(function (d) {
      var path = document.createElementNS(ns, "path");
      path.setAttribute("d", d);
      svg.appendChild(path);
    });
    return svg;
  }

  function jobRow(job) {
    /* Feste Struktur fuer jede Zeile — dadurch stehen Name, Angaben, Balken und
       Aktionen bei allen Auftraegen exakt auf derselben Kante:

         [ Symbol ]  Dateiname .................... Zustand
                     Groesse · Seiten · Zeit · Dauer
                     [ Fortschritt oder Aktionen ]
    */
    var row = el("li", "job job-" + job.status);

    var rail = el("div", "job-rail");
    rail.appendChild(statusIcon(job.status));
    row.appendChild(rail);

    var head = el("div", "job-head");
    head.appendChild(el("span", "job-name", job.name));
    head.appendChild(el("span", "job-state", STATUS_TEXT[job.status] || job.status));
    row.appendChild(head);

    var meta = [formatSize(job.size)];
    if (job.pages) { meta.push(job.pages + (job.pages === 1 ? " Seite" : " Seiten")); }
    meta.push(formatTime(job.created_at));
    if (job.status === "done" && job.duration_ms) {
      meta.push((job.duration_ms / 1000).toFixed(1).replace(".", ",") + " s");
    }
    row.appendChild(el("p", "job-meta", meta.join(" · ")));

    if (job.status === "error" && job.error) {
      row.appendChild(el("p", "job-error", job.error));
    }
    if (job.status === "queued" || job.status === "processing") {
      row.appendChild(jobProgress(job));
    }

    var actions = el("div", "job-actions");
    if (job.status === "done") {
      var group = el("div", "job-actions-main");

      var view = el("a", "btn btn-secondary btn-small", "Ansehen");
      view.href = "/app/auftrag/" + encodeURIComponent(job.id);
      group.appendChild(view);

      var md = el("a", "btn btn-secondary btn-small", ".md");
      md.href = "/app/auftrag/" + encodeURIComponent(job.id) + "/download/md";
      md.setAttribute("aria-label", "Markdown herunterladen: " + job.name);
      group.appendChild(md);

      var js = el("a", "btn btn-secondary btn-small", ".json");
      js.href = "/app/auftrag/" + encodeURIComponent(job.id) + "/download/json";
      js.setAttribute("aria-label", "JSON herunterladen: " + job.name);
      group.appendChild(js);

      actions.appendChild(group);
    }

    var deleteForm = document.createElement("form");
    deleteForm.method = "post";
    deleteForm.action = "/app/auftrag/" + encodeURIComponent(job.id) + "/loeschen";
    deleteForm.className = "inline-form job-delete";
    var token = document.createElement("input");
    token.type = "hidden"; token.name = "csrf"; token.value = csrf;
    deleteForm.appendChild(token);
    // Nur ein Symbol: vier Textknoepfe passen am Handy nicht in eine Zeile.
    // Beschriftung fuer Screenreader und Mauszeiger bleibt vollstaendig erhalten,
    // und vor dem Loeschen wird ohnehin nachgefragt.
    var del = el("button", "btn btn-danger btn-icon");
    del.type = "submit";
    del.setAttribute("aria-label", "Auftrag löschen: " + job.name);
    del.title = "Auftrag löschen";
    del.appendChild(binIcon());
    deleteForm.appendChild(del);
    deleteForm.addEventListener("submit", function (event) {
      if (!window.confirm("Diesen Auftrag mit allen Ergebnissen endgültig löschen?")) {
        event.preventDefault();
      }
    });
    actions.appendChild(deleteForm);

    row.appendChild(actions);
    return row;
  }

  function renderJobs(jobs) {
    jobList.textContent = "";
    if (jobs.length === 0) {
      // Muss inhaltlich dem serverseitigen Leerzustand in dashboard.html
      // entsprechen — sonst sieht der Benutzer nach dem Loeschen des letzten
      // Auftrags eine andere Seite als beim normalen Aufruf.
      var empty = el("li", "muted small empty");
      empty.id = "empty-state";
      empty.appendChild(el("p", "empty-lead",
        "Noch nichts konvertiert. Lade oben eine Datei hoch — das Ergebnis erscheint hier."));
      var schritte = el("ol", "empty-steps");
      [
        "Datei auswählen oder in das Feld oben ziehen.",
        "Auf „Konvertierung starten\u201c tippen.",
        "Fertige Aufträge erscheinen hier mit Markdown- und JSON-Download."
      ].forEach(function (text) { schritte.appendChild(el("li", null, text)); });
      empty.appendChild(schritte);
      jobList.appendChild(empty);
      zipButton.hidden = true;
      return;
    }
    jobs.forEach(function (job) { jobList.appendChild(jobRow(job)); });

    var doneIds = jobs.filter(function (job) { return job.status === "done"; })
                      .map(function (job) { return job.id; });
    if (doneIds.length > 0) {
      zipButton.href = "/app/download/zip?ids=" + doneIds.slice(0, 50).join(",");
      zipButton.hidden = false;
    } else {
      zipButton.hidden = true;
    }
  }

  function refreshJobs() {
    fetch("/api/jobs", {
      credentials: "same-origin",
      headers: { "Accept": "application/json" }
    }).then(function (response) {
      if (response.status === 401) { window.location.href = "/anmelden"; return null; }
      return response.ok ? response.json() : null;
    }).then(function (payload) {
      if (!payload) { return; }
      renderJobs(payload.jobs);
      updateUsage(payload.usage, payload.limits);
      var busy = payload.jobs.some(function (job) {
        return job.status === "queued" || job.status === "processing";
      });
      // Ruhige Seite pollt selten, aktive Verarbeitung pollt zuegig.
      pollDelay = busy ? 2000 : 15000;
    }).catch(function () {
      pollDelay = Math.min(pollDelay * 2, 60000);
    }).then(function () {
      clearTimeout(pollTimer);
      pollTimer = setTimeout(refreshJobs, pollDelay);
    });
  }

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) {
      clearTimeout(pollTimer);
      refreshJobs();
    }
  });

  renderSelection();
  refreshJobs();
})();
