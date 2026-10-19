module.exports = function(H){
const { pres, F, INK, MUTED, RULE, BAR, RED, P1,P2,P3,P4,P5,P1BG,P2BG,P3BG,P4BG,P5BG,NAVY,NAVYBG,
  T,R,RR,EL,m2,m3,grayBar,numCols,noteBox,blackBanner,m4,m4Table,m4Cards,m5,wsTable } = H;

// ══════ CHAPTER 4 ════════════════════════════════════════════════
m2(4,"P-AI 실전 적용","Adoption Roadmap · Where to Start");

{ const s=m3("4-1","왜 필요한가","조직 관점의 세 가지 동인");
  grayBar(s,1.52,"도입 동인 (Drivers)");
  numCols(s,2.28,[
    ["1","사람이 보던 것을 기계가","Automated Inspection","검사 · 감시 · 계수. 사람이 눈으로 하던 반복 판단을 넘긴다."],
    ["2","데이터가 밖으로 안 나간다","On-Premise","온디바이스 추론이면 영상도 판단도 보드를 벗어나지 않는다."],
    ["3","네트워크 없이 돈다","Offline","공장 · 현장 · 오지. 연결이 끊겨도 판단은 계속된다."]]);
  noteBox(s,5.42,[{text:"그러나 — ",options:{color:MUTED}},
    {text:"“AI 를 넣자” 로 시작하면 실패합니다.",options:{bold:true,color:INK}},
    {text:"  다음 장에서 그 이유를 봅니다.",options:{color:"333333"}}]);
  s._foot(); }

{ const s=m3("4-2","“AI 를 넣자” 로 시작하면 실패한다","흔한 실패 순서");
  const steps=[["AI 도입 결정","경영진 지시",BAR],["PoC","잘 되는 조건에서",BAR],
    ["데모 성공","박수",BAR],["현장 투입","운용 조건",BAR],["실패","원인 불명",RED]];
  steps.forEach(([t,d,c],i)=>{ const x=0.62+i*2.46;
    R(s,{x,y:1.9,w:2.2,h:1.1,fill:{color:c==RED?"FBF4F3":"F7F7F7"},
      line:{color:c==RED?"EFD6D2":"DDDDDD",width:1}});
    T(s,t,{x,y:2.06,w:2.2,h:0.42,fontSize:14,bold:true,color:c==RED?RED:INK,align:"center"});
    T(s,d,{x,y:2.48,w:2.2,h:0.34,fontSize:11,color:MUTED,align:"center"});
    if(i<4) T(s,"→",{x:x+2.2,y:2.26,w:0.26,h:0.4,fontSize:16,color:"AAAAAA",align:"center"}); });
  T(s,"↑",{x:8.85,y:3.06,w:0.5,h:0.3,fontSize:16,color:RED,align:"center"});
  R(s,{x:0.62,y:3.5,w:12.09,h:1.46,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"실패 지점 — 데모 환경 ≠ 운용 환경",{x:0.9,y:3.64,w:11.5,h:0.36,fontSize:15,bold:true,color:RED});
  T(s,"PoC 는 모델만 띄워놓고 잽니다. 현장에서는 카메라 파이프라인과 제어 루프가 함께 돕니다.\n7B 가 적재되고 카메라까지 견디다가 추론 요청에서 죽은 것이 정확히 이 차이입니다 (1-5 참조).",
    {x:0.9,y:4.04,w:11.5,h:0.78,fontSize:12.5,color:"444444",lineSpacing:18});
  noteBox(s,5.12,[{text:"PoC 는 ",options:{color:"333333"}},
    {text:"운용 조건으로 해야 합니다.",options:{bold:true,color:INK}},
    {text:"  잘 되는 조건에서 재면 잘 된다는 사실만 확인합니다.",options:{color:"333333"}}]);
  blackBanner(s,6.0,"측정 조건이 결론을 만듭니다");
  s._foot(); }

// 로드맵 (M4)
{ const s=m4({crumb:"Phase 1 ~ 5",
    crumbTitle:"AX 전략가의 로드맵 — P-AI 5 Phase 11 Step",
    badge:"로드맵", c:NAVY, bg:NAVYBG,
    phase:"P-AI 방법론", step:"5 Phase · 11 Step",
    chips:[["산출물","22건"],["최소 기간","14주"]],
    title:"무엇부터, 어떤 순서로",
    sub:"1단계는 AI 가 아니다 — 지금 사람이 무엇을 보고 있는지부터 적는다",
    banner:"규칙 단계를 건너뛰면 AI 가 무엇을 개선했는지 알 수 없습니다", bannerRight:"P-AI 방법론",
    note:"※ 기간은 과제 규모에 따라 달라집니다. 순서는 바뀌지 않습니다",
    deliv:"방법론 개요 · P-AI 5-Phase"});
  const ph=[["1","관측 설계","무엇을 볼 것인가","관측 목록 · 환경 진단","2주",P1,P1BG],
    ["2","인지 구축","센서와 특징","센서 식별서 · 노이즈 바닥","3주",P2,P2BG],
    ["3","판단 설계","규칙 → AI","지연 기준선 · A/B 비교","6주",P3,P3BG],
    ["4","구동 · 계약","장치와 안전","장치 선언서 · 워치독","3주",P4,P4BG],
    ["5","운용 · 환류","회귀와 확산","골든셋 · 확산 로드맵","지속",P5,P5BG]];
  ph.forEach(([n,ko,q,out,dur,c,bg],i)=>{ const x=0.82+i*2.36;
    R(s,{x,y:2.7,w:2.18,h:0.44,fill:{color:c}});
    T(s,`PHASE ${n}`,{x,y:2.7,w:2.18,h:0.44,fontSize:11,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
    R(s,{x,y:3.14,w:2.18,h:2.3,fill:{color:bg},line:{color:"DDDDDD",width:1}});
    T(s,ko,{x:x+0.1,y:3.26,w:1.98,h:0.36,fontSize:14,bold:true,color:INK,align:"center"});
    T(s,q,{x:x+0.1,y:3.64,w:1.98,h:0.34,fontSize:11,color:"555555",align:"center"});
    R(s,{x:x+0.26,y:4.06,w:1.66,h:0.012,fill:{color:"CCCCCC"}});
    T(s,out,{x:x+0.1,y:4.18,w:1.98,h:0.8,fontSize:10.5,color:"444444",align:"center",lineSpacing:15});
    R(s,{x:x+0.5,y:5.02,w:1.18,h:0.3,fill:{color:"FFFFFF"},line:{color:c,width:1}});
    T(s,dur,{x:x+0.5,y:5.02,w:1.18,h:0.3,fontSize:10.5,bold:true,color:c,align:"center",valign:"middle"});
    if(i<4) T(s,"→",{x:x+2.18,y:4.0,w:0.18,h:0.4,fontSize:14,color:"BBBBBB",align:"center"}); });
  R(s,{x:0.82,y:5.64,w:11.7,h:0.66,fill:{color:"F7F9FD"},line:{color:"D5DEF0",width:1}});
  T(s,[{text:"가장 흔한 실수 — ",options:{color:"444444"}},
       {text:"Phase 1 과 3 의 규칙 단계를 건너뛰고 바로 AI 로 가는 것.",options:{bold:true,color:NAVY}},
       {text:"  비교 기준도, 폴백도, 원인 분리 수단도 없이 시작하게 됩니다.",options:{color:"444444"}}],
    {x:1.08,y:5.64,w:11.2,h:0.66,fontSize:12,valign:"middle"}); }

// Phase 1 강조 (M4)
{ const s=m4({crumb:"Phase 1 · Step 1.1 · 1.1.1",
    crumbTitle:"관측 대상 정의 — 산출물 예시: 관측 목록",
    badge:"산출물 예시", c:P1, bg:P1BG,
    phase:"PHASE 1 · Observe", step:"STEP 1.1 관측 대상",
    chips:[["기간","2주"],["질문","하나"]],
    title:"“지금 사람이 무엇을 보고 있나”",
    sub:"“AI 로 무엇을 할까” 가 아니다. 질문의 방향이 반대다",
    banner:"사람이 보고 있지 않은 것은 AI 도 볼 필요가 없습니다", bannerRight:"Phase 1 · Step 1.1",
    note:"※ 교육용 예시입니다. 실제로는 현장 관찰과 인터뷰로 채웁니다",
    deliv:"산출물 1.1.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["사람이 보는 것",3.3],["빈도",1.6],["판단 기준",3.4],["틀리면",3.2]],
    [["부품 색상이 맞는가","건당","도색 표준 색상표","재작업 · 고객 반품"],
     ["작업자가 구역 안에 있는가","상시","안전선 기준","안전 사고"],
     ["조립이 끝났는가","건당","부품 6종 체결 여부","후공정 정지"],
     ["작업대가 정리됐는가","교대마다","담당자 판단","다음 조 작업 지연"]],P1,0.54);
  R(s,{x:0.82,y:5.3,w:11.7,h:1.0,fill:{color:"F7FAFB"},line:{color:"D7E6E9",width:1}});
  T(s,"이 표를 채우면 다음 단계가 자동으로 정해집니다",{x:1.08,y:5.42,w:6.5,h:0.3,fontSize:12.5,bold:true,color:P1});
  T(s,"“판단 기준” 열이 숫자나 규칙으로 적히면 → 규칙으로 됩니다.  “담당자 판단” 이라고 적히면 → AI 후보입니다.\n“틀리면” 열이 비어 있으면, 그 관측은 애초에 중요하지 않다는 뜻입니다.",
    {x:1.08,y:5.74,w:11.1,h:0.5,fontSize:12,color:"444444",lineSpacing:17}); }

// 규칙 건너뛰지 마라 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.1",
    crumbTitle:"규칙 베이스라인 — 왜 건너뛰면 안 되는가",
    badge:"핵심", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.1 규칙 베이스라인",
    chips:[["실측","330배"],["규칙 판단","7.4 ms"]],
    title:"규칙 베이스라인이 주는 세 가지",
    sub:"없으면 AI 를 넣고도 그것이 나아진 것인지 알 수 없다",
    banner:"규칙으로 되는 것은 규칙으로 하십시오", bannerRight:"Phase 3 · Step 3.1",
    note:"※ 위치 판단 실측: 규칙 9/9 · 7.4 ms vs VLM 3/9 · 2,472 ms",
    deliv:"Phase 3 해설 · P-AI 방법론 5-Phase"});
  [["비교 기준","AI 가 얼마나 나아졌는지 재려면 전후를 같은 자로 재야 한다. 기준선이 없으면 “좋아진 것 같다” 밖에 말할 수 없다."],
   ["폴백","AI 가 죽어도 시스템은 돌아야 한다. 규칙 정책이 그 자리를 메운다."],
   ["원인 분리","AI 가 이상하게 굴 때 모델 문제인지 배선 문제인지 가른다. 같은 배선에서 규칙이 돌면 배선은 정상이다."]]
    .forEach(([t,d],i)=>{ const y=2.7+i*1.14;
      R(s,{x:0.82,y,w:11.7,h:1.0,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
      EL(s,{x:1.06,y:y+0.28,w:0.44,h:0.44,fill:{color:P3}});
      T(s,String(i+1),{x:1.06,y:y+0.28,w:0.44,h:0.44,fontSize:13,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
      T(s,t,{x:1.66,y:y+0.14,w:3.0,h:0.36,fontSize:14,bold:true,color:INK});
      T(s,d,{x:1.66,y:y+0.5,w:10.6,h:0.44,fontSize:12,color:"444444"}); });
  R(s,{x:0.82,y:6.1,w:11.7,h:0.2,fill:{color:"FFFFFF"}});
  T(s,"그리고 위치 판단처럼, 규칙이 AI 보다 330배 빠르고 정확한 경우가 실제로 있습니다.",
    {x:0.82,y:6.06,w:11.7,h:0.3,fontSize:12,bold:true,color:P3,align:"center"}); }

{ const s=m3("4-3","무엇부터 준비해야 할까","영역별 준비물과 흔한 착각");
  const rows=[["사람","측정할 줄 아는 사람","“AI 전문가부터 뽑자”"],
    ["데이터","현장 이미지 + 기대 출력","“데이터만 많으면 된다”"],
    ["하드웨어","실제 운용 조건의 보드","“일단 좋은 GPU 부터”"],
    ["프로세스","골든셋 · 회귀 탐지","“잘 되면 끝”"]];
  R(s,{x:0.62,y:1.62,w:2.4,h:0.56,fill:{color:"F2F2F2"}});
  R(s,{x:3.02,y:1.62,w:4.9,h:0.56,fill:{color:BAR}});
  R(s,{x:7.92,y:1.62,w:4.79,h:0.56,fill:{color:"F2F2F2"}});
  T(s,"영역",{x:0.62,y:1.62,w:2.4,h:0.56,fontSize:13,bold:true,color:INK,align:"center",valign:"middle"});
  T(s,"준비할 것",{x:3.02,y:1.62,w:4.9,h:0.56,fontSize:13,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  T(s,"흔한 착각",{x:7.92,y:1.62,w:4.79,h:0.56,fontSize:13,bold:true,color:INK,align:"center",valign:"middle"});
  rows.forEach(([a,b,c],i)=>{ const y=2.18+i*0.78;
    R(s,{x:0.62,y,w:12.09,h:0.012,fill:{color:RULE}});
    T(s,a,{x:0.62,y,w:2.4,h:0.78,fontSize:13.5,bold:true,color:INK,align:"center",valign:"middle"});
    T(s,b,{x:3.02,y,w:4.9,h:0.78,fontSize:13,bold:true,color:INK,align:"center",valign:"middle"});
    T(s,c,{x:7.92,y,w:4.79,h:0.78,fontSize:13,color:"888888",align:"center",valign:"middle"}); });
  R(s,{x:0.62,y:5.3,w:12.09,h:0.012,fill:{color:RULE}});
  noteBox(s,5.6,[{text:"가장 중요한 것은 첫 줄입니다 — ",options:{color:"333333"}},
    {text:"측정할 줄 아는 사람이 없으면 나머지가 다 있어도 데모에서 멈춥니다.",options:{bold:true,color:INK}}]);
  s._foot(); }

// 안전 (M4)
{ const s=m4({crumb:"Phase 4 · Step 4.2 · 4.2.1",
    crumbTitle:"안전 설계 — 산출물 예시: 안전 상태 정의서",
    badge:"산출물 예시", c:P4, bg:P4BG,
    phase:"PHASE 4 · Actuate", step:"STEP 4.2 안전 설계",
    chips:[["기본값","꺼짐"],["모터","필수"]],
    title:"안전장치는 부품보다 먼저 만든다",
    sub:"붙이고 나서 만들면, 그 사이의 실수 한 번이 기구를 부순다",
    banner:"서보의 “중립 복귀” 가 더 위험할 수 있습니다", bannerRight:"Phase 4 · Step 4.2",
    note:"※ 안전 상태는 장치가 아니라 설치 환경이 정합니다. 선언에 적고 펌웨어가 구현합니다",
    deliv:"산출물 4.2.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["장치",2.4],["호스트가 죽으면",3.6],["안전 상태",3.0],["워치독",2.7]],
    [["LED","계속 켜져 있다","소등","선택"],
     ["서보","마지막 각도를 밀어붙인다","— 환경이 정한다","필수"],
     ["스테퍼","계속 돈다 · 기구 파손","코일 전원 차단","필수"],
     ["히터","계속 가열된다","즉시 차단","필수"]],P4,0.54);
  R(s,{x:0.82,y:5.3,w:11.7,h:1.0,fill:{color:"FDF8F0"},line:{color:"E8D5B5",width:1}});
  T(s,"⚠  서보의 안전 상태는 자명하지 않습니다",{x:1.08,y:5.42,w:6.0,h:0.3,fontSize:12.5,bold:true,color:P4});
  T(s,"중립으로 복귀 → 이동 경로에 사람 손이 있으면 그것을 칩니다.  현재 위치 유지 → 부하가 걸려 있으면 과열됩니다.\n토크 해제 → 중력에 의해 팔이 떨어집니다. 아래에 무엇이 있느냐가 답을 정합니다.",
    {x:1.08,y:5.74,w:11.1,h:0.5,fontSize:12,color:"444444",lineSpacing:17}); }

// 골든셋 (M4)
{ const s=m4({crumb:"Phase 5 · Step 5.1 · 5.1.2",
    crumbTitle:"회귀 탐지 — 산출물 예시: 골든셋 평가 리포트",
    badge:"산출물 예시", c:P5, bg:P5BG,
    phase:"PHASE 5 · Operate", step:"STEP 5.1 회귀 탐지",
    chips:[["사례","5건"],["통과","2 / 5"]],
    title:"2/5 를 그대로 두었다",
    sub:"느슨하게 고쳐 5/5 로 만들면 정확히 틀린 반사신경을 가르치게 된다",
    banner:"골든셋은 통과하라고 있는 게 아니라 알아차리라고 있습니다", bannerRight:"Phase 5 · Step 5.1",
    note:"※ colour 만 고정했을 때는 5/5 통과였습니다. action 을 함께 고정하자 2/5 가 됐습니다",
    deliv:"산출물 5.1.2 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,7.4,[["사례",2.2],["기대",2.4],["실제",1.6],["판정",1.0]],
    [["red LED","on · red","none · red","FAIL"],["green LED","on · green","on · green","PASS"],
     ["blue LED","on · blue","none · blue","FAIL"],["yellow LED","on · yellow","off · yellow","FAIL"],
     ["LED 소등","off","off · white","PASS"]],P5,0.50);
  R(s,{x:8.4,y:2.66,w:4.12,h:1.74,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"무엇을 찾았나",{x:8.64,y:2.8,w:3.6,h:0.3,fontSize:13,bold:true,color:P5});
  T(s,"이 모델은 색은 안정적으로\n맞히지만 행동 선택이\n일관되지 않다.\n같은 장면에서 on / none / off 를\n오간다.",
    {x:8.64,y:3.14,w:3.6,h:1.16,fontSize:11.5,color:"444444",lineSpacing:17});
  R(s,{x:8.4,y:4.56,w:4.12,h:1.74,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"부분 일치는 양날이다",{x:8.64,y:4.7,w:3.6,h:0.3,fontSize:13,bold:true,color:RED});
  T(s,"적어둔 필드만 검사한다.\n적지 않은 필드의 회귀는 조용히 통과한다.\n\n무엇을 고정할지가 곧\n무엇을 지키겠다는 선언이다.",
    {x:8.64,y:5.04,w:3.6,h:1.16,fontSize:11.5,color:"444444",lineSpacing:17});
  R(s,{x:0.82,y:5.62,w:7.4,h:0.68,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"느슨하게 되돌리고 싶은 충동이 들 때",{x:1.06,y:5.7,w:6.9,h:0.28,fontSize:12,bold:true,color:P5});
  T(s,"묻습니다 — “5/5 로 만들면 모델이 좋아지나요?”",
    {x:1.06,y:5.98,w:6.9,h:0.3,fontSize:12,color:"444444"}); }

{ const s=m3("4-4","다음 주 월요일에 할 한 가지","하나만 고릅니다");
  grayBar(s,1.52,"선택지 (Pick One)");
  const opts=[["①","관측 목록 쓰기","우리 현장에서 사람이 눈으로 보는 것 5가지를 적는다"],
    ["②","규칙 가능성 표시","그중 규칙으로 되는 것에 표시한다"],
    ["③","운용 조건으로 재기","보드 하나를 주문해 운용 조건에서 측정한다"]];
  opts.forEach(([n,t,d],i)=>{ const y=2.1+i*1.06;
    R(s,{x:0.62,y,w:12.09,h:0.9,fill:{color:"F7F7F7"},line:{color:"DDDDDD",width:1}});
    R(s,{x:0.86,y:y+0.22,w:0.46,h:0.46,fill:{color:"FFFFFF"},line:{color:INK,width:1.5}});
    T(s,[{text:n+"  ",options:{color:MUTED}},{text:t,options:{bold:true,color:INK}}],
      {x:1.5,y:y+0.1,w:10.8,h:0.36,fontSize:15});
    T(s,d,{x:1.5,y:y+0.46,w:10.8,h:0.34,fontSize:12.5,color:"555555"}); });
  R(s,{x:0.62,y:5.4,w:12.09,h:1.1,fill:{color:"FFFFFF"},line:{color:INK,width:1}});
  T(s,"내가 고른 것",{x:0.9,y:5.52,w:2.4,h:0.3,fontSize:11.5,bold:true,color:MUTED});
  s._foot(); }

{ const s=m3("4-5","클로징","세 문장으로 끝냅니다");
  const lines=[["①","화면 밖에서는 되돌릴 수 없다","그래서 검증이 구조여야 한다"],
    ["②","측정하지 않은 것은 모른다","데모와 운용은 다르다"],
    ["③","AI 가 항상 낫지 않다","산술을 모델에게 시키지 마라"]];
  lines.forEach(([n,a,b],i)=>{ const y=2.0+i*1.3;
    T(s,n,{x:0.9,y,w:0.8,h:0.6,fontSize:30,bold:true,color:"CCCCCC",valign:"middle"});
    T(s,a,{x:1.9,y,w:10.6,h:0.6,fontSize:24,bold:true,color:INK,valign:"middle"});
    T(s,b,{x:1.9,y:y+0.58,w:10.6,h:0.4,fontSize:14,color:MUTED}); });
  R(s,{x:0.62,y:6.1,w:12.09,h:0.6,fill:{color:"F2F2F2"}});
  T(s,"저장소 · 실습 자료 · 실측 기록 전체 공개",
    {x:0.62,y:6.1,w:12.09,h:0.6,fontSize:13,color:"555555",align:"center",valign:"middle"});
  s._foot(); }

// ══════ CHAPTER 5 — 워크시트 ═════════════════════════════════════
m2(5,"실습 워크시트","Practice Workshop · Design Your Own");

// 실습 대상 현장
{ const s=m4({crumb:"CHAPTER 5 · PRACTICE",
    crumbTitle:"실습 대상 — 현장 개요",
    badge:"실습 대상", c:NAVY, bg:NAVYBG,
    phase:"실습 워크숍", step:"30분",
    chips:[["인원","4~5인"],["산출","워크시트 2종"]],
    title:"한빛정밀(주) 조립 1라인",
    sub:"소형 전자부품 조립 · 2교대 · 작업자 12명",
    banner:"30분 안에 \u201C무엇을 AI 로 하지 않을지\u201D 까지 정합니다", bannerRight:"Chapter 5",
    note:"※ 교육용 가상 사례이며 수치는 실습을 위한 가정입니다",
    deliv:"실습 대상 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,5.72,[["항목",1.9],["현황",3.5]],
    [["생산","일 2,400개 · 2교대"],["인원","조립 8 · 검사 2 · 반장 2"],
     ["검사","전수 육안 · 1인당 1,200개"],["불량","약 2.1% · 대부분 색상·체결"],
     ["기록","종이 체크시트 · 수기 집계"]],NAVY,0.50);
  R(s,{x:6.8,y:2.66,w:5.72,h:0.42,fill:{color:NAVY}});
  T(s,"현장의 목소리",{x:6.96,y:2.66,w:5.4,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  [["검사 담당","\u201C눈이 금방 피로해집니다. 교대 끝 무렵이 특히 걱정됩니다.\u201D"],
   ["반장","\u201C불량이 왜 늘었는지 물으면 답할 자료가 없습니다.\u201D"],
   ["공장장","\u201C사람을 늘릴 수는 없습니다. 6개월 안에 숫자로 보여줘야 합니다.\u201D"]]
    .forEach(([who,q],i)=>{ const y=3.14+i*0.84;
      T(s,who,{x:6.96,y,w:1.5,h:0.3,fontSize:11,bold:true,color:NAVY});
      T(s,q,{x:6.96,y:y+0.28,w:5.4,h:0.5,fontSize:11.5,color:"444444",lineSpacing:16}); });
  R(s,{x:0.82,y:5.62,w:11.7,h:0.68,fill:{color:"FFF8EC"},line:{color:"E8C88A",width:1}});
  T(s,"◆ 작업 힌트",{x:1.08,y:5.70,w:2.0,h:0.28,fontSize:11.5,bold:true,color:"B07A1E"});
  T(s,"\u201C눈이 피로하다\u201D 는 관측 빈도 문제입니다. \u201C답할 자료가 없다\u201D 는 기록 문제입니다. 둘은 다른 과제입니다.",
    {x:1.08,y:5.98,w:11.1,h:0.3,fontSize:11.5,color:"444444"}); }

// 예상 과제 5개
{ const s=m4({crumb:"CHAPTER 5 · PRACTICE",
    crumbTitle:"예상 과제 5개와 규칙 가능성",
    badge:"실습 대상", c:NAVY, bg:NAVYBG,
    phase:"실습 워크숍", step:"30분 · 3단계",
    chips:[["후보","5개"],["선택","1개"]],
    title:"다섯 후보 중 하나를 고릅니다",
    sub:"과제 발굴 시간을 줄이기 위해 후보를 미리 제시합니다",
    banner:"규칙으로 되는 것에 AI 를 쓰면 느리고 부정확해집니다", bannerRight:"Chapter 5",
    note:"※ 교육용 가상 사례이며 수치는 실습을 위한 가정입니다",
    deliv:"실습 대상 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["#",0.5],["과제",2.9],["해결할 문제",3.6],["규칙으로 되나",2.3],["먼저 따져볼 점",2.4]],
    [["1","부품 색상 검사","색상 불량 전수 육안","○  색상환으로 가능","조명 편차"],
     ["2","작업자 구역 이탈","안전선 침범 감지","○  위치는 산술","오탐 허용치"],
     ["3","조립 완료 판정","부품 6종 체결 확인","△  일부만","가림 · 각도"],
     ["4","작업대 정리 상태","교대 인수인계 분쟁","✕  AI 필요","기준의 주관성"],
     ["5","이상 움직임 감지","비정상 동작 조기 발견","○  차분으로 가능","노이즈 바닥"]],NAVY,0.48);
  R(s,{x:0.82,y:5.52,w:11.7,h:0.38,fill:{color:"C87F0A"}});
  T(s,"실습 진행 (30분)",{x:1.0,y:5.52,w:5.0,h:0.38,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  ["① 관측 + 과제 선택  10분","② 규칙 / AI 판정  15분","③ 한 줄 발표  5분"]
    .forEach((t,i)=>{ const x=0.82+i*3.95;
      R(s,{x,y:5.96,w:3.75,h:0.34,fill:{color:NAVYBG},line:{color:"C9D4E8",width:1}});
      T(s,t,{x,y:5.96,w:3.75,h:0.34,fontSize:10.5,bold:true,color:NAVY,align:"center",valign:"middle"}); }); }

// 워크시트 ① 관측 + 과제 선택
{ const s=m5("① 관측 목록 · 과제 선택","사람이 눈으로 보는 것을 적고, 그중 하나를 고릅니다 (10분)","");
  wsTable(s,0.5,1.3,12.32,
    [["사람이 보는 것",3.2],["빈도",1.3],["판단 기준",3.3],["틀리면 생기는 일",3.4],["선택",1.12]],
    [],{blankRows:4,rh:0.78});
  R(s,{x:0.5,y:4.88,w:12.32,h:0.42,fill:{color:"C87F0A"}});
  T(s,"고른 과제와 이유",{x:0.7,y:4.88,w:4.0,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  R(s,{x:0.5,y:5.30,w:12.32,h:0.64,fill:{color:"FFFFFF"},line:{color:"C9D4E8",width:1}});
  R(s,{x:0.5,y:6.0,w:12.32,h:1.0,fill:{color:"FFF8EC"},line:{color:"E8C88A",width:1}});
  T(s,"◆ \u201C판단 기준\u201D 이 숫자나 규칙으로 적히면 규칙 과제, \u201C담당자 판단\u201D 이면 AI 후보입니다.",
    {x:0.74,y:6.12,w:11.8,h:0.3,fontSize:11.5,bold:true,color:"B07A1E"});
  T(s,"\u201C틀리면 생기는 일\u201D 이 비어 있으면 그 관측은 애초에 중요하지 않다는 뜻입니다. 지우십시오.",
    {x:0.74,y:6.46,w:11.8,h:0.3,fontSize:11,color:"555555"}); }

// 워크시트 ② 규칙 / AI 판정 (핵심)
{ const s=m5("② 규칙 / AI 판정","이 실습의 핵심입니다. 판단 항목마다 규칙으로 되는지 먼저 따집니다 (15분)","");
  wsTable(s,0.5,1.3,12.32,
    [["판단 항목",3.0],["규칙으로 되나",1.9],["근거 (무엇을 재면 되나)",4.0],["결론",3.42]],
    [],{blankRows:5,rh:0.86,tint:1});
  R(s,{x:0.5,y:6.1,w:12.32,h:0.9,fill:{color:"FFF8EC"},line:{color:"E8C88A",width:1}});
  T(s,"◆ 색은 의미 해석이고 위치는 산술입니다. 산술을 모델에게 시키지 마십시오.",
    {x:0.74,y:6.2,w:11.8,h:0.3,fontSize:11.5,bold:true,color:"B07A1E"});
  T(s,"\u201C근거\u201D 열에 무엇을 재면 되는지 쓸 수 있으면 규칙 과제입니다. 쓸 수 없으면 AI 후보입니다.",
    {x:0.74,y:6.54,w:11.8,h:0.3,fontSize:11,color:"555555"}); }

// 워크시트 ② 작성 예시
{ const s=m5("② 규칙 / AI 판정 · 작성 예시","본 커리큘럼의 실측값으로 채운 예시입니다","");
  R(s,{x:10.82,y:0.84,w:2.0,h:0.3,fill:{color:"C87F0A"}});
  T(s,"작성 예시",{x:10.82,y:0.84,w:2.0,h:0.3,fontSize:10.5,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  wsTable(s,0.5,1.3,12.32,
    [["판단 항목",3.0],["규칙으로 되나",1.9],["근거 (무엇을 재면 되나)",4.0],["결론",3.42]],
    [["부품 색상이 맞는가","△  조건부","색상환 각도. 단 조명이 고정돼야 한다","규칙 + 노출 고정"],
     ["작업자가 구역 안인가","○  된다","가로 위치 좌표. 실측 9/9 · 7.4 ms","규칙 (AI 는 3/9)"],
     ["조립이 끝났는가","△  일부","부품 6종의 유무. 가림이 변수","규칙 먼저, 실패분만 AI"],
     ["작업대가 정리됐는가","✕  안 된다","\u201C정리\u201D 를 픽셀로 정의할 수 없다","AI 필요"],
     ["이상 움직임인가","○  된다","프레임 차분. 노이즈 바닥 0.300","규칙 (임계 0.601)"]],{rh:0.86});
  R(s,{x:0.5,y:6.1,w:12.32,h:0.9,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"다섯 중 넷이 규칙으로 되거나 조건부로 됩니다. AI 가 꼭 필요한 것은 하나뿐입니다.",
    {x:0.74,y:6.2,w:11.8,h:0.3,fontSize:11.5,bold:true,color:P5});
  T(s,"그 하나(\u201C정리되어 있나\u201D)가 AI 를 쓰는 이유이고, 나머지 넷은 AI 를 쓰지 않는 이유입니다.",
    {x:0.74,y:6.54,w:11.8,h:0.3,fontSize:11,color:"555555"}); }

// 발표 양식
{ const s=m5("③ 한 줄 발표","팀당 1분. 고른 과제와 \u201C AI 로 하지 않기로 한 것 \u201D 을 말합니다 (5분)","");
  R(s,{x:0.5,y:1.3,w:12.32,h:1.5,fill:{color:NAVYBG},line:{color:"C9D4E8",width:1}});
  T(s,"우리가 고른 과제는",{x:0.74,y:1.42,w:4.0,h:0.3,fontSize:11.5,bold:true,color:NAVY});
  T(s,"\u201C___ 를 ___ 로 판정한다\u201D",{x:0.74,y:1.78,w:11.8,h:0.6,fontSize:18,color:"AAAAAA"});
  R(s,{x:0.5,y:2.94,w:12.32,h:1.5,fill:{color:"FFFFFF"},line:{color:"C9D4E8",width:1}});
  T(s,"규칙으로 하기로 한 것 — 그리고 무엇을 재면 되는가",
    {x:0.74,y:3.06,w:11.8,h:0.3,fontSize:11.5,bold:true,color:NAVY});
  R(s,{x:0.5,y:4.58,w:12.32,h:1.5,fill:{color:"FFFFFF"},line:{color:"C9D4E8",width:1}});
  T(s,"AI 로 하지 않기로 한 것 — 그리고 그 이유",
    {x:0.74,y:4.70,w:11.8,h:0.3,fontSize:11.5,bold:true,color:NAVY});
  R(s,{x:0.5,y:6.22,w:12.32,h:0.78,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"가장 중요한 것은 세 번째 칸입니다 — 모든 것을 AI 로 하겠다는 계획은 아무것도 측정하지 않았다는 뜻입니다.",
    {x:0.74,y:6.22,w:11.8,h:0.78,fontSize:11.5,bold:true,color:P5,valign:"middle"}); }

// 가져가는 양식 (실습 시간에는 쓰지 않는다)
{ const s=m5("가져가는 양식","현장에 돌아가 과제를 실제로 진행할 때 채웁니다","");
  R(s,{x:10.82,y:0.84,w:2.0,h:0.3,fill:{color:MUTED}});
  T(s,"실습 외",{x:10.82,y:0.84,w:2.0,h:0.3,fontSize:10.5,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
  T(s,"안전 설계 — 액추에이터를 붙이기 전에",{x:0.5,y:1.3,w:6.0,h:0.34,fontSize:13,bold:true,color:P4});
  wsTable(s,0.5,1.7,6.0,
    [["장치",1.5],["호스트가 죽으면",1.8],["안전 상태",1.5],["워치독",1.2]],
    [],{blankRows:3,rh:0.72,headColor:P4});
  T(s,"골든셋 — 나빠진 것을 자동으로 알려면",{x:6.82,y:1.3,w:6.0,h:0.34,fontSize:13,bold:true,color:P5});
  wsTable(s,6.82,1.7,6.0,
    [["사례명",1.5],["입력",1.6],["기대 출력",1.4],["지키는 것",1.5]],
    [],{blankRows:3,rh:0.72,headColor:P5});
  R(s,{x:0.5,y:4.3,w:6.0,h:1.5,fill:{color:"FDF8F0"},line:{color:"E8D5B5",width:1}});
  T(s,"◆ 안전 상태는 장치가 아니라 설치 환경이 정합니다",
    {x:0.74,y:4.42,w:5.5,h:0.3,fontSize:11,bold:true,color:P4});
  T(s,"서보의 \u201C중립 복귀\u201D 는 이동 경로에 사람 손이 있으면\n위험하고, \u201C위치 유지\u201D 는 부하가 걸리면 과열되며,\n\u201C토크 해제\u201D 는 팔이 떨어집니다. 아래에 무엇이\n있느냐가 답을 정합니다.",
    {x:0.74,y:4.74,w:5.5,h:0.96,fontSize:10.5,color:"555555",lineSpacing:15});
  R(s,{x:6.82,y:4.3,w:6.0,h:1.5,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"◆ 적지 않은 필드는 회귀가 조용히 통과합니다",
    {x:7.06,y:4.42,w:5.5,h:0.3,fontSize:11,bold:true,color:P5});
  T(s,"\u201C지키는 것\u201D 을 반드시 적으십시오. 몇 주 뒤\n실패했을 때 무엇을 지키려 했는지 알아야\n고칠 수 있습니다. 사례 수를 늘리는 것이\n품질을 뜻하지 않습니다.",
    {x:7.06,y:4.74,w:5.5,h:0.96,fontSize:10.5,color:"555555",lineSpacing:15});
  R(s,{x:0.5,y:6.1,w:12.32,h:0.9,fill:{color:NAVYBG},line:{color:"C9D4E8",width:1}});
  T(s,"30분 실습에서는 이 둘을 쓰지 않습니다. 개념만 잡고, 현장에서 채웁니다.",
    {x:0.74,y:6.2,w:11.8,h:0.3,fontSize:11.5,bold:true,color:NAVY});
  T(s,"안전 설계는 Phase 4, 골든셋은 Phase 5 의 산출물입니다 — 둘 다 4장에서 예시를 봤습니다.",
    {x:0.74,y:6.54,w:11.8,h:0.3,fontSize:11,color:"555555"}); }

// ══════ 부록 ═════════════════════════════════════════════════════
{ const s=m3("부록 A","실측 데이터 색인","슬라이드에 쓰인 모든 수치의 출처");
  const rows=[["7B 사망 · 3B 2.6GB","tech/notes/vlm-on-orin-nano.md"],
    ["34ms / 3,306ms 지연","tech/notes/vs2-latency-baseline.md"],
    ["규칙 9/9 vs VLM 3/9","tech/notes/direction-rule-vs-vlm.md"],
    ["노이즈 0.300 · 증폭 3.2배","tech/notes/motion-threshold.md"],
    ["전역 밝기 +0.02","tech/notes/led-camera-detection.md"],
    ["공통 애노드 · 공통 저항","tech/notes/rgb-led-calibration.md"],
    ["12색 6/12 · 한 칸 이내","visuals/vlm-colour-loop.html"],
    ["코드 0줄 장치 추가","tech/adr/0010-declare-actuators-as-data.md"],
    ["전송 18 → 2회","tech/adr/0007-quantise-decisions-to-observation-quality.md"]];
  R(s,{x:0.62,y:1.52,w:12.09,h:0.42,fill:{color:BAR}});
  T(s,"수치",{x:0.86,y:1.52,w:5.0,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  T(s,"출처 문서",{x:6.2,y:1.52,w:6.3,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  rows.forEach(([a,b],i)=>{ const y=1.94+i*0.52;
    T(s,a,{x:0.86,y,w:5.2,h:0.52,fontSize:12,color:INK,valign:"middle"});
    T(s,b,{x:6.2,y,w:6.3,h:0.52,fontSize:11.5,color:"555555",valign:"middle"});
    if(i<rows.length-1) R(s,{x:0.62,y:y+0.5,w:12.09,h:0.012,fill:{color:"EAEAEA"}}); });
  T(s,"※ 모든 수치는 Jetson Orin Nano Super 8GB 한 대에서 직접 측정한 값입니다.",
    {x:0.62,y:6.50,w:12.09,h:0.3,fontSize:11,color:MUTED});
  s._foot(); }

{ const s=m3("부록 B","시연 대본과 축약판","실패 시 대안과 시간별 구성");
  grayBar(s,1.52,"시연 대본 (Demo Script)",5.94,0.62);
  [["오프닝","vs2_demo.py --policy vlm","설명 페이지 재생"],
   ["2-3","호스트 ↔ MCU 점멸 비교","녹화본"],
   ["3-3","rainbow.py --period 8","녹화본"],
   ["3-5","색지를 바꿔 들기","골든셋 이미지"]].forEach(([w,c,alt],i)=>{ const y=2.0+i*0.62;
    T(s,w,{x:0.86,y,w:1.0,h:0.56,fontSize:11.5,bold:true,color:INK,valign:"middle"});
    T(s,c,{x:1.96,y,w:2.6,h:0.56,fontSize:11,color:"444444",valign:"middle"});
    T(s,alt,{x:4.66,y,w:1.8,h:0.56,fontSize:11,color:MUTED,valign:"middle"});
    R(s,{x:0.62,y:y+0.56,w:5.94,h:0.012,fill:{color:"EAEAEA"}}); });
  R(s,{x:0.62,y:4.6,w:5.94,h:1.0,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"시연 15분 전 점검",{x:0.86,y:4.7,w:5.4,h:0.28,fontSize:12,bold:true,color:RED});
  T(s,"ls /dev/video0 /dev/ttyACM0\nmake test\n./host/evaluate.py   ← health 만 보면 모릅니다",
    {x:0.86,y:5.0,w:5.4,h:0.54,fontSize:10.5,color:"444444",lineSpacing:15});
  grayBar(s,1.52,"축약판 구성 (Short Versions)",6.03,6.68);
  [["60분","오프닝 · 1-2 · 1-5 · 2-3 · 2-8 · 3-1~3 · 4-2 · 4-4","18장"],
   ["90분","위 + 계약(2-5·2-6) · 측정(3-4) · 준비(4-3)","28장"],
   ["105분","전체","60장"]].forEach(([t,c,n],i)=>{ const y=2.0+i*0.94;
    R(s,{x:6.68,y,w:6.03,h:0.84,fill:{color:"F7F7F7"},line:{color:"DDDDDD",width:1}});
    T(s,t,{x:6.92,y:y+0.08,w:1.2,h:0.34,fontSize:14,bold:true,color:INK});
    T(s,n,{x:11.4,y:y+0.08,w:1.1,h:0.34,fontSize:11.5,color:MUTED,align:"right"});
    T(s,c,{x:6.92,y:y+0.42,w:5.5,h:0.34,fontSize:10.5,color:"555555"}); });
  R(s,{x:6.68,y:4.9,w:6.03,h:0.84,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"60분에서도 빼지 않는 것",{x:6.92,y:4.98,w:5.5,h:0.3,fontSize:12,bold:true,color:RED});
  T(s,"7B 사망 (1-5) · 위치 실패 (2-8)",{x:6.92,y:5.3,w:5.5,h:0.34,fontSize:11.5,color:"444444"});
  s._foot(); }
};
