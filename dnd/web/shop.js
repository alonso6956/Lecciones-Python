"use strict";
const el = id => document.getElementById(id);
const node = (tag, text) => {const n = document.createElement(tag); if (text !== undefined) n.textContent = text; return n;};
let state = null, busy = false, mode = "buy";

async function api(path, body) {
  const response = await fetch(`/api/tienda/${path}`, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw Error(result.error || "No se pudo completar la operación.");
  return result;
}
function errorMessage(error) {el("error").textContent = error.message; el("error").hidden = false;}
async function load() {
  if (busy) return;
  busy = true; render();
  try {
    const id = el("character").value;
    let data = await api(`estado${id ? `?personaje_id=${encodeURIComponent(id)}` : ""}`);
    if (!data.personaje_id && data.personajes.length) data = await api(`estado?personaje_id=${encodeURIComponent(data.personajes[0].id)}`);
    state = data;
    el("character").replaceChildren();
    for (const personaje of data.personajes) {
      const option = node("option", personaje.nombre); option.value = personaje.id;
      option.selected = personaje.id === data.personaje_id; el("character").append(option);
    }
    el("message").textContent = ""; el("error").hidden = true;
  } catch (error) {if (state) state.disponible = false; errorMessage(error);}
  finally {busy = false; render();}
}
async function buy(product, quantity) {
  if (busy || !state?.disponible || !state.personaje_id) return;
  busy = true; render();
  try {
    state = await api("comprar", {personaje_id: state.personaje_id, categoria: product.categoria,
      nombre: product.nombre, cantidad: quantity});
    el("message").textContent = state.mensaje;
    el("error").hidden = true;
  } catch (error) {errorMessage(error);}
  finally {busy = false; render();}
}
function description(p) {
  const details = [];
  if (p.ataque) details.push(`Daño ${p.ataque.join("–")}`, `Escala con ${p.estadistica_escalado}`, p.dos_manos ? "Dos manos" : "Una mano");
  if (p.defensa !== undefined) details.push(`Armadura ${p.defensa}`);
  if (p.salud !== undefined) details.push(`Recupera ${p.salud} de vida`);
  if (p.absorcion_pasiva !== undefined) details.push(`Absorción pasiva ${Math.round(p.absorcion_pasiva * 100)}%`, `Bloqueo activo ${Math.round(p.bloqueo_activo * 100)}%`);
  const requirements = Object.entries(p.requisitos || {}).map(([k,v]) => `${k} ${v}`);
  if (requirements.length) details.push(`Requiere ${requirements.join(", ")}`);
  if (p.cumple_requisitos === false) details.push("Puedes comprarlo, pero aún no cumples los requisitos para equiparlo");
  return details.join(" · ");
}
function render() {
  el("character").disabled = busy;
  el("refresh").disabled = busy;
  el("buyPanel").hidden = mode !== "buy"; el("sellPanel").hidden = mode !== "sell";
  el("buyMode").setAttribute("aria-pressed", String(mode === "buy")); el("sellMode").setAttribute("aria-pressed", String(mode === "sell"));
  if (!state) return;
  el("gold").textContent = state.oro;
  if (!state.disponible) el("message").textContent = "La tienda está cerrada durante las expediciones y los combates tácticos. Vuelve al menú para comprar.";
  else if (!state.personaje_id) el("message").textContent = "Crea un personaje desde el menú principal para acceder a la tienda.";
  const products = el("products"); products.replaceChildren();
  const query = el("search").value.toLocaleLowerCase(), category = el("category").value;
  for (const product of state.productos.filter(p => p.nombre.toLocaleLowerCase().includes(query) && (!category || p.categoria === category))) {
    const card = node("article"); card.className = "item";
    card.append(node("h3", product.nombre), node("p", description(product)),
      node("p", `${product.precio} oro por unidad · En inventario: ${product.cantidad}`));
    const label = node("label", "Cantidad"), quantity = node("input");
    quantity.type = "number"; quantity.min = "1"; quantity.max = "999"; quantity.value = "1"; quantity.required = true;
    label.append(quantity);
    const button = node("button", "Comprar"); button.className = "primary";
    const price = node("p", `Total: ${product.precio} oro`);
    const update = () => {
      const amount = Number(quantity.value), valid = Number.isInteger(amount) && amount >= 1 && amount <= 999;
      price.textContent = valid ? `Total: ${product.precio * amount} oro` : "Introduce una cantidad válida.";
      button.disabled = busy || !state.disponible || !state.personaje_id || !valid || state.oro < product.precio * amount;
    };
    quantity.oninput = update; update();
    button.onclick = () => {if (quantity.reportValidity()) buy(product, Number(quantity.value));};
    card.append(label, price, button); products.append(card);
  }
  if (!products.children.length) products.append(node("p", "No hay productos con esos filtros."));
  const inventory = el("inventory"); inventory.replaceChildren();
  for (const item of (state.ventas || []).filter(i => i.nombre.toLocaleLowerCase().includes(el("sellSearch").value.toLocaleLowerCase()))) {
    const card = node("article"); card.className = "item";
    card.append(node("h3", `${item.nombre} ×${item.cantidad}`), node("p", description(item.detalles)), node("p", item.motivo || `${item.precio_venta} oro por unidad`));
    const label = node("label", "Cantidad"), quantity = node("input");
    quantity.type = "number"; quantity.min = "1"; quantity.max = String(Math.min(999, item.cantidad)); quantity.step = "1"; quantity.value = "1"; quantity.required = true;
    quantity.disabled = busy || !item.vendible; label.append(quantity);
    const button = node("button", "Vender"), price = node("p");
    const update = () => {
      const amount = Number(quantity.value), valid = Number.isInteger(amount) && amount >= 1 && amount <= Math.min(999, item.cantidad);
      price.textContent = valid ? `Recibirás: ${item.precio_venta * amount} oro` : "Introduce una cantidad válida.";
      button.disabled = busy || !state.disponible || !item.vendible || !valid;
    };
    quantity.oninput = update; update();
    button.onclick = () => {if (quantity.reportValidity()) sell(item, Number(quantity.value));};
    card.append(label, price, button);
    inventory.append(card);
  }
  if (!inventory.children.length) inventory.append(node("p", state.personaje_id ? "No hay objetos con esos filtros." : "Selecciona un personaje para ver su inventario."));
}
async function sell(item, quantity) {
  if (busy || !state?.disponible || !state.personaje_id || !item.vendible) return;
  busy = true; render();
  try {
    state = await api("vender", {personaje_id: state.personaje_id, instance_id: item.instance_id, cantidad: quantity});
    el("message").textContent = state.mensaje; el("error").hidden = true;
  } catch (error) {errorMessage(error);}
  finally {busy = false; render();}
}
el("buyMode").onclick = () => {mode = "buy"; render();};
el("sellMode").onclick = () => {mode = "sell"; render();};
el("sellSearch").oninput = render;
el("character").onchange = load;
el("refresh").onclick = load;
el("search").oninput = render;
el("category").onchange = render;
load();
