const H = require("./full.js");
require("./deck.js");
require("./ch2.js")(H);
require("./ch3.js")(H);
require("./ch45.js")(H);
console.log("total slides:", H.pres._slides.length, "| page counter:", H.getPG());
H.pres.writeFile({ fileName: "pai-deck.pptx" })
  .then(() => H.applyTheme("pai-deck.pptx", H.THEME))
  .then(() => console.log("written: pai-deck.pptx"))
  .catch(e => { console.error("FAIL:", e.message); process.exit(1); });
