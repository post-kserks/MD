
const LINKS = {"01 Главная": [[10, 148, 200, 34, "02 Компьютеры"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 402, 200, 34, "06 Готовые запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"], [262, 246, 170, 34, "03 Постановка на учёт"], [444, 246, 148, 34, "04 Выдача компьютера"]], "02 Компьютеры": [[10, 110, 200, 34, "01 Главная"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 402, 200, 34, "06 Готовые запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"], [1127, 92, 82, 34, "08 Подтверждение удаления"], [917, 92, 104, 34, "03 Постановка на учёт"]], "03 Постановка на учёт": [[10, 110, 200, 34, "01 Главная"], [10, 148, 200, 34, "02 Компьютеры"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 402, 200, 34, "06 Готовые запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"], [740, 586, 120, 34, "02 Компьютеры"], [628, 586, 100, 34, "02 Компьютеры"]], "04 Выдача компьютера": [[10, 110, 200, 34, "01 Главная"], [10, 148, 200, 34, "02 Компьютеры"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 402, 200, 34, "06 Готовые запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"], [740, 496, 120, 34, "01 Главная"], [628, 496, 100, 34, "01 Главная"]], "05 SQL-запросы": [[10, 110, 200, 34, "01 Главная"], [10, 148, 200, 34, "02 Компьютеры"], [10, 402, 200, 34, "06 Готовые запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"]], "06 Готовые запросы": [[10, 110, 200, 34, "01 Главная"], [10, 148, 200, 34, "02 Компьютеры"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 440, 200, 34, "07 Импорт и экспорт"], [876, 208, 119, 34, "05 SQL-запросы"]], "07 Импорт и экспорт": [[10, 110, 200, 34, "01 Главная"], [10, 148, 200, 34, "02 Компьютеры"], [10, 364, 200, 34, "05 SQL-запросы"], [10, 402, 200, 34, "06 Готовые запросы"]], "08 Подтверждение удаления": [[794, 461, 82, 34, "02 Компьютеры"], [709, 461, 75, 34, "02 Компьютеры"]]};
const C = {"primary": "#2F5D9E", "primary_dark": "#234A80", "primary_light": "#E8EEF7", "bg": "#F5F7FA", "surface": "#FFFFFF", "border": "#D5DBE3", "text": "#1F2933", "muted": "#6B7785", "sidebar": "#1F2A3A", "sidebar_text": "#C9D3E0", "success": "#2E7D4F", "success_bg": "#E3F2E8", "warning": "#B7791F", "warning_bg": "#FBF0DC", "info": "#3D6FB6", "info_bg": "#E4EDF9", "danger": "#C0392B", "danger_bg": "#FBE5E2", "row_alt": "#F9FAFC", "selected": "#DCE7F7", "overlay": "#1F2933"};
function hex(h) { const n = parseInt(h.slice(1), 16); return {r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255}; }
async function run() {
  await figma.loadAllPagesAsync();
  for (const style of ["Regular", "Bold"]) await figma.loadFontAsync({family: "Inter", style});
  const page = figma.currentPage;
  const frames = {};
  for (const n of page.children) if (n.type === "FRAME") frames[n.name] = n;
  const missing = Object.keys(LINKS).filter(k => !frames[k]);
  if (missing.length) { figma.closePlugin("Нет фреймов: " + missing.join(", ")); return; }
  let count = 0;
  for (const [name, spots] of Object.entries(LINKS)) {
    const frame = frames[name];
    for (const old of frame.findChildren(n => n.name.startsWith("Переход → "))) old.remove();
    for (const [x, y, w, h, target] of spots) {
      const r = figma.createRectangle();
      r.name = "Переход → " + target;
      r.x = x; r.y = y; r.resize(w, h); r.fills = [];
      frame.appendChild(r);
      const reactions = [{trigger: {type: "ON_CLICK"}, actions: [{type: "NODE", destinationId: frames[target].id,
        navigation: "NAVIGATE", transition: {type: "DISSOLVE", easing: {type: "EASE_OUT"}, duration: 0.2},
        resetScrollPosition: true}]}];
      if (r.setReactionsAsync) await r.setReactionsAsync(reactions); else r.reactions = reactions;
      count++;
    }
  }
  page.flowStartingPoints = [{nodeId: frames["01 Главная"].id, name: "Учёт ПК — основной сценарий"}];
  const old = page.findOne(n => n.name === "Компоненты дизайн-системы");
  if (old) old.remove();
  const box = figma.createFrame();
  box.name = "Компоненты дизайн-системы";
  box.x = 0; box.y = 2000; box.resize(1280, 420);
  box.fills = [{type: "SOLID", color: hex(C.bg)}];
  const title = figma.createText();
  title.fontName = {family: "Inter", style: "Bold"}; title.fontSize = 22; title.characters = "Компоненты";
  title.x = 40; title.y = 30; box.appendChild(title);
  function label(parent, text, size, color, bold) {
    const t = figma.createText();
    t.fontName = {family: "Inter", style: bold ? "Bold" : "Regular"}; t.fontSize = size; t.characters = text;
    t.fills = [{type: "SOLID", color: hex(color)}]; parent.appendChild(t); return t;
  }
  function component(name, w, h, fill, stroke, text, textColor, radius, bold, align) {
    const c = figma.createComponent();
    c.name = name; c.resize(w, h); c.cornerRadius = radius;
    c.fills = fill ? [{type: "SOLID", color: hex(fill)}] : [];
    if (stroke) { c.strokes = [{type: "SOLID", color: hex(stroke)}]; c.strokeWeight = 1; }
    c.layoutMode = "HORIZONTAL"; c.primaryAxisAlignItems = align || "CENTER"; c.counterAxisAlignItems = "CENTER";
    c.paddingLeft = 12; c.paddingRight = 12; c.primaryAxisSizingMode = "FIXED"; c.counterAxisSizingMode = "FIXED";
    label(c, text, 13, textColor, bold);
    return c;
  }
  const buttons = [
    component("Тип=Основная", 140, 34, C.primary, null, "Сохранить", "#FFFFFF", 6, true),
    component("Тип=Вторичная", 140, 34, C.surface, C.border, "Отмена", C.text, 6, false),
    component("Тип=Опасная", 140, 34, C.danger, null, "Удалить", "#FFFFFF", 6, true),
    component("Тип=Недоступна", 140, 34, C.bg, C.border, "Недоступна", C.muted, 6, false)];
  buttons.forEach(b => box.appendChild(b));
  const btnSet = figma.combineAsVariants(buttons, box);
  btnSet.name = "Кнопка"; btnSet.x = 40; btnSet.y = 90;
  btnSet.layoutMode = "HORIZONTAL"; btnSet.itemSpacing = 16; btnSet.paddingLeft = 16; btnSet.paddingRight = 16;
  btnSet.paddingTop = 16; btnSet.paddingBottom = 16; btnSet.primaryAxisSizingMode = "AUTO"; btnSet.counterAxisSizingMode = "AUTO";
  const fields = [
    component("Состояние=Обычное", 260, 34, C.surface, C.border, "Подсказка", C.muted, 5, false, "MIN"),
    component("Состояние=Фокус", 260, 34, C.surface, C.primary, "ПК-00031", C.text, 5, false, "MIN"),
    component("Состояние=Ошибка", 260, 34, C.danger_bg, C.danger, "PC-1", C.text, 5, false, "MIN")];
  fields.forEach(f => box.appendChild(f));
  const fieldSet = figma.combineAsVariants(fields, box);
  fieldSet.name = "Поле ввода"; fieldSet.x = 40; fieldSet.y = 200;
  fieldSet.layoutMode = "HORIZONTAL"; fieldSet.itemSpacing = 16; fieldSet.paddingLeft = 16; fieldSet.paddingRight = 16;
  fieldSet.paddingTop = 16; fieldSet.paddingBottom = 16; fieldSet.primaryAxisSizingMode = "AUTO"; fieldSet.counterAxisSizingMode = "AUTO";
  const badges = [["в эксплуатации", "success"], ["в резерве", "info"], ["в ремонте", "warning"], ["списан", "danger"]]
    .map(([s, k]) => component("Состояние=" + s, 140, 22, C[k + "_bg"], null, s, C[k], 11, true));
  badges.forEach(b => box.appendChild(b));
  const badgeSet = figma.combineAsVariants(badges, box);
  badgeSet.name = "Метка состояния"; badgeSet.x = 40; badgeSet.y = 310;
  badgeSet.layoutMode = "HORIZONTAL"; badgeSet.itemSpacing = 16; badgeSet.paddingLeft = 16; badgeSet.paddingRight = 16;
  badgeSet.paddingTop = 16; badgeSet.paddingBottom = 16; badgeSet.primaryAxisSizingMode = "AUTO"; badgeSet.counterAxisSizingMode = "AUTO";
  const nav = component("Пункт меню", 200, 34, C.primary, null, "⌂  Главная", "#FFFFFF", 6, true, "MIN");
  box.appendChild(nav); nav.x = 760; nav.y = 106;
  figma.closePlugin("Переходов: " + count + ", компонентов: " + (buttons.length + fields.length + badges.length + 1));
}
run().catch(e => figma.closePlugin("Ошибка: " + e.message));
