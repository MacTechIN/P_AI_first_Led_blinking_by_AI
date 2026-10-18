const pptx = require("pptxgenjs");
const { applyTheme } = require("/home/sam/.claude/skills/synced/e0ded2c0-5687-437f-81a9-25283e305c85_ef2d0686-80bf-4c46-9dcd-37619fed09ad/pptx/scripts/apply_theme.js");

const THEME = {
  name: "PhysicalAI",
  headFontFace: "Malgun Gothic",
  bodyFontFace: "Malgun Gothic",
  colors: {
    dk1: "1A1A1A", lt1: "FFFFFF", dk2: "404040", lt2: "F2F2F2",
    accent1: "1F3A93", accent2: "E8963C", accent3: "7F7F7F",
    accent4: "7B3FA0", accent5: "1F8A4C", accent6: "C0392B",
    hlink: "1F3A93", folHlink: "7F7F7F",
  },
};
const F = "Malgun Gothic";
const INK = "1A1A1A", MUTED = "7F7F7F", RULE = "BFBFBF", BAR = "7F7F7F";

const pres = new pptx();
pres.layout = "LAYOUT_WIDE";          // 13.33 x 7.5
pres.theme = { headFontFace: F, bodyFontFace: F };
pres.author = "Physical AI Curriculum";
pres.title = "Physical AI: 챗봇을 넘어 격전지로";

// ── 레이아웃 M2/M3/M4 공통 요소는 슬라이드별로 조립한다 ───────────────
pres.defineSlideMaster({ title: "M_BLANK", background: { color: "FFFFFF" } });

// 페이지 번호
const pageNo = (s, n) => s.addText(String(n), {
  x: 12.52, y: 7.18, w: 0.5, h: 0.3, fontSize: 10, color: MUTED,
  align: "right", fontFace: F, isTextBox: true, margin: 0,
});

// M3 제목 블록: 큰 제목 + 작은 회색 부제 + 굵은 가로선
function m3Head(s, num, title, sub) {
  s.addText([
    { text: `${num}. `, options: { fontSize: 30, bold: false, color: INK } },
    { text: title, options: { fontSize: 30, bold: true, color: INK } },
    { text: `   ${sub}`, options: { fontSize: 13, color: MUTED } },
  ], { x: 0.62, y: 0.42, w: 12.1, h: 0.62, fontFace: F, isTextBox: true,
       margin: 0, valign: "bottom" });
  s.addShape(pres.ShapeType.rect, { x: 0.62, y: 1.14, w: 12.09, h: 0.028,
                                    fill: { color: INK } });
}
// M3 하단 마감선
const m3Foot = (s) => s.addShape(pres.ShapeType.rect,
  { x: 0.62, y: 6.84, w: 12.09, h: 0.012, fill: { color: RULE } });

// M3 회색 헤더바
const grayBar = (s, y, text, w = 12.09, x = 0.62) => {
  s.addShape(pres.ShapeType.rect, { x, y, w, h: 0.4, fill: { color: BAR } });
  s.addText(text, { x, y, w, h: 0.4, fontSize: 13, bold: true, color: "FFFFFF",
                    align: "center", valign: "middle", fontFace: F,
                    isTextBox: true, margin: 0 });
};

// ══ S1 · M1 표지 ═══════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { path: "cover_bg.png" };
  s.addShape(pres.ShapeType.roundRect, { x: 0.82, y: 1.22, w: 3.92, h: 0.44,
    rectRadius: 0.22, fill: { color: "FFFFFF", transparency: 88 },
    line: { color: "AFC8EC", width: 1 } });
  s.addText("PHYSICAL AI · EDGE INTELLIGENCE", { x: 0.82, y: 1.22, w: 3.92,
    h: 0.44, fontSize: 10.5, color: "DCE8FA", align: "center", valign: "middle",
    charSpacing: 2.2, fontFace: F, isTextBox: true, margin: 0 });

  s.addText("Physical AI", { x: 0.78, y: 1.78, w: 6.0, h: 0.92, fontSize: 52,
    bold: true, color: "FFFFFF", fontFace: F, isTextBox: true, margin: 0 });
  s.addText([
    { text: "챗봇을 넘어 ", options: { color: "FFFFFF" } },
    { text: "격전지", options: { color: "E8A355" } },
    { text: "로", options: { color: "FFFFFF" } },
  ], { x: 0.78, y: 2.62, w: 6.6, h: 0.92, fontSize: 52, bold: true,
       fontFace: F, isTextBox: true, margin: 0 });

  s.addShape(pres.ShapeType.rect, { x: 0.82, y: 3.86, w: 1.5, h: 0.035,
    fill: { color: "E8A355" } });
  s.addText("Physical AI: From Chatbots to the Contested Ground",
    { x: 0.78, y: 4.08, w: 6.4, h: 0.4, fontSize: 17, bold: true,
      color: "FFFFFF", fontFace: F, isTextBox: true, margin: 0 });
  s.addText("5 Phase 11 Step · 22 산출물 · 실측 데이터 기반 · LED 실습 포함",
    { x: 0.78, y: 4.46, w: 6.6, h: 0.34, fontSize: 12.5, color: "CFE0F7",
      fontFace: F, isTextBox: true, margin: 0 });
  s.addText("관측 → 인지 → 판단 → 구동 → 운용  |  2026.10",
    { x: 0.78, y: 6.42, w: 6.0, h: 0.34, fontSize: 11.5, color: "BBD2F0",
      fontFace: F, isTextBox: true, margin: 0 });

  // 단계 노드 (배경 곡선 위)
  const nodes = [[6.222, 5.760, "1", "관측"], [8.256, 4.950, "2", "인지"],
                 [9.665, 3.450, "3", "판단"], [11.010, 1.950, "4", "구동"],
                 [12.075, 1.080, "5", "운용"]];
  nodes.forEach(([x, y, n, label]) => {
    s.addShape(pres.ShapeType.ellipse, { x: x - 0.21, y: y - 0.21, w: 0.42,
      h: 0.42, fill: { color: "FFFFFF" }, line: { color: "E8A355", width: 2 } });
    s.addText(n, { x: x - 0.21, y: y - 0.21, w: 0.42, h: 0.42, fontSize: 13,
      bold: true, color: "1F3A93", align: "center", valign: "middle",
      fontFace: F, isTextBox: true, margin: 0 });
    s.addText(label, { x: x - 0.45, y: y + 0.24, w: 0.9, h: 0.26, fontSize: 11,
      bold: true, color: "FFFFFF", align: "center", fontFace: F,
      isTextBox: true, margin: 0 });
  });
  s.addNotes("표지. 설명 없이 바로 S2 시연으로 넘어간다.");
}

// ══ S2 · M2 Chapter 간지 ═══════════════════════════════════════════
{
  const s = pres.addSlide();
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 4.55, h: 7.5,
    fill: { color: "8A8A8A" } });
  s.addText("CHAPTER", { x: 0.5, y: 2.52, w: 3.3, h: 0.42, fontSize: 19,
    color: "FFFFFF", charSpacing: 2, fontFace: F, isTextBox: true, margin: 0 });
  s.addText("1", { x: 0.44, y: 2.86, w: 2.2, h: 1.7, fontSize: 112,
    color: "FFFFFF", fontFace: F, isTextBox: true, margin: 0 });

  s.addText("패러다임 시프트", { x: 5.35, y: 3.02, w: 7.4, h: 0.86,
    fontSize: 38, bold: true, color: INK, fontFace: F, isTextBox: true,
    margin: 0, valign: "middle" });
  s.addShape(pres.ShapeType.rect, { x: 5.38, y: 4.06, w: 7.35, h: 0.022,
    fill: { color: INK } });
  s.addText("Paradigm Shift · From Screen to Field", { x: 5.35, y: 4.28,
    w: 7.4, h: 0.42, fontSize: 16, color: MUTED, fontFace: F,
    isTextBox: true, margin: 0 });
  pageNo(s, 2);
  s.addNotes("Chapter 1 간지. 25분.");
}

// ══ S3 · M3 개념 — 1-1 ════════════════════════════════════════════
{
  const s = pres.addSlide();
  m3Head(s, "1-1", "화면 안의 AI", "지난 3년, AI 는 텍스트를 주고받았다");
  grayBar(s, 1.52, "화면 안의 AI (On-Screen AI)");

  const cols = [
    ["1", "챗봇", "Chatbot", "사람이 묻고 모델이 답한다. 대화가 끝나면 세상에는 아무것도 남지 않는다."],
    ["2", "코파일럿", "Copilot", "사람이 쓰던 것을 이어서 쓴다. 최종 판단은 사람이 한다."],
    ["3", "문서 요약", "Summarization", "긴 것을 짧게 만든다. 원본은 그대로 남아 있고, 요약이 틀려도 원본을 다시 읽으면 된다."],
  ];
  cols.forEach(([n, ko, en, desc], i) => {
    const x = 0.62 + i * 4.03;
    if (i) s.addShape(pres.ShapeType.rect, { x: x - 0.09, y: 2.28, w: 0.012,
      h: 2.52, fill: { color: RULE } });
    s.addShape(pres.ShapeType.rect, { x: x + 1.52, y: 2.3, w: 0.98, h: 0.78,
      fill: { color: BAR } });
    s.addText(n, { x: x + 1.52, y: 2.3, w: 0.98, h: 0.78, fontSize: 25,
      color: "FFFFFF", align: "center", valign: "middle", fontFace: F,
      isTextBox: true, margin: 0 });
    s.addText(ko, { x, y: 3.24, w: 4.02, h: 0.4, fontSize: 17, bold: true,
      color: INK, align: "center", fontFace: F, isTextBox: true, margin: 0 });
    s.addText(en, { x, y: 3.64, w: 4.02, h: 0.3, fontSize: 11.5, color: MUTED,
      align: "center", fontFace: F, isTextBox: true, margin: 0 });
    s.addShape(pres.ShapeType.rect, { x: x + 1.26, y: 4.0, w: 1.5, h: 0.012,
      fill: { color: RULE } });
    s.addText(desc, { x: x + 0.3, y: 4.14, w: 3.42, h: 0.9, fontSize: 12.5,
      color: "333333", align: "center", lineSpacing: 19, fontFace: F,
      isTextBox: true, margin: 0 });
  });

  s.addShape(pres.ShapeType.rect, { x: 0.62, y: 5.42, w: 12.09, h: 0.72,
    fill: { color: "F2F2F2" }, line: { color: RULE, width: 1 } });
  s.addText([
    { text: "공통점 — ", options: { color: MUTED } },
    { text: "틀려도 되돌릴 수 있다.", options: { bold: true, color: INK } },
    { text: "  다시 생성하면 그만이다.", options: { color: "333333" } },
  ], { x: 0.9, y: 5.42, w: 11.5, h: 0.72, fontSize: 15, valign: "middle",
       fontFace: F, isTextBox: true, margin: 0 });
  m3Foot(s); pageNo(s, 3);
  s.addNotes("세 가지 모두 텍스트 입출력이고, 틀려도 되돌릴 수 있다는 점을 강조한다.");
}

// ══ S4 · M3 비교 — 1-2 ════════════════════════════════════════════
{
  const s = pres.addSlide();
  m3Head(s, "1-2", "화면 밖으로 나오면", "규칙이 바뀐다");

  const rows = [
    ["", "챗봇형 AI", "Physical AI", 0],
    ["출력", "텍스트", "물리적 상태 변화", 1],
    ["틀렸을 때", "재생성", "되돌릴 수 없음", 1],
    ["지연 허용", "수 초", "밀리초 (제어)", 1],
    ["입력", "사람이 입력", "센서가 계속", 1],
    ["실패 비용", "어색한 문장", "기구 파손 · 안전", 1],
  ];
  const y0 = 1.62, rh = 0.62;
  rows.forEach(([label, a, b], i) => {
    const y = y0 + i * rh;
    if (i === 0) {
      s.addShape(pres.ShapeType.rect, { x: 3.0, y, w: 4.76, h: rh,
        fill: { color: "D9D9D9" } });
      s.addShape(pres.ShapeType.rect, { x: 7.76, y, w: 4.95, h: rh,
        fill: { color: BAR } });
      s.addText(a, { x: 3.0, y, w: 4.76, h: rh, fontSize: 14, bold: true,
        color: INK, align: "center", valign: "middle", fontFace: F,
        isTextBox: true, margin: 0 });
      s.addText(b, { x: 7.76, y, w: 4.95, h: rh, fontSize: 14, bold: true,
        color: "FFFFFF", align: "center", valign: "middle", fontFace: F,
        isTextBox: true, margin: 0 });
      return;
    }
    s.addShape(pres.ShapeType.rect, { x: 0.62, y, w: 12.09, h: 0.012,
      fill: { color: RULE } });
    s.addText(label, { x: 0.62, y, w: 2.3, h: rh, fontSize: 13.5, bold: true,
      color: INK, valign: "middle", fontFace: F, isTextBox: true, margin: 0 });
    s.addText(a, { x: 3.0, y, w: 4.76, h: rh, fontSize: 13.5, color: "555555",
      align: "center", valign: "middle", fontFace: F, isTextBox: true,
      margin: 0 });
    s.addText(b, { x: 7.76, y, w: 4.95, h: rh, fontSize: 13.5, bold: true,
      color: INK, align: "center", valign: "middle", fontFace: F,
      isTextBox: true, margin: 0 });
  });
  s.addShape(pres.ShapeType.rect, { x: 0.62, y: y0 + 6 * rh, w: 12.09,
    h: 0.012, fill: { color: RULE } });

  s.addShape(pres.ShapeType.rect, { x: 0.62, y: 5.72, w: 12.09, h: 0.72,
    fill: { color: INK } });
  s.addText("“모터는 Ctrl+Z 가 없습니다”", { x: 0.62, y: 5.72,
    w: 12.09, h: 0.72, fontSize: 18, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", fontFace: F, isTextBox: true,
    margin: 0 });
  m3Foot(s); pageNo(s, 4);
  s.addNotes("이 슬라이드가 1부의 핵심. 다섯 행을 하나씩 짚는다.");
}

// ══ M4 공통 조립기 ════════════════════════════════════════════════
function m4(s, o) {
  // 상단 브레드크럼
  s.addText(o.crumb, { x: 0.52, y: 0.22, w: 4.0, h: 0.34, fontSize: 12.5,
    bold: true, color: o.phaseColor, fontFace: F, isTextBox: true, margin: 0,
    valign: "middle" });
  s.addText(o.crumbTitle, { x: 4.2, y: 0.22, w: 6.4, h: 0.34, fontSize: 12.5,
    bold: true, color: INK, align: "center", fontFace: F, isTextBox: true,
    margin: 0, valign: "middle" });
  s.addShape(pres.ShapeType.rect, { x: 10.98, y: 0.19, w: 1.84, h: 0.4,
    fill: { color: o.badgeColor } });
  s.addText(o.badge, { x: 10.98, y: 0.19, w: 1.84, h: 0.4, fontSize: 11.5,
    bold: true, color: "FFFFFF", align: "center", valign: "middle",
    fontFace: F, isTextBox: true, margin: 0 });

  // 본문 카드
  s.addShape(pres.ShapeType.roundRect, { x: 0.52, y: 0.74, w: 12.3, h: 5.72,
    rectRadius: 0.06, fill: { color: "FFFFFF" },
    line: { color: "E2E2E2", width: 1 } });

  // Phase / Step 알약
  s.addShape(pres.ShapeType.roundRect, { x: 0.82, y: 1.0, w: 2.62, h: 0.36,
    rectRadius: 0.18, fill: { color: o.phaseColor } });
  s.addText(o.phase, { x: 0.82, y: 1.0, w: 2.62, h: 0.36, fontSize: 10.5,
    bold: true, color: "FFFFFF", align: "center", valign: "middle",
    fontFace: F, isTextBox: true, margin: 0 });
  s.addShape(pres.ShapeType.roundRect, { x: 3.54, y: 1.0, w: 2.06, h: 0.36,
    rectRadius: 0.18, fill: { color: o.stepBg } });
  s.addText(o.step, { x: 3.54, y: 1.0, w: 2.06, h: 0.36, fontSize: 10.5,
    bold: true, color: o.phaseColor, align: "center", valign: "middle",
    fontFace: F, isTextBox: true, margin: 0 });

  // 메트릭 칩 (우측)
  let cx = 12.52;
  [...o.chips].reverse().forEach(([k, v]) => {
    const w = 1.72;
    cx -= w;
    s.addShape(pres.ShapeType.rect, { x: cx, y: 1.0, w, h: 0.36,
      fill: { color: "F5F6F8" }, line: { color: "E2E2E2", width: 1 } });
    s.addText([{ text: k + " ", options: { bold: true, color: INK } },
               { text: v, options: { color: "666666" } }],
      { x: cx, y: 1.0, w, h: 0.36, fontSize: 9.5, align: "center",
        valign: "middle", fontFace: F, isTextBox: true, margin: 0 });
    cx -= 0.1;
  });

  // 제목 · 부제
  s.addText(o.title, { x: 0.82, y: 1.46, w: 11.7, h: 0.62, fontSize: 28,
    bold: true, color: INK, fontFace: F, isTextBox: true, margin: 0 });
  s.addText(o.sub, { x: 0.82, y: 2.08, w: 11.7, h: 0.32, fontSize: 12.5,
    color: MUTED, fontFace: F, isTextBox: true, margin: 0 });

  // 하단 배너
  s.addShape(pres.ShapeType.rect, { x: 0.52, y: 6.6, w: 12.3, h: 0.56,
    fill: { color: o.phaseColor } });
  s.addText(o.banner, { x: 0.86, y: 6.6, w: 9.2, h: 0.56, fontSize: 14.5,
    bold: true, color: "FFFFFF", valign: "middle", fontFace: F,
    isTextBox: true, margin: 0 });
  s.addText(o.bannerRight, { x: 10.0, y: 6.6, w: 2.5, h: 0.56, fontSize: 10.5,
    color: "FFFFFF", align: "right", valign: "middle", fontFace: F,
    isTextBox: true, margin: 0 });

  // 푸터
  s.addText(o.note, { x: 0.52, y: 7.2, w: 8.0, h: 0.26, fontSize: 8.5,
    color: "A6A6A6", fontFace: F, isTextBox: true, margin: 0 });
  s.addText(o.deliv, { x: 8.6, y: 7.2, w: 3.9, h: 0.26, fontSize: 8.5,
    color: "A6A6A6", align: "right", fontFace: F, isTextBox: true, margin: 0 });
}

// ══ S5 · M4 산출물 — 실측 ═════════════════════════════════════════
{
  const s = pres.addSlide();
  const TEAL = "0F7B8A";
  m4(s, { crumb: "Phase 1 · Step 1.2 · 1.2.1",
    crumbTitle: "환경 진단 — 산출물 예시: 하드웨어 적합성 판정",
    badge: "실측 데이터", badgeColor: TEAL,
    phase: "PHASE 1 · Observe", step: "STEP 1.2 환경 진단",
    phaseColor: TEAL, stepBg: "E3F1F3",
    chips: [["모델", "2.6 GB"], ["색 판별", "12/12"], ["지연", "1~3초"]],
    title: "8GB 엣지 보드에서 무엇이 되나",
    sub: "Jetson Orin Nano 8GB · 인터넷 연결 없이 · 실제 측정값",
    banner: "온디바이스에서 비전 모델이 실제로 돕니다",
    bannerRight: "Phase 1 · Step 1.2",
    note: "※ 측정 환경: Jetson Orin Nano Super 8GB · JetPack 6 · IMX219 · Qwen2.5-VL-3B Q4_K_M",
    deliv: "산출물 1.2.1 · P-AI 방법론 5-Phase" });

  const items = [["모델", "Qwen2.5-VL 3B (Q4_K_M)"], ["가중치", "2.59 GB"],
    ["잔여 메모리", "2.0 GB"], ["색 판별 정확도", "12색 전부 한 칸 이내"],
    ["추론 지연", "1.3 ~ 3.3 초"], ["인터넷", "불필요"]];
  const y0 = 2.62, rh = 0.52;
  s.addShape(pres.ShapeType.rect, { x: 0.82, y: y0, w: 5.9, h: 0.42,
    fill: { color: TEAL } });
  s.addText("측정 항목", { x: 0.96, y: y0, w: 2.4, h: 0.42, fontSize: 11.5,
    bold: true, color: "FFFFFF", valign: "middle", fontFace: F,
    isTextBox: true, margin: 0 });
  s.addText("결과", { x: 3.6, y: y0, w: 3.0, h: 0.42, fontSize: 11.5,
    bold: true, color: "FFFFFF", valign: "middle", fontFace: F,
    isTextBox: true, margin: 0 });
  items.forEach(([k, v], i) => {
    const y = y0 + 0.42 + i * rh;
    s.addText(k, { x: 0.96, y, w: 2.5, h: rh, fontSize: 12.5, color: "444444",
      valign: "middle", fontFace: F, isTextBox: true, margin: 0 });
    s.addText(v, { x: 3.6, y, w: 3.0, h: rh, fontSize: 12.5, bold: true,
      color: INK, valign: "middle", fontFace: F, isTextBox: true, margin: 0 });
    s.addShape(pres.ShapeType.rect, { x: 0.82, y: y + rh - 0.012, w: 5.9,
      h: 0.012, fill: { color: "EAEAEA" } });
  });

  // 우측 해설 카드
  const cards = [["왜 3B 인가", "7B 는 적재되지만 운용 중 죽는다.\n3B 가 더 빠르고 정확하며 유일하게 동작했다."],
                 ["무엇이 전제인가", "GUI 를 끄면 가용이 2.3GB → 6.4GB 가 된다.\n데스크톱이 떠 있으면 아무것도 올라가지 않는다."]];
  cards.forEach(([t, d], i) => {
    const y = 2.62 + i * 1.72;
    s.addShape(pres.ShapeType.roundRect, { x: 7.0, y, w: 5.5, h: 1.52,
      rectRadius: 0.05, fill: { color: "F7FAFB" },
      line: { color: "D7E6E9", width: 1 } });
    s.addText(t, { x: 7.26, y: y + 0.16, w: 5.0, h: 0.32, fontSize: 13,
      bold: true, color: TEAL, fontFace: F, isTextBox: true, margin: 0 });
    s.addText(d, { x: 7.26, y: y + 0.54, w: 5.0, h: 0.82, fontSize: 11.5,
      color: "444444", lineSpacing: 17, fontFace: F, isTextBox: true,
      margin: 0 });
  });
  pageNo(s, 5);
  s.addNotes("실측값만 쓴다. 업계 전망이나 추정치는 넣지 않는다.");
}

// ══ S6 · M4 실패 사례 — 7B ════════════════════════════════════════
{
  const s = pres.addSlide();
  const RED = "B03A2E";
  m4(s, { crumb: "Phase 1 · Step 1.2 · 1.2.2",
    crumbTitle: "환경 진단 — 실패 사례: 데모는 되고 운용은 안 된 경우",
    badge: "실패 사례", badgeColor: RED,
    phase: "PHASE 1 · Observe", step: "STEP 1.2 환경 진단",
    phaseColor: RED, stepBg: "F7E4E1",
    chips: [["잔여", "100 MiB"], ["스왑", "3.7GB 전소"]],
    title: "그런데 7B 는 죽었다",
    sub: "같은 보드, 같은 모델 계열. 조건만 운용 상태로 바꿨을 때",
    banner: "적재되는 것과 운용되는 것은 다릅니다",
    bannerRight: "Phase 1 · Step 1.2",
    note: "※ 측정 환경: 동일 보드에서 카메라 파이프라인·제어 루프를 함께 가동한 상태",
    deliv: "산출물 1.2.2 · P-AI 방법론 5-Phase" });

  const steps = [["1", "서버 적재", "성공", "가용 530 MB", "1F8A4C"],
                 ["2", "+ 카메라 · 제어 루프", "견딤", "가용 393 MB", "D68910"],
                 ["3", "+ 추론 요청 1건", "사망", "스왑 3.7GB 전소", RED]];
  steps.forEach(([n, t, verdict, metric, c], i) => {
    const x = 0.82 + i * 3.95;
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.66, w: 3.72, h: 1.96,
      rectRadius: 0.05, fill: { color: "FCFCFC" },
      line: { color: "E2E2E2", width: 1 } });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.24, y: 2.9, w: 0.46,
      h: 0.46, fill: { color: c } });
    s.addText(n, { x: x + 0.24, y: 2.9, w: 0.46, h: 0.46, fontSize: 13,
      bold: true, color: "FFFFFF", align: "center", valign: "middle",
      fontFace: F, isTextBox: true, margin: 0 });
    s.addText(t, { x: x + 0.82, y: 2.92, w: 2.7, h: 0.42, fontSize: 13.5,
      bold: true, color: INK, valign: "middle", fontFace: F, isTextBox: true,
      margin: 0 });
    s.addText(verdict, { x: x + 0.24, y: 3.56, w: 3.24, h: 0.52, fontSize: 24,
      bold: true, color: c, fontFace: F, isTextBox: true, margin: 0 });
    s.addText(metric, { x: x + 0.24, y: 4.12, w: 3.24, h: 0.34, fontSize: 11.5,
      color: "666666", fontFace: F, isTextBox: true, margin: 0 });
    if (i < 2) s.addText("→", { x: x + 3.72, y: 3.42, w: 0.23, h: 0.4,
      fontSize: 17, color: "AAAAAA", align: "center", fontFace: F,
      isTextBox: true, margin: 0 });
  });

  s.addShape(pres.ShapeType.rect, { x: 0.82, y: 4.88, w: 11.7, h: 1.42,
    fill: { color: "FBF4F3" }, line: { color: "EFD6D2", width: 1 } });
  s.addText("무엇을 놓쳤나", { x: 1.08, y: 5.02, w: 4.0, h: 0.32,
    fontSize: 13, bold: true, color: RED, fontFace: F, isTextBox: true,
    margin: 0 });
  s.addText("이미지 인코딩에 필요한 연산 버퍼 약 700MB 가 들어갈 자리가 없다. " +
    "서버 단독으로는 적재되고, 카메라와 제어 루프까지도 견딘다. " +
    "그러나 추론 요청이 들어오는 순간 죽는다.",
    { x: 1.08, y: 5.38, w: 11.1, h: 0.46, fontSize: 12.5, color: "444444",
      fontFace: F, isTextBox: true, margin: 0 });
  s.addText("→ 새 모델을 검토할 때는 반드시 제어 루프를 함께 돌리면서 재야 한다.",
    { x: 1.08, y: 5.86, w: 11.1, h: 0.34, fontSize: 12.5, bold: true,
      color: INK, fontFace: F, isTextBox: true, margin: 0 });
  pageNo(s, 6);
  s.addNotes("이 슬라이드는 60분 축약판에서도 빼지 않는다. PoC 와 현장의 차이를 만드는 지점.");
}

pres.writeFile({ fileName: "ch1-draft.pptx" })
  .then(() => applyTheme("ch1-draft.pptx", THEME))
  .then(() => console.log("built ch1-draft.pptx"))
  .catch(e => { console.error("ERR", e); process.exit(1); });
