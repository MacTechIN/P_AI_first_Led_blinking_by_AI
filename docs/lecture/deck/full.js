const pptx = require("pptxgenjs");
const { applyTheme } = require("/home/sam/.claude/skills/synced/e0ded2c0-5687-437f-81a9-25283e305c85_ef2d0686-80bf-4c46-9dcd-37619fed09ad/pptx/scripts/apply_theme.js");

const THEME = { name: "PhysicalAI", headFontFace: "Malgun Gothic", bodyFontFace: "Malgun Gothic",
  colors: { dk1:"1A1A1A", lt1:"FFFFFF", dk2:"404040", lt2:"F2F2F2", accent1:"1F3A93",
            accent2:"E8963C", accent3:"7F7F7F", accent4:"7B3FA0", accent5:"1F8A4C",
            accent6:"C0392B", hlink:"1F3A93", folHlink:"7F7F7F" } };

const F = "Malgun Gothic";
const INK="1A1A1A", MUTED="7F7F7F", RULE="BFBFBF", BAR="7F7F7F", RED="B03A2E";
// Phase 색
const P1="0F7B8A", P2="2E6DA4", P3="7B3FA0", P4="C87F0A", P5="1F8A4C";
const P1BG="E3F1F3", P2BG="E4EDF6", P3BG="F0E7F6", P4BG="FAF0DF", P5BG="E4F2EA";
const NAVY="1F3A93", NAVYBG="EAF0FA";

const pres = new pptx();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: F, bodyFontFace: F };
pres.author = "Physical AI Curriculum";
pres.title = "Physical AI: 챗봇을 넘어 격전지로";
pres.defineSlideMaster({ title: "M_BLANK", background: { color: "FFFFFF" } });

let PG = 0;
const T = (s,t,o) => s.addText(t, Object.assign({ fontFace:F, isTextBox:true, margin:0 }, o));
const R = (s,o) => s.addShape(pres.ShapeType.rect, o);
const RR = (s,o) => s.addShape(pres.ShapeType.roundRect, o);
const EL = (s,o) => s.addShape(pres.ShapeType.ellipse, o);
const pageNo = (s) => { PG++; T(s, String(PG), { x:12.52, y:7.18, w:0.5, h:0.3,
  fontSize:10, color:MUTED, align:"right" }); };

// ── M2 Chapter 간지 ───────────────────────────────────────────────
function m2(num, ko, en) {
  const s = pres.addSlide();
  R(s, { x:0, y:0, w:4.55, h:7.5, fill:{color:"8A8A8A"} });
  T(s, "CHAPTER", { x:0.5, y:2.52, w:3.3, h:0.42, fontSize:19, color:"FFFFFF", charSpacing:2 });
  T(s, String(num), { x:0.44, y:2.86, w:2.2, h:1.7, fontSize:112, color:"FFFFFF" });
  T(s, ko, { x:5.35, y:3.02, w:7.4, h:0.86, fontSize:38, bold:true, color:INK, valign:"middle" });
  R(s, { x:5.38, y:4.06, w:7.35, h:0.022, fill:{color:INK} });
  T(s, en, { x:5.35, y:4.28, w:7.4, h:0.42, fontSize:16, color:MUTED });
  pageNo(s);
  return s;
}

// ── M3 개념 ───────────────────────────────────────────────────────
function m3(num, title, sub) {
  const s = pres.addSlide();
  T(s, [{text:`${num}. `,options:{fontSize:30,color:INK}},
        {text:title,options:{fontSize:30,bold:true,color:INK}},
        {text:`   ${sub}`,options:{fontSize:13,color:MUTED}}],
    { x:0.62, y:0.42, w:12.1, h:0.62, valign:"bottom" });
  R(s, { x:0.62, y:1.14, w:12.09, h:0.028, fill:{color:INK} });
  s._foot = () => { R(s,{x:0.62,y:6.84,w:12.09,h:0.012,fill:{color:RULE}}); pageNo(s); };
  return s;
}
const grayBar = (s,y,text,w=12.09,x=0.62) => {
  R(s,{x,y,w,h:0.4,fill:{color:BAR}});
  T(s,text,{x,y,w,h:0.4,fontSize:13,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
};
// 번호 박스 n열
function numCols(s, y, items, x0=0.62, totalW=12.09) {
  const cw = totalW / items.length;
  items.forEach(([n,ko,en,desc],i) => {
    const x = x0 + i*cw;
    if (i) R(s,{x:x-0.09,y:y,w:0.012,h:2.52,fill:{color:RULE}});
    R(s,{x:x+cw/2-0.49,y:y+0.02,w:0.98,h:0.78,fill:{color:BAR}});
    T(s,n,{x:x+cw/2-0.49,y:y+0.02,w:0.98,h:0.78,fontSize:25,color:"FFFFFF",align:"center",valign:"middle"});
    T(s,ko,{x,y:y+0.96,w:cw,h:0.4,fontSize:17,bold:true,color:INK,align:"center"});
    if (en) T(s,en,{x,y:y+1.36,w:cw,h:0.3,fontSize:11.5,color:MUTED,align:"center"});
    R(s,{x:x+cw/2-0.75,y:y+1.72,w:1.5,h:0.012,fill:{color:RULE}});
    T(s,desc,{x:x+0.3,y:y+1.86,w:cw-0.6,h:0.96,fontSize:12.5,color:"333333",align:"center",lineSpacing:19});
  });
}
// 회색 강조 박스
const noteBox = (s,y,runs,h=0.72) => {
  R(s,{x:0.62,y,w:12.09,h,fill:{color:"F2F2F2"},line:{color:RULE,width:1}});
  T(s,runs,{x:0.9,y,w:11.5,h,fontSize:15,valign:"middle"});
};
// 검은 배너
const blackBanner = (s,y,text) => {
  R(s,{x:0.62,y,w:12.09,h:0.72,fill:{color:INK}});
  T(s,text,{x:0.62,y,w:12.09,h:0.72,fontSize:18,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
};

// ── M4 산출물 ─────────────────────────────────────────────────────
function m4(o) {
  const s = pres.addSlide();
  T(s,o.crumb,{x:0.52,y:0.22,w:4.2,h:0.34,fontSize:12.5,bold:true,color:o.c,valign:"middle"});
  T(s,o.crumbTitle,{x:4.3,y:0.22,w:6.3,h:0.34,fontSize:12.5,bold:true,color:INK,align:"center",valign:"middle"});
  R(s,{x:10.98,y:0.19,w:1.84,h:0.4,fill:{color:o.badgeColor||o.c}});
  T(s,o.badge,{x:10.98,y:0.19,w:1.84,h:0.4,fontSize:11.5,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  RR(s,{x:0.52,y:0.74,w:12.3,h:5.72,rectRadius:0.06,fill:{color:"FFFFFF"},line:{color:"E2E2E2",width:1}});
  RR(s,{x:0.82,y:1.0,w:2.62,h:0.36,rectRadius:0.18,fill:{color:o.c}});
  T(s,o.phase,{x:0.82,y:1.0,w:2.62,h:0.36,fontSize:10.5,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  RR(s,{x:3.54,y:1.0,w:2.3,h:0.36,rectRadius:0.18,fill:{color:o.bg}});
  T(s,o.step,{x:3.54,y:1.0,w:2.3,h:0.36,fontSize:10.5,bold:true,color:o.c,align:"center",valign:"middle"});
  let cx = 12.52;
  [...(o.chips||[])].reverse().forEach(([k,v]) => {
    const w = 1.76; cx -= w;
    R(s,{x:cx,y:1.0,w,h:0.36,fill:{color:"F5F6F8"},line:{color:"E2E2E2",width:1}});
    T(s,[{text:k+" ",options:{bold:true,color:INK}},{text:v,options:{color:"666666"}}],
      {x:cx,y:1.0,w,h:0.36,fontSize:9.5,align:"center",valign:"middle"});
    cx -= 0.1;
  });
  T(s,o.title,{x:0.82,y:1.46,w:11.7,h:0.62,fontSize:28,bold:true,color:INK});
  T(s,o.sub,{x:0.82,y:2.08,w:11.7,h:0.32,fontSize:12.5,color:MUTED});
  R(s,{x:0.52,y:6.6,w:12.3,h:0.56,fill:{color:o.c}});
  T(s,o.banner,{x:0.86,y:6.6,w:9.2,h:0.56,fontSize:14.5,bold:true,color:"FFFFFF",valign:"middle"});
  T(s,o.bannerRight,{x:10.0,y:6.6,w:2.5,h:0.56,fontSize:10.5,color:"FFFFFF",align:"right",valign:"middle"});
  T(s,o.note,{x:0.52,y:7.2,w:8.2,h:0.26,fontSize:8.5,color:"A6A6A6"});
  T(s,o.deliv,{x:8.6,y:7.2,w:3.9,h:0.26,fontSize:8.5,color:"A6A6A6",align:"right"});
  pageNo(s);
  return s;
}
// M4 본문: 표
function m4Table(s,x,y,w,cols,rows,c,rh=0.5) {
  R(s,{x,y,w,h:0.42,fill:{color:c}});
  let cxp = x+0.14;
  cols.forEach(([label,cw]) => { T(s,label,{x:cxp,y,w:cw,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"}); cxp += cw; });
  rows.forEach((r,i) => {
    const ry = y+0.42+i*rh; let rx = x+0.14;
    r.forEach((cell,j) => {
      const [cw] = cols[j].slice(1);
      const bold = j>0 && !/^—/.test(String(cell));
      T(s,String(cell),{x:rx,y:ry,w:cw,h:rh,fontSize:12,bold:j===1&&bold,color:j===0?"444444":INK,valign:"middle"});
      rx += cw;
    });
    R(s,{x,y:ry+rh-0.012,w,h:0.012,fill:{color:"EAEAEA"}});
  });
}
// M4 본문: 카드 n개
function m4Cards(s,y,cards,c,bg,h=1.52,x0=0.82,totalW=11.7) {
  const gap=0.26, cw=(totalW-gap*(cards.length-1))/cards.length;
  cards.forEach(([t,d],i) => {
    const x = x0+i*(cw+gap);
    RR(s,{x,y,w:cw,h,rectRadius:0.05,fill:{color:bg},line:{color:"DDDDDD",width:1}});
    T(s,t,{x:x+0.24,y:y+0.16,w:cw-0.48,h:0.34,fontSize:13,bold:true,color:c});
    T(s,d,{x:x+0.24,y:y+0.54,w:cw-0.48,h:h-0.7,fontSize:11.5,color:"444444",lineSpacing:17});
  });
}

// ── M5 워크시트 ───────────────────────────────────────────────────
function m5(title, sub, task) {
  const s = pres.addSlide();
  T(s,title,{x:0.5,y:0.3,w:9.0,h:0.5,fontSize:26,bold:true,color:INK});
  T(s,sub,{x:0.5,y:0.82,w:9.6,h:0.3,fontSize:11.5,color:MUTED});
  R(s,{x:9.62,y:0.3,w:1.2,h:0.48,fill:{color:NAVY}});
  T(s,"추진과제",{x:9.62,y:0.3,w:1.2,h:0.48,fontSize:11.5,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  R(s,{x:10.82,y:0.3,w:2.0,h:0.48,fill:{color:"FFFFFF"},line:{color:NAVY,width:1}});
  if (task) T(s,task,{x:10.9,y:0.3,w:1.9,h:0.48,fontSize:11.5,color:INK,valign:"middle"});
  pageNo(s);
  return s;
}
// 워크시트 표 (빈칸 또는 채움)
function wsTable(s,x,y,w,cols,rows,opt={}) {
  const rh = opt.rh||0.74, head=opt.headColor||NAVY;
  R(s,{x,y,w,h:0.42,fill:{color:head}});
  let cxp=x;
  cols.forEach(([label,cw]) => {
    T(s,label,{x:cxp,y,w:cw,h:0.42,fontSize:11,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
    cxp+=cw;
  });
  (rows.length?rows:Array(opt.blankRows||4).fill(null)).forEach((r,i) => {
    const ry=y+0.42+i*rh; let rx=x;
    cols.forEach(([,cw],j) => {
      const fill = r ? "FFFFFF" : (opt.tint&&j>=opt.tint ? NAVYBG : "FFFFFF");
      R(s,{x:rx,y:ry,w:cw,h:rh,fill:{color:fill},line:{color:"C9D4E8",width:1}});
      if (r && r[j]!==undefined)
        T(s,String(r[j]),{x:rx+0.12,y:ry,w:cw-0.24,h:rh,fontSize:10.5,
          color:j===0?INK:"333333",bold:j===0,valign:"middle",lineSpacing:15});
      rx+=cw;
    });
  });
}
module.exports = { pres, pptx, applyTheme, THEME, F, INK, MUTED, RULE, BAR, RED,
  P1,P2,P3,P4,P5,P1BG,P2BG,P3BG,P4BG,P5BG,NAVY,NAVYBG,
  T,R,RR,EL,pageNo,m2,m3,grayBar,numCols,noteBox,blackBanner,m4,m4Table,m4Cards,m5,wsTable,
  getPG:()=>PG };
