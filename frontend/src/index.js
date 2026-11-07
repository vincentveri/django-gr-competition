import "./main.css";

const root = document.documentElement;

// Theme toggle (initial theme is set by the inline script in base.html <head>)
const toggle = document.getElementById("theme-toggle");
if (toggle) {
  // Icons are switched in CSS (dark:hidden / dark:block), so only the attribute changes here.
  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
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

// Formset "add row" button (e.g. bulk athlete entry)
const addRow = document.getElementById("add-row");
if (addRow) {
  addRow.addEventListener("click", () => {
    const total = document.getElementById(addRow.dataset.total);
    const template = document.getElementById(addRow.dataset.template);
    const body = document.getElementById(addRow.dataset.body);
    const index = parseInt(total.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, String(index));
    body.insertAdjacentHTML("beforeend", html);
    total.value = String(index + 1);
  });
}
