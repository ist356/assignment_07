// The detail page is drawn from menu.json too: item.html?id=latte&shop=Westcott
const MARKUP = { "Westcott": 0, "Downtown": 0.30 };
function money(x) { return "$" + x.toFixed(2); }

(async () => {
  const params = new URLSearchParams(location.search);
  const id = params.get("id"), shop = params.get("shop") || "Westcott";
  await new Promise(r => setTimeout(r, 300));
  const menu = await (await fetch("menu.json")).json();
  const item = menu.find(i => i.id === id);
  const box = document.getElementById("detail");
  if (!item) { box.innerHTML = "<p>Item not found.</p>"; return; }
  box.innerHTML = `<h1 id="item-name"></h1><p id="item-category"></p>
    <table id="sizes"><thead><tr><th>Size</th><th>Price</th></tr></thead><tbody></tbody></table>
    <p id="item-description"></p><p><a href="./">← Back to the menu</a></p>`;
  document.getElementById("item-name").textContent = item.name;
  document.getElementById("item-category").textContent = item.category + " · " + shop;
  document.getElementById("item-description").textContent = item.description;
  const tbody = box.querySelector("#sizes tbody");
  for (const [size, price] of Object.entries(item.prices)) {
    const tr = document.createElement("tr");
    tr.innerHTML = "<td></td><td></td>";
    tr.children[0].textContent = size;
    tr.children[1].textContent = money(price + MARKUP[shop]);
    tbody.appendChild(tr);
  }
})();
