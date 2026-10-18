const H = require("./full.js");
const { pres, applyTheme, THEME, F, INK, MUTED, RULE, BAR, RED,
        P1,P2,P3,P4,P5,P1BG,P2BG,P3BG,P4BG,P5BG,NAVY,
        T,R,RR,EL,pageNo,m2,m3,grayBar,numCols,noteBox,blackBanner,
        m4,m4Table,m4Cards,m5,wsTable } = H;

// ══════ S1 표지 ══════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { path: "cover_bg.png" };
  RR(s,{x:0.82,y:1.22,w:3.92,h:0.44,rectRadius:0.22,
    fill:{color:"FFFFFF",transparency:88},line:{color:"AFC8EC",width:1}});
  T(s,"PHYSICAL AI · EDGE INTELLIGENCE",{x:0.82,y:1.22,w:3.92,h:0.44,fontSize:10.5,
    color:"DCE8FA",align:"center",valign:"middle",charSpacing:2.2});
  T(s,"Physical AI",{x:0.78,y:1.78,w:6.0,h:0.92,fontSize:52,bold:true,color:"FFFFFF"});
  T(s,[{text:"챗봇을 넘어 ",options:{color:"FFFFFF"}},
       {text:"격전지",options:{color:"E8A355"}},
       {text:"로",options:{color:"FFFFFF"}}],
    {x:0.78,y:2.62,w:6.6,h:0.92,fontSize:52,bold:true});
  R(s,{x:0.82,y:3.86,w:1.5,h:0.035,fill:{color:"E8A355"}});
  T(s,"Physical AI: From Chatbots to the Contested Ground",
    {x:0.78,y:4.08,w:6.4,h:0.4,fontSize:17,bold:true,color:"FFFFFF"});
  T(s,"5 Phase 11 Step · 22 산출물 · 실측 데이터 기반 · LED 실습 포함",
    {x:0.78,y:4.46,w:6.6,h:0.34,fontSize:12.5,color:"CFE0F7"});
  T(s,"관측 → 인지 → 판단 → 구동 → 운용  |  2026.10",
    {x:0.78,y:6.42,w:6.0,h:0.34,fontSize:11.5,color:"BBD2F0"});
  [[6.222,5.760,"1","관측"],[8.256,4.950,"2","인지"],[9.665,3.450,"3","판단"],
   [11.010,1.950,"4","구동"],[12.075,1.080,"5","운용"]].forEach(([x,y,n,l])=>{
    EL(s,{x:x-0.21,y:y-0.21,w:0.42,h:0.42,fill:{color:"FFFFFF"},line:{color:"E8A355",width:2}});
    T(s,n,{x:x-0.21,y:y-0.21,w:0.42,h:0.42,fontSize:13,bold:true,color:"1F3A93",align:"center",valign:"middle"});
    T(s,l,{x:x-0.45,y:y+0.24,w:0.9,h:0.26,fontSize:11,bold:true,color:"FFFFFF",align:"center"});
  });
  H.pageNo(s); // 1
  s.addNotes("표지. 설명 없이 바로 시연으로 넘어간다.");
}

// ══════ CHAPTER 1 ════════════════════════════════════════════════
m2(1,"패러다임 시프트","Paradigm Shift · From Screen to Field");

{ const s=m3("1-1","화면 안의 AI","지난 3년, AI 는 텍스트를 주고받았다");
  grayBar(s,1.52,"화면 안의 AI (On-Screen AI)");
  numCols(s,2.28,[
    ["1","챗봇","Chatbot","사람이 묻고 모델이 답한다. 대화가 끝나면 세상에는 아무것도 남지 않는다."],
    ["2","코파일럿","Copilot","사람이 쓰던 것을 이어서 쓴다. 최종 판단과 책임은 사람이 진다."],
    ["3","문서 요약","Summarization","긴 것을 짧게 만든다. 요약이 틀려도 원본을 다시 읽으면 된다."]]);
  noteBox(s,5.42,[{text:"공통점 — ",options:{color:MUTED}},
    {text:"틀려도 되돌릴 수 있다.",options:{bold:true,color:INK}},
    {text:"  다시 생성하면 그만이다.",options:{color:"333333"}}]);
  s._foot();
  s.addNotes("세 가지 모두 텍스트 입출력이고 되돌릴 수 있다는 점을 짚는다."); }

{ const s=m3("1-2","화면 밖으로 나오면","규칙이 바뀐다");
  const rows=[["출력","텍스트","물리적 상태 변화"],["틀렸을 때","재생성","되돌릴 수 없음"],
    ["지연 허용","수 초","밀리초 (제어)"],["입력","사람이 입력","센서가 계속"],
    ["실패 비용","어색한 문장","기구 파손 · 안전"]];
  R(s,{x:3.0,y:1.62,w:4.76,h:0.62,fill:{color:"D9D9D9"}});
  R(s,{x:7.76,y:1.62,w:4.95,h:0.62,fill:{color:BAR}});
  T(s,"챗봇형 AI",{x:3.0,y:1.62,w:4.76,h:0.62,fontSize:14,bold:true,color:INK,align:"center",valign:"middle"});
  T(s,"Physical AI",{x:7.76,y:1.62,w:4.95,h:0.62,fontSize:14,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  rows.forEach(([l,a,b],i)=>{ const y=2.24+i*0.62;
    R(s,{x:0.62,y,w:12.09,h:0.012,fill:{color:RULE}});
    T(s,l,{x:0.62,y,w:2.3,h:0.62,fontSize:13.5,bold:true,color:INK,valign:"middle"});
    T(s,a,{x:3.0,y,w:4.76,h:0.62,fontSize:13.5,color:"555555",align:"center",valign:"middle"});
    T(s,b,{x:7.76,y,w:4.95,h:0.62,fontSize:13.5,bold:true,color:INK,align:"center",valign:"middle"}); });
  R(s,{x:0.62,y:5.34,w:12.09,h:0.012,fill:{color:RULE}});
  blackBanner(s,5.72,"“모터는 Ctrl+Z 가 없습니다”");
  s._foot(); s.addNotes("1부의 핵심. 다섯 행을 하나씩 짚는다."); }

{ const s=m3("1-3","왜 격전지인가","먼저 들어간 쪽이 자리를 차지한다");
  grayBar(s,1.52,"진입 장벽의 세 층 (Three Barriers)");
  numCols(s,2.28,[
    ["1","구조적 진입 장벽","Structural Barrier","소프트웨어만으로 되지 않는다. 하드웨어·제어·AI 가 동시에 필요하다."],
    ["2","현장에만 있는 데이터","Field-Only Data","공개 데이터셋으로 만들 수 없다. 그 공장, 그 조명, 그 카메라의 데이터다."],
    ["3","높은 교체 비용","High Switching Cost","설비에 한 번 박히면 수년을 간다. 늦게 들어가면 자리가 없다."]]);
  noteBox(s,5.42,[{text:"세 장벽은 서로를 강화한다 — ",options:{color:"333333"}},
    {text:"어려워서 늦고, 늦어서 데이터가 없고, 데이터가 없어서 더 어렵다.",options:{bold:true,color:INK}}]);
  s._foot(); }

{ const s=m3("1-4","왜 지금인가","세 가지가 동시에 가능해졌다");
  grayBar(s,1.52,"지금을 만든 세 조건 (Enablers)");
  numCols(s,2.28,[
    ["1","엣지 추론","Edge Inference","8GB 보드에서 비전 모델이 돈다. 오늘 시연한 것이 그것이다."],
    ["2","비전·언어 통합","Vision-Language","이미지를 보고 말로 답한다. 규칙으로 못 쓰던 판단이 가능해졌다."],
    ["3","온디바이스","On-Device","인터넷 없이, 데이터를 밖으로 내보내지 않고 판단한다."]]);
  noteBox(s,5.42,[{text:"다음 장부터는 ",options:{color:"333333"}},
    {text:"추정이 아니라 이 보드에서 실제로 잰 값",options:{bold:true,color:INK}},
    {text:"만 보여드립니다.",options:{color:"333333"}}]);
  s._foot(); }

{ const s=m4({crumb:"Phase 1 · Step 1.2 · 1.2.1",
    crumbTitle:"환경 진단 — 산출물 예시: 하드웨어 적합성 판정",
    badge:"실측 데이터", c:P1, bg:P1BG,
    phase:"PHASE 1 · Observe", step:"STEP 1.2 환경 진단",
    chips:[["모델","2.6 GB"],["색 판별","12/12"],["지연","1~3초"]],
    title:"8GB 엣지 보드에서 무엇이 되나",
    sub:"Jetson Orin Nano 8GB · 인터넷 연결 없이 · 실제 측정값",
    banner:"온디바이스에서 비전 모델이 실제로 돕니다", bannerRight:"Phase 1 · Step 1.2",
    note:"※ 측정 환경: Jetson Orin Nano Super 8GB · JetPack 6 · IMX219 · Qwen2.5-VL-3B Q4_K_M",
    deliv:"산출물 1.2.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.62,5.9,[["측정 항목",2.5],["결과",3.1]],
    [["모델","Qwen2.5-VL 3B (Q4_K_M)"],["가중치","2.59 GB"],["잔여 메모리","2.0 GB"],
     ["색 판별 정확도","12색 전부 한 칸 이내"],["추론 지연","1.3 ~ 3.3 초"],["인터넷","불필요"]],P1,0.52);
  m4Cards(s,2.62,[["왜 3B 인가","7B 는 적재되지만 운용 중 죽는다.\n3B 가 더 빠르고 정확하며 유일하게 동작했다."]],P1,"F7FAFB",1.52,7.0,5.5);
  m4Cards(s,4.34,[["무엇이 전제인가","GUI 를 끄면 가용이 2.3GB → 6.4GB 가 된다.\n데스크톱이 떠 있으면 아무것도 올라가지 않는다."]],P1,"F7FAFB",1.52,7.0,5.5);
  s.addNotes("실측값만 쓴다. 업계 전망이나 추정치는 넣지 않는다."); }

{ const s=m4({crumb:"Phase 1 · Step 1.2 · 1.2.2",
    crumbTitle:"환경 진단 — 실패 사례: 데모는 되고 운용은 안 된 경우",
    badge:"실패 사례", c:RED, bg:"F7E4E1", badgeColor:RED,
    phase:"PHASE 1 · Observe", step:"STEP 1.2 환경 진단",
    chips:[["잔여","100 MiB"],["스왑","3.7GB 전소"]],
    title:"그런데 7B 는 죽었다",
    sub:"같은 보드, 같은 모델 계열. 조건만 운용 상태로 바꿨을 때",
    banner:"적재되는 것과 운용되는 것은 다릅니다", bannerRight:"Phase 1 · Step 1.2",
    note:"※ 측정 환경: 동일 보드에서 카메라 파이프라인·제어 루프를 함께 가동한 상태",
    deliv:"산출물 1.2.2 · P-AI 방법론 5-Phase"});
  [["1","서버 적재","성공","가용 530 MB","1F8A4C"],
   ["2","+ 카메라 · 제어 루프","견딤","가용 393 MB","D68910"],
   ["3","+ 추론 요청 1건","사망","스왑 3.7GB 전소",RED]].forEach(([n,t,v,mt,c],i)=>{
    const x=0.82+i*3.95;
    RR(s,{x,y:2.66,w:3.72,h:1.96,rectRadius:0.05,fill:{color:"FCFCFC"},line:{color:"E2E2E2",width:1}});
    EL(s,{x:x+0.24,y:2.9,w:0.46,h:0.46,fill:{color:c}});
    T(s,n,{x:x+0.24,y:2.9,w:0.46,h:0.46,fontSize:13,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
    T(s,t,{x:x+0.82,y:2.92,w:2.7,h:0.42,fontSize:13.5,bold:true,color:INK,valign:"middle"});
    T(s,v,{x:x+0.24,y:3.56,w:3.24,h:0.52,fontSize:24,bold:true,color:c});
    T(s,mt,{x:x+0.24,y:4.12,w:3.24,h:0.34,fontSize:11.5,color:"666666"});
    if(i<2) T(s,"→",{x:x+3.72,y:3.42,w:0.23,h:0.4,fontSize:17,color:"AAAAAA",align:"center"}); });
  R(s,{x:0.82,y:4.88,w:11.7,h:1.42,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"무엇을 놓쳤나",{x:1.08,y:5.02,w:4.0,h:0.32,fontSize:13,bold:true,color:RED});
  T(s,"이미지 인코딩에 필요한 연산 버퍼 약 700MB 가 들어갈 자리가 없다. 서버 단독으로는 적재되고, 카메라와 제어 루프까지도 견딘다. 그러나 추론 요청이 들어오는 순간 죽는다.",
    {x:1.08,y:5.38,w:11.1,h:0.46,fontSize:12.5,color:"444444"});
  T(s,"→ 새 모델을 검토할 때는 반드시 제어 루프를 함께 돌리면서 재야 한다.",
    {x:1.08,y:5.86,w:11.1,h:0.34,fontSize:12.5,bold:true,color:INK});
  s.addNotes("60분 축약판에서도 빼지 않는다. PoC 와 현장의 차이를 만드는 지점."); }

{ const s=m4({crumb:"Phase 1 · Step 1.1 · 1.1.2",
    crumbTitle:"관측 대상 정의 — 점검표: 성공 신호가 거짓인 경우",
    badge:"점검표", c:P1, bg:P1BG,
    phase:"PHASE 1 · Observe", step:"STEP 1.1 관측 대상",
    chips:[["사례","4건"],["전부","실제 발생"]],
    title:"성공처럼 보였지만 아니었던 것들",
    sub:"네 번 모두 화면상으로는 정상이었다",
    banner:"무엇을 근거로 “동작한다” 고 말할 것인가", bannerRight:"Phase 1 · Step 1.1",
    note:"※ 모두 본 커리큘럼 제작 과정에서 실제로 겪은 사례입니다",
    deliv:"산출물 1.1.2 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["층위",2.0],["성공처럼 보인 것",4.3],["실제",5.2]],
    [["하드웨어","/dev/video0 존재, 캡처 성공","전 픽셀이 같은 값 (4100)"],
     ["모델 서버","model loaded, /health ok","첫 요청에 사망"],
     ["AI 출력","스키마 통과","검증기가 5회 중 4회 거부"],
     ["운용","30fps 로 잘 돎","폴백이 실패를 완전히 가림"]],P1,0.62);
  R(s,{x:0.82,y:5.6,w:11.7,h:0.7,fill:{color:"F7FAFB"},line:{color:"D7E6E9",width:1}});
  T(s,[{text:"공통 해법 — ",options:{color:"555555"}},
       {text:"출력을 직접 잰다.",options:{bold:true,color:P1}},
       {text:"  픽셀 값, 사진 속 색, 실제 요청. 상태 표시가 아니라 결과물을 본다.",options:{color:"444444"}}],
    {x:1.08,y:5.6,w:11.2,h:0.7,fontSize:12.5,valign:"middle"}); }

{ const s=m3("1-5","1부 요약","네 가지만 기억하면 된다");
  grayBar(s,1.52,"요약 (Summary)");
  numCols(s,2.28,[
    ["①","화면 밖","",'되돌릴 수 없다.\n그래서 검증이 구조여야 한다.'],
    ["②","격전지","",'진입 장벽 · 현장 데이터 · 락인.\n늦으면 자리가 없다.'],
    ["③","지금 가능","",'엣지에서 비전 모델이 돈다.\n인터넷 없이.'],
    ["④","단, 조건부","",'되는 것과 운용되는 것은\n다르다.']]);
  noteBox(s,5.42,[{text:"다음 장 — ",options:{color:MUTED}},
    {text:"그래서 어떤 구조로 만들어야 하는가.",options:{bold:true,color:INK}}]);
  s._foot(); }

module.exports = { H };
