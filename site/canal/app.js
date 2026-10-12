// Canal Street Coffee: the menu is not in the HTML. It is fetched from menu.json and
// drawn into the page after you choose a shop and search (or ask for the full menu).
// The list shows names only; each item's sizes and prices are on its own page (item.html).
const PAGE_SIZE = 6;
let matches = [], shown = 0, shop = "";

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function load() {
  const r = await fetch("menu.json");
  return r.json();
}

function card(item) {
  const a = document.createElement("a");
  a.className = "result-card";
  a.href = "item.html?id=" + encodeURIComponent(item.id) + "&shop=" + encodeURIComponent(shop);
  a.innerHTML = "<h3></h3><p class='result-card__category'></p>";
  a.querySelector("h3").textContent = item.name;
  a.querySelector(".result-card__category").textContent = item.category;
  return a;
}

async function showNext() {
  const more = document.getElementById("more");
  more.hidden = true;
  await sleep(350);                       // the "server" is a little slow
  const box = document.getElementById("results");
  for (const item of matches.slice(shown, shown + PAGE_SIZE)) box.appendChild(card(item));
  shown = Math.min(shown + PAGE_SIZE, matches.length);
  more.hidden = shown >= matches.length;
  document.getElementById("status").textContent =
    "Showing " + shown + " of " + matches.length + " items at " + shop + ".";
}

async function run(query) {
  const status = document.getElementById("status");
  shop = document.getElementById("location").value;
  document.getElementById("results").innerHTML = "";
  document.getElementById("more").hidden = true;
  if (!shop) {
    status.className = "error";
    status.textContent = "Choose a shop first — prices differ by location.";
    return;
  }
  status.className = "";
  status.textContent = "Loading the " + shop + " menu…";
  const menu = await load();
  const q = query.trim().toLowerCase();
  matches = menu.filter(i => !q || i.name.toLowerCase().includes(q) || i.category.toLowerCase().includes(q));
  shown = 0;
  if (!matches.length) { status.textContent = "No items match “" + query + "”."; return; }
  await showNext();
}

document.getElementById("search-btn").addEventListener("click", () => run(document.getElementById("search").value));
document.getElementById("search").addEventListener("keydown", e => { if (e.key === "Enter") run(e.target.value); });
document.getElementById("show-all").addEventListener("click", () => { document.getElementById("search").value = ""; run(""); });
document.getElementById("more").addEventListener("click", showNext);
