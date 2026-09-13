// DOM smoke test. Pass real HTML, scripts and server states to testTacticalUI.
// No browser globals or dependencies required; layout is not tested here.
function testTacticalUI(fixture) {
  class Element {
    constructor(tag) {
      this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {};
      this.value = ""; this.hidden = false; this.style = {setProperty() {}};
      this.classList = {toggle() {}};
      this.scrollHeight = this.scrollTop = this.clientHeight = 0;
    }
    append(...nodes) { this.children.push(...nodes); }
    replaceChildren(...nodes) { this.children = nodes; }
    setAttribute(key, value) { this.attributes[key] = value; }
    getAttribute(key) { return this.attributes[key]; }
    addEventListener(name, fn) { this[`on${name}`] = fn; }
    focus() {}
    reportValidity() { return true; }
  }
  const elements = new Map();
  for (const match of fixture.html.matchAll(/<(\w+)\b[^>]*\bid="([^"]+)"[^>]*>/g)) {
    if (elements.has(match[2])) throw Error(`Duplicate ID: ${match[2]}`);
    elements.set(match[2], new Element(match[1]));
  }
  const document = {getElementById: id => elements.get(id), createElement: tag => new Element(tag)};
  const main = fixture.main.replace(/\nload\(\);\s*$/, "");
  const check = new Function("document", "fixture", fixture.board + "\n" + main + `
    for (const sample of fixture.states) {
      state = sample; displayedEvents = 0; render();
      if (el("battleGrid").children.length !== 80) throw Error("Missing grid cells");
      if (el("boardUnit").children.length !== state.party.length) throw Error("Enemy is deployable");
      if (el("scenario").children.length !== 3) throw Error("Missing scenarios");
      if (state.combate && el("health").children.length !== state.party.length + state.combate.enemigos.length)
        throw Error("Missing health cards");
    }
    if (el("boardTool") || el("clearTerrain")) throw Error("Terrain editor remains");
    return fixture.states.length;
  `);
  return check(document, fixture);
}
