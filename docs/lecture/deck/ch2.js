module.exports = function(H){
const { pres, F, INK, MUTED, RULE, BAR, RED, P1,P2,P3,P4,P5,P1BG,P2BG,P3BG,P4BG,P5BG,
  T,R,RR,EL,m2,m3,grayBar,numCols,noteBox,blackBanner,m4,m4Table,m4Cards } = H;

m2(2,"P-AI 아키텍처 해부","Physical AI Architecture · Core Skeleton");

// 2-1 전체 구조 (6계층)
{ const s=m3("2-1","전체 구조","여섯 계층과 그 위를 흐르는 다섯 단계");
  const layers=[["L5","관측 · 평가","결정 로그 · 골든셋 · 회귀 탐지",P5],
    ["L4","오케스트레이션","정책 루프 · 안전 · 기술 기록",P4],
    ["L3","추론","로컬 VLM · 구조화 출력",P3],
    ["L2","인지","카메라 · 센서 → 관측",P2],
    ["L1","장치 추상화","역량 계약 (capability contract)",P4],
    ["L0","하드웨어 · 전송","MCU · serial / SPI / WiFi",MUTED]];
  layers.forEach(([id,ko,desc,c],i)=>{ const y=1.52+i*0.78;
    R(s,{x:0.62,y,w:1.1,h:0.68,fill:{color:c}});
    T(s,id,{x:0.62,y,w:1.1,h:0.68,fontSize:15,bold:true,color:"FFFFFF",align:"center",valign:"middle"});
    R(s,{x:1.72,y,w:10.99,h:0.68,fill:{color:"F7F7F7"},line:{color:"E4E4E4",width:1}});
    T(s,ko,{x:1.96,y,w:3.0,h:0.68,fontSize:14,bold:true,color:INK,valign:"middle"});
    T(s,desc,{x:5.0,y,w:7.5,h:0.68,fontSize:12.5,color:"555555",valign:"middle"}); });
  noteBox(s,6.26,[{text:"계층 규칙 — ",options:{color:MUTED}},
    {text:"각 계층은 아래 계층 없이 시험할 수 있어야 한다.",options:{bold:true,color:INK}},
    {text:"  카메라가 없어도 L3~L5 를 개발할 수 있다.",options:{color:"333333"}}],0.56);
  s._foot(); }

// 2-2 수직 구조
{ const s=m3("2-2","수직 구조","거시에서 미시로 쪼개는 계층 축");
  T(s,"과제를 시간 순서에 따라 거시에서 미시로 쪼개어, 무엇을 어떤 순서로 수행할지 정의하는 계층 축",
    {x:1.6,y:1.42,w:10.4,h:0.34,fontSize:13,bold:true,color:INK,align:"center"});
  T(s,"수평 구조가 “그 일을 끝까지 가게 하는 힘” 이라면, 수직 구조는 “무엇을 어떤 순서로 하는가” 를 정하는 뼈대입니다.",
    {x:1.6,y:1.74,w:10.4,h:0.3,fontSize:11,color:MUTED,align:"center"});
  T(s,"거시",{x:0.62,y:2.16,w:0.6,h:0.3,fontSize:11,color:MUTED});
  const tiers=[["PHASE","대단계","P-AI 구축 라이프사이클의 거시적 흐름","관측 → 인지 → 판단 → 구동 → 운용",0],
    ["STEP","단계","PHASE 내부의 기능별 업무 단위","예: 규칙 베이스라인, AI 판단 도입",1],
    ["SUB STEP","세부 과제","STEP 을 구성하는 구체적 실행 단위","예: 지연 기준선 측정, A/B 비교",2],
    ["ACTIVITY","활동","현장에서 직접 수행되는 최소 단위","예: 30스텝 루프 실행, 전송 횟수 집계",3]];
  tiers.forEach(([en,ko,title,ex,i])=>{ const y=2.2+i*1.1, x=0.62+i*1.5;
    R(s,{x,y,w:2.3,h:0.86,fill:{color:BAR}});
    T(s,en,{x,y:y+0.1,w:2.3,h:0.38,fontSize:14,bold:true,color:"FFFFFF",align:"center"});
    T(s,ko,{x,y:y+0.46,w:2.3,h:0.28,fontSize:10.5,color:"EEEEEE",align:"center"});
    R(s,{x:x+2.3,y,w:12.71-x-2.3,h:0.86,fill:{color:"FFFFFF"},line:{color:"D9D9D9",width:1}});
    T(s,title,{x:x+2.52,y:y+0.1,w:9.4,h:0.36,fontSize:13,bold:true,color:INK});
    T(s,ex,{x:x+2.52,y:y+0.46,w:9.4,h:0.3,fontSize:11,color:MUTED});
    if(i<3) T(s,"↓",{x:x+0.5,y:y+0.86,w:0.4,h:0.24,fontSize:13,color:INK,align:"center"}); });
  T(s,"미시",{x:0.62,y:6.5,w:0.6,h:0.3,fontSize:11,color:MUTED});
  s._foot(); }

// 2-3 뼈대 1
{ const s=m3("2-3","뼈대 ① 느린 판단과 빠른 제어를 분리한다","Physical AI 의 제1원칙");
  grayBar(s,1.52,"왜 분리해야 하는가 (Why Separate)");
  numCols(s,2.28,[
    ["1","시간 척도가 다르다","Different Scales","AI 판단은 초 단위, 물리 제어는 밀리초 단위다. 하나로 묶으면 둘 다 망가진다."],
    ["2","실패 양상이 다르다","Different Failures","판단은 늦거나 틀릴 수 있다. 제어는 멈추면 안 된다."],
    ["3","책임이 다르다","Different Owners","무엇을 할지는 모델이, 어떻게 할지는 MCU 가 정한다."]]);
  noteBox(s,5.42,[{text:"결론 — ",options:{color:MUTED}},
    {text:"타이밍은 MCU 가 소유하고, 호스트는 의도만 보낸다.",options:{bold:true,color:INK}}]);
  s._foot(); }

// 지연 기준선 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.1 · 3.1.2",
    crumbTitle:"규칙 베이스라인 — 산출물 예시: 종단 지연 기준선",
    badge:"실측 데이터", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.1 규칙 베이스라인",
    chips:[["루프","34 ms"],["VLM","3,306 ms"],["배율","97배"]],
    title:"판단은 제어보다 97배 느리다",
    sub:"같은 보드, 같은 루프에서 단계별로 나눠 측정",
    banner:"모델은 3초 걸리는데 LED 는 끊기지 않습니다", bannerRight:"Phase 3 · Step 3.1",
    note:"※ 측정: argus:0 @640×480, 30~400 스텝 평균. 지연은 단계별로 분리 계측",
    deliv:"산출물 3.1.2 · P-AI 방법론 5-Phase"});
  const bars=[["촬영",30.4,"30.4 ms",MUTED],["특징 추출",3.6,"3.6 ms",MUTED],
    ["규칙 판단",0.05,"0.0 ms",MUTED],["VLM 판단",3306,"3,306 ms",P3]];
  const maxW=7.2;
  bars.forEach(([l,v,label,c],i)=>{ const y=2.76+i*0.62;
    T(s,l,{x:0.9,y,w:2.0,h:0.46,fontSize:12.5,color:"444444",valign:"middle"});
    R(s,{x:3.0,y:y+0.08,w:maxW,h:0.3,fill:{color:"F0F0F0"}});
    const w=Math.max(v/3306*maxW,0.035);
    R(s,{x:3.0,y:y+0.08,w,h:0.3,fill:{color:c}});
    T(s,label,{x:10.3,y,w:1.6,h:0.46,fontSize:12,bold:true,color:INK,valign:"middle"}); });
  R(s,{x:0.82,y:5.36,w:11.7,h:0.94,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
  T(s,"동기로 부르면 0.3 fps · 비동기로 돌리면 30 fps",
    {x:1.08,y:5.48,w:11.1,h:0.34,fontSize:13.5,bold:true,color:P3});
  T(s,"추론을 작업 스레드로 옮기고 decide() 가 마지막으로 완성된 명령을 즉시 반환하게 하면, 측정된 판단 시간은 0.0 ms 가 된다. 제어 루프는 30 fps 를 유지한다.",
    {x:1.08,y:5.84,w:11.1,h:0.36,fontSize:12,color:"444444"}); }

// 2-4 세 층 반복
{ const s=m3("2-4","같은 원리가 세 층에서 반복된다","하나의 원리가 세 번 나타난다");
  grayBar(s,1.52,"분리의 세 얼굴 (Three Faces of Separation)");
  numCols(s,2.28,[
    ["1","점멸 타이밍","34 ms 아래","호스트가 매번 켜고 끄면 USB 지연과 스케줄러 지터로 떨린다. MCU 가 소유한다."],
    ["2","VLM 판단","3초 위","추론을 작업 스레드로 옮긴다. 제어 루프는 마지막 판단을 들고 계속 돈다."],
    ["3","출력 흔들림","관측 분해능","센서 노이즈를 그대로 따라가면 LED 가 떤다. 이력으로 붙잡는다."]]);
  noteBox(s,5.42,[{text:"학습자가 “이거 앞에서 한 얘기 아닌가요” 라고 물으면 — ",options:{color:"333333"}},
    {text:"맞습니다. 그게 핵심입니다.",options:{bold:true,color:INK}}]);
  s._foot(); }

// 2-5 뼈대 2
{ const s=m3("2-5","뼈대 ② 출력은 검증을 통과해야 한다","모델이 지어낸 것이 하드웨어에 닿지 않도록");
  grayBar(s,1.52,"세 관문 (Three Gates)");
  numCols(s,2.28,[
    ["1","스키마 강제","Decoding-time","디코딩 단계에서 JSON 구조를 강제한다. 사후 파싱은 반드시 깨진다."],
    ["2","계약 검증","Host-side","선언에 없는 장치·명령·범위 밖 값을 거부한다."],
    ["3","펌웨어 한계","MCU","같은 범위를 MCU 가 다시 검사한다. 우회 경로가 없다."]]);
  noteBox(s,5.42,[{text:"중복이 아닌 이유 — ",options:{color:MUTED}},
    {text:"우회 경로가 서로 다르다.",options:{bold:true,color:INK}},
    {text:"  선언은 안내문이고 펌웨어는 잠긴 문이다.",options:{color:"333333"}}]);
  s._foot(); }

// 계약 분기 실패 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.2 · 3.2.1",
    crumbTitle:"AI 판단 도입 — 실패 사례: 계약이 갈라졌을 때",
    badge:"실패 사례", c:RED, bg:"F7E4E1", badgeColor:RED,
    phase:"PHASE 3 · Decide", step:"STEP 3.2 AI 판단",
    chips:[["거부율","80%"],["화면상","30fps 정상"]],
    title:"아무것도 고장나 보이지 않았다",
    sub:"모델도 서버도 정상이었다. 계약을 두 곳에 적은 것이 원인이었다",
    banner:"폴백이 실패를 완전히 가렸습니다", bannerRight:"Phase 3 · Step 3.2",
    note:"※ 발견 경로: policy.stats 의 failed 카운터. 화면만 보고는 알 수 없었음",
    deliv:"산출물 3.2.1 · P-AI 방법론 5-Phase"});
  const rows=[["스키마가 말한 것","colour 는 선택 항목","모델은 이를 따랐다"],
    ["검증기가 말한 것","on/blink 에는 colour 필수","모델 출력을 거부했다"],
    ["결과","5회 중 4회 거부","그런데 LED 는 계속 켜져 있었다"]];
  m4Table(s,0.82,2.66,11.7,[["구분",2.6],["내용",4.4],["결과",4.5]],rows,RED,0.62);
  R(s,{x:0.82,y:5.0,w:5.72,h:1.3,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"왜 안 보였나",{x:1.06,y:5.12,w:5.2,h:0.3,fontSize:13,bold:true,color:RED});
  T(s,"폴백 정책이 30fps 를 유지했다. 시연 화면은 완벽히 정상이었고,\n통계를 열어보기 전까지 아무도 몰랐다.",
    {x:1.06,y:5.46,w:5.2,h:0.7,fontSize:11.5,color:"444444",lineSpacing:17});
  R(s,{x:6.8,y:5.0,w:5.72,h:1.3,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"어떻게 고쳤나",{x:7.04,y:5.12,w:5.2,h:0.3,fontSize:13,bold:true,color:P5});
  T(s,"계약을 한 곳에만 적는다. 스키마와 검증기가 같은 선언에서\n파생되면 갈라질 대상이 없다. (뼈대 ③)",
    {x:7.04,y:5.46,w:5.2,h:0.7,fontSize:11.5,color:"444444",lineSpacing:17}); }

// 2-6 모르겠다
{ const s=m3("2-6","“모르겠다” 를 합법으로 만든다","출구를 주지 않으면 모델은 반드시 지어낸다");
  grayBar(s,1.52,"none 의 설계 (Designing an Exit)");
  const items=[["없을 때","모델은 어두운 장면에서도 색을 지어낸다. 확신에 찬 오답이 나온다.","FBF4F3","EFD6D2",RED],
    ["있을 때","“The image is too dark, blurred or ambiguous” — 실제 응답이다.","F4F7F4","D5E3D7",P5]];
  items.forEach(([t,d,bg,ln,c],i)=>{ const x=0.62+i*6.15;
    R(s,{x,y:2.3,w:5.94,h:1.5,fill:{color:bg},line:{color:ln,width:1}});
    T(s,t,{x:x+0.3,y:2.46,w:5.3,h:0.36,fontSize:15,bold:true,color:c});
    T(s,d,{x:x+0.3,y:2.88,w:5.3,h:0.8,fontSize:12.5,color:"444444",lineSpacing:18}); });
  R(s,{x:0.62,y:4.06,w:12.09,h:1.16,fill:{color:"F7F7F7"},line:{color:RULE,width:1}});
  T(s,"none ≠ off",{x:0.9,y:4.18,w:4.0,h:0.34,fontSize:15,bold:true,color:INK});
  T(s,"“판단할 수 없다” 와 “끄라” 는 다른 말이다. none 은 직전 명령을 유지한다 — 조명이 한 프레임 깜빡였다고 경고등이 꺼지면 안 된다.",
    {x:0.9,y:4.56,w:11.5,h:0.52,fontSize:12.5,color:"444444"});
  noteBox(s,5.42,[{text:"모터라면 더 나쁘다 — ",options:{color:"333333"}},
    {text:"판단 불가마다 정지하면 기구가 덜컥거린다.",options:{bold:true,color:INK}}]);
  s._foot(); }

// 2-7 뼈대 3
{ const s=m3("2-7","뼈대 ③ 역량을 데이터로 선언한다","“프로그램 불필요” 가 성립하는 지점");
  grayBar(s,1.52,"하나의 선언에서 셋이 파생된다 (One Declaration, Three Outputs)");
  R(s,{x:0.62,y:2.3,w:3.3,h:1.9,fill:{color:P4},line:{color:P4,width:1}});
  T(s,"장치 선언",{x:0.62,y:2.5,w:3.3,h:0.4,fontSize:17,bold:true,color:"FFFFFF",align:"center"});
  T(s,"capabilities/*.json",{x:0.62,y:2.9,w:3.3,h:0.32,fontSize:11.5,color:"FBEAD2",align:"center"});
  T(s,"id · kind · transport\ncommands · args · wire",
    {x:0.62,y:3.3,w:3.3,h:0.74,fontSize:11.5,color:"FFFFFF",align:"center",lineSpacing:17});
  T(s,"→",{x:4.0,y:3.0,w:0.5,h:0.5,fontSize:22,color:"AAAAAA",align:"center"});
  [["모델 도구 스키마","모델이 고를 수 있는 선택지"],["출력 검증기","계약 밖 호출을 거부"],
   ["전송 문자열","wire 템플릿으로 직접 생성"]].forEach(([t,d],i)=>{
    const y=2.3+i*0.66;
    R(s,{x:4.6,y,w:8.11,h:0.58,fill:{color:P4BG},line:{color:"E8D5B5",width:1}});
    T(s,t,{x:4.84,y,w:3.0,h:0.58,fontSize:13,bold:true,color:P4,valign:"middle"});
    T(s,d,{x:7.9,y,w:4.6,h:0.58,fontSize:12,color:"555555",valign:"middle"}); });
  noteBox(s,4.4,[{text:"wire 템플릿이 핵심이다 — ",options:{color:"333333"}},
    {text:"이것이 없으면 장치마다 파이썬 어댑터가 필요하고, “선언만 추가” 가 거짓이 된다.",options:{bold:true,color:INK}}],0.72);
  grayBar(s,5.34,"합격 판정 (Acceptance Test)");
  T(s,"새 액추에이터를 추가하는 데 코드를 한 줄도 쓰지 않는다",
    {x:0.62,y:5.84,w:12.09,h:0.5,fontSize:17,bold:true,color:INK,align:"center"});
  s._foot(); }

// 계약 증명 (M4)
{ const s=m4({crumb:"Phase 4 · Step 4.1 · 4.1.1",
    crumbTitle:"역량 계약 — 산출물 예시: 장치 선언서와 그 증명",
    badge:"산출물 예시", c:P4, bg:P4BG,
    phase:"PHASE 4 · Actuate", step:"STEP 4.1 역량 계약",
    chips:[["장치","1 → 2"],["스키마","3 → 5"],["코드","0줄"]],
    title:"코드 0줄로 장치를 추가했다",
    sub:"선언 파일 하나를 놓은 것 외에 파이썬을 한 글자도 바꾸지 않았다",
    banner:"장치 추가에 파이썬을 한 줄도 쓰지 않았습니다", bannerRight:"Phase 4 · Step 4.1",
    note:"※ 검증 방법: 추가 전후 파이썬 파일 전체의 md5 해시를 비교",
    deliv:"산출물 4.1.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["시점",3.4],["파이썬 md5",3.6],["모델이 보는 스키마",4.7]],
    [["servo_pointer.json 추가 전","51a8999616dcf698…","옵션 3개 / 장치 1개"],
     ["선언 파일 1개 추가","(파이썬 수정 없음)","—"],
     ["추가 후","51a8999616dcf698…","옵션 5개 / 장치 2개"]],P4,0.62);
  R(s,{x:0.82,y:4.86,w:11.7,h:1.44,fill:{color:"FDF8F0"},line:{color:"E8D5B5",width:1}});
  T(s,"계약이 막는 것들",{x:1.08,y:4.98,w:4.0,h:0.32,fontSize:13,bold:true,color:P4});
  [["laser.fire","없는 장치"],["servo.spin","없는 명령"],["angle = 999","범위 초과"],["torque = 9000","없는 인자"]]
    .forEach(([cmd,why],i)=>{ const x=1.08+i*2.9;
      T(s,cmd,{x,y:5.36,w:2.7,h:0.3,fontSize:12,bold:true,color:INK});
      T(s,"✕  "+why,{x,y:5.66,w:2.7,h:0.3,fontSize:11.5,color:RED}); });
  T(s,"환각이 하드웨어에 닿지 않는다. 그리고 범위는 펌웨어가 한 번 더 막는다.",
    {x:1.08,y:5.98,w:11.1,h:0.3,fontSize:12,color:"555555"}); }

// 2-8 쓸 문제/쓰지 말 문제
{ const s=m3("2-8","AI 를 쓸 문제 / 쓰지 말 문제","문제의 성질이 도구를 정한다");
  const rows=[["색 판별","보통","좋음","VLM",P3],
    ["위치 판단","9/9 · 7 ms","3/9 · 2.5초","규칙 (330배 빠름)",P5],
    ["“정리되어 있나”","불가능","가능","VLM",P3]];
  R(s,{x:0.62,y:1.62,w:3.5,h:0.56,fill:{color:"F2F2F2"}});
  R(s,{x:4.12,y:1.62,w:2.9,h:0.56,fill:{color:"F2F2F2"}});
  R(s,{x:7.02,y:1.62,w:2.9,h:0.56,fill:{color:"F2F2F2"}});
  R(s,{x:9.92,y:1.62,w:2.79,h:0.56,fill:{color:BAR}});
  [["과제",0.62,3.5,INK],["규칙 기반",4.12,2.9,INK],["VLM",7.02,2.9,INK],["승자",9.92,2.79,"FFFFFF"]]
    .forEach(([l,x,w,c])=>T(s,l,{x,y:1.62,w,h:0.56,fontSize:13,bold:true,color:c,align:"center",valign:"middle"}));
  rows.forEach(([q,a,b,win,c],i)=>{ const y=2.18+i*0.78;
    R(s,{x:0.62,y,w:12.09,h:0.012,fill:{color:RULE}});
    T(s,q,{x:0.62,y,w:3.5,h:0.78,fontSize:13.5,bold:true,color:INK,align:"center",valign:"middle"});
    T(s,a,{x:4.12,y,w:2.9,h:0.78,fontSize:13,color:"555555",align:"center",valign:"middle"});
    T(s,b,{x:7.02,y,w:2.9,h:0.78,fontSize:13,color:"555555",align:"center",valign:"middle"});
    T(s,win,{x:9.92,y,w:2.79,h:0.78,fontSize:13,bold:true,color:c,align:"center",valign:"middle"}); });
  R(s,{x:0.62,y:4.52,w:12.09,h:0.012,fill:{color:RULE}});
  noteBox(s,4.86,[{text:"차이는 문제의 성질에 있다 — ",options:{color:"333333"}},
    {text:"색은 의미 해석이고, 위치는 산술이다.",options:{bold:true,color:INK}}]);
  blackBanner(s,5.78,"산술을 모델에게 시키지 마십시오");
  s._foot(); }

// 위치 A/B (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.2 · 3.2.2",
    crumbTitle:"AI 판단 도입 — 산출물 예시: 규칙 / AI A·B 비교표",
    badge:"A/B 비교", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.2 AI 판단",
    chips:[["규칙","9/9 · 7ms"],["VLM","3/9 · 2.5초"],["배율","330배"]],
    title:"위치 판단은 규칙이 완승했다",
    sub:"정답이 확실한 합성 이미지 9개. 같은 이미지를 양쪽에 준다",
    banner:"3/9 만 보면 “부정확”, 답변을 보면 “안 보고 있음”", bannerRight:"Phase 3 · Step 3.2",
    note:"※ 정답은 사각형을 그려 넣은 좌표. 채점에 논란의 여지가 없도록 합성 이미지를 사용",
    deliv:"산출물 3.2.2 · P-AI 방법론 5-Phase"});
  const data=[[0.10,"left","left","left"],[0.30,"left","left","left"],[0.50,"centre","centre","left"],
    [0.70,"right","right","left"],[0.90,"right","right","left"]];
  m4Table(s,0.82,2.66,6.6,[["정답 x",1.5],["정답",1.7],["규칙",1.7],["VLM",1.6]],
    data.map(r=>[r[0].toFixed(2),r[1],r[2],r[3]]),P3,0.52);
  R(s,{x:7.8,y:2.66,w:4.72,h:1.62,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
  T(s,"실패의 모양",{x:8.04,y:2.8,w:4.2,h:0.32,fontSize:13,bold:true,color:P3});
  T(s,"VLM 이 9개 전부 left 로 답했다.\n맞은 3개는 우연히 왼쪽이었을 뿐이다.\n위치를 조금 틀리는 것이 아니라,\n위치를 보고 있지 않다.",
    {x:8.04,y:3.16,w:4.2,h:1.0,fontSize:11.5,color:"444444",lineSpacing:17});
  R(s,{x:7.8,y:4.44,w:4.72,h:1.86,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"이미지를 키우면 나아지나",{x:8.04,y:4.58,w:4.2,h:0.32,fontSize:13,bold:true,color:RED});
  [["768×432","2/5 · 2.3초"],["1024×576","3/5 · 5.6초"],["1280×720","3/5 · 8.1초"]].forEach(([a,b],i)=>{
    T(s,a,{x:8.04,y:4.94+i*0.34,w:2.0,h:0.3,fontSize:11.5,color:"444444"});
    T(s,b,{x:10.1,y:4.94+i*0.34,w:2.2,h:0.3,fontSize:11.5,bold:true,color:INK}); });
  T(s,"하나 더 맞히는 대가로 지연 3.5배",{x:8.04,y:5.98,w:4.2,h:0.28,fontSize:11,bold:true,color:RED});
  R(s,{x:0.82,y:5.3,w:6.6,h:1.0,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
  T(s,"정확도 숫자 하나로 모델을 판단하지 마십시오",{x:1.06,y:5.42,w:6.1,h:0.3,fontSize:12.5,bold:true,color:P3});
  T(s,"답변 목록을 보지 않으면 “좀 부정확하다” 로 읽힌다.\n무엇을 못 하는지는 분포에서 드러난다.",
    {x:1.06,y:5.74,w:6.1,h:0.5,fontSize:11.5,color:"444444",lineSpacing:16}); }

// 2-9 요약
{ const s=m3("2-9","2부 요약","뼈대 셋과 원칙 하나");
  grayBar(s,1.52,"요약 (Summary)");
  numCols(s,2.28,[
    ["①","느린 / 빠른 분리","Separation","판단은 비동기로, 타이밍은 MCU 가. 97배 차이를 구조로 흡수한다."],
    ["②","출력은 검증을 통과","Validation","스키마 · 계약 · 펌웨어. 우회 경로가 달라 중복이 아니다."],
    ["③","역량을 데이터로","Declaration","하나의 선언에서 셋이 파생된다. 갈라질 대상이 없다."]]);
  blackBanner(s,5.42,"그리고 — 산술을 모델에게 시키지 마십시오");
  s._foot(); }
};
