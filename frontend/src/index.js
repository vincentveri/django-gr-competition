import "./main.css";

const root = document.documentElement;

// Theme toggle (initial theme is set by the inline script in base.html <head>)
const toggle = document.getElementById("theme-toggle");
if (toggle) {
  const sync = () => {
    toggle.textContent = root.getAttribute("data-theme") === "dark" ? "Chiaro" : "Scuro";
  };
  sync();
  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
    sync();
  });
}

// Mobile sidebar toggle
const burger = document.getElementById("sidebar-burger");
const sidebar = document.getElementById("sidebar");
if (burger && sidebar) {
  burger.addEventListener("click", () => {
    const open = sidebar.classList.toggle("hidden") === false;
    burger.setAttribute("aria-expanded", String(open));
  });
}
