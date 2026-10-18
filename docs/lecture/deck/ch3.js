module.exports = function(H){
const { pres, F, INK, MUTED, RULE, BAR, RED, P1,P2,P3,P4,P5,P1BG,P2BG,P3BG,P4BG,P5BG,
  T,R,RR,EL,m2,m3,grayBar,numCols,noteBox,blackBanner,m4,m4Table,m4Cards } = H;

m2(3,"P-AI 실습","Hands-on · Colour Control with a Local VLM");

// 실습 개요 (M4)
{ const s=m4({crumb:"Phase 2 · Step 2.1",
    crumbTitle:"인지 구축 — 실습 개요: 카메라가 본 색을 LED 가 재현한다",
    badge:"실습", c:P2, bg:P2BG,
    phase:"PHASE 2 · Perceive", step:"STEP 2.1 센서 연동",
    chips:[["부품","5종"],["소요","60분"],["난이도","중"]],
    title:"오늘 만들 것",
    sub:"색지를 카메라 앞에 들면 LED 가 같은 색으로 켜진다",
    banner:"다섯 단계가 모두 이 보드 안에서 끝납니다", bannerRight:"Phase 2 · Step 2.1",
    note:"※ 인터넷 연결 없이 동작합니다. 영상도 판단 결과도 보드 밖으로 나가지 않습니다",
    deliv:"실습 개요 · P-AI 방법론 5-Phase"});
  const steps=[["LED","빛을 낸다","~1 ms",P4],["카메라","장면을 담는다","30 ms",P2],
    ["로컬 VLM","색을 읽는다","3,306 ms",P3],["계약","명령을 검사한다","<1 ms",P4],
    ["LED","다시 켜진다","~5 ms",P4]];
  steps.forEach(([t,d,ms,c],i)=>{ const x=0.82+i*2.4;
    RR(s,{x,y:2.9,w:2.1,h:1.5,rectRadius:0.05,fill:{color:"FCFCFC"},line:{color:"E2E2E2",width:1}});
    R(s,{x,y:2.9,w:2.1,h:0.06,fill:{color:c}});
    T(s,t,{x:x+0.16,y:3.1,w:1.8,h:0.36,fontSize:14,bold:true,color:INK,align:"center"});
    T(s,d,{x:x+0.1,y:3.46,w:1.9,h:0.34,fontSize:11.5,color:"555555",align:"center"});
    T(s,ms,{x:x+0.1,y:3.92,w:1.9,h:0.34,fontSize:13,bold:true,color:c,align:"center"});
    if(i<4) T(s,"→",{x:x+2.1,y:3.4,w:0.3,h:0.4,fontSize:16,color:"AAAAAA",align:"center"}); });
  R(s,{x:0.82,y:4.74,w:11.7,h:1.56,fill:{color:"F6F9FC"},line:{color:"D8E4EF",width:1}});
  T(s,"실습에서 확인할 것",{x:1.08,y:4.88,w:5.0,h:0.32,fontSize:13,bold:true,color:P2});
  [["① 색은 어떻게 표현하는가","색상환의 각도 하나. 빨강은 두 번 나온다"],
   ["② AI 는 얼마나 맞히는가","12색 중 정확 6, 한 칸 이내 12"],
   ["③ 무엇이 측정을 망치는가","자동보정이 두 방향으로 방해한다"]].forEach(([t,d],i)=>{
    const x=1.08+i*3.85;
    T(s,t,{x,y:5.3,w:3.6,h:0.34,fontSize:12.5,bold:true,color:INK});
    T(s,d,{x,y:5.64,w:3.6,h:0.5,fontSize:11.5,color:"555555",lineSpacing:16}); }); }

// 부품 함정 (M4)
{ const s=m4({crumb:"Phase 2 · Step 2.1 · 2.1.1",
    crumbTitle:"센서 연동 — 점검표: 부품 선택에서 실제로 막힌 것",
    badge:"실패 사례", c:RED, bg:"F7E4E1", badgeColor:RED,
    phase:"PHASE 2 · Perceive", step:"STEP 2.1 센서 연동",
    chips:[["함정","4종"],["손실","3일"]],
    title:"이 네 가지를 먼저 확인하십시오",
    sub:"전부 본 커리큘럼 제작 중에 실제로 걸려든 것들이다",
    banner:"이 슬라이드가 실습 시간을 절반으로 줄입니다", bannerRight:"Phase 2 · Step 2.1",
    note:"※ 부품을 주문하기 전에 확인하면 가장 좋습니다",
    deliv:"산출물 2.1.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["함정",3.0],["증상",4.6],["확인 방법",4.1]],
    [["Camera Module 3 (IMX708)","JetPack 미지원. 그런데 /dev/video0 은 생긴다","레지스터 0x0016 직독 → 0x0708"],
     ["15핀 CSI 케이블","꽂히는데 접점이 닿지 않는다 (Orin 은 22핀)","케이블 끝 금속 접점을 센다"],
     ["공통 애노드 RGB LED","RGB 255 255 255 를 보내면 꺼진다","흰색 명령에 소등되면 공통 애노드"],
     ["공통 저항 1개","노랑이 빨강으로, 청록이 초록으로 나온다","빨강을 줄여 초록이 드러나면 확정"]],RED,0.62);
  R(s,{x:0.82,y:5.3,w:11.7,h:1.0,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"가장 위험한 것은 첫 번째입니다",{x:1.08,y:5.42,w:5.5,h:0.3,fontSize:12.5,bold:true,color:RED});
  T(s,"IMX708 은 IMX477 과 i2c 주소를 공유해서, 오버레이를 올리면 장치 노드가 생기고 캡처까지 성공합니다. 그런데 모든 픽셀이 같은 값입니다.",
    {x:1.08,y:5.76,w:11.1,h:0.44,fontSize:12,color:"444444"}); }

// 센서 식별서 (M4)
{ const s=m4({crumb:"Phase 2 · Step 2.1 · 2.1.2",
    crumbTitle:"센서 연동 — 산출물 예시: 센서 식별서와 건전성 검사 기준",
    badge:"산출물 예시", c:P2, bg:P2BG,
    phase:"PHASE 2 · Perceive", step:"STEP 2.1 센서 연동",
    chips:[["판독","레지스터 0x0016"],["검사","std ≥ 1.0"]],
    title:"장치 노드는 드라이버가 만든다",
    sub:"센서가 만드는 것이 아니다. 그래서 칩에게 직접 물어본다",
    banner:"존재 · 바인딩 · 캡처 성공은 모두 증거가 아닙니다", bannerRight:"Phase 2 · Step 2.1",
    note:"※ 센서는 INCK 클럭이 공급될 때만 i2c 에 응답합니다. 스트리밍 중에 읽어야 합니다",
    deliv:"산출물 2.1.2 · P-AI 방법론 5-Phase"});
  R(s,{x:0.82,y:2.66,w:5.72,h:0.42,fill:{color:P2}});
  T(s,"센서 식별 — 칩 ID 판독표",{x:0.96,y:2.66,w:5.5,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"});
  [["0x02 0x19","IMX219","지원 · 주소 0x10"],["0x04 0x77","IMX477","지원 · 주소 0x1a"],
   ["0x07 0x08","IMX708","미지원 · 주소 0x1a"]].forEach(([v,n,st],i)=>{ const y=3.08+i*0.52;
    T(s,v,{x:0.96,y,w:1.7,h:0.52,fontSize:12,color:"444444",valign:"middle"});
    T(s,n,{x:2.76,y,w:1.5,h:0.52,fontSize:12,bold:true,color:INK,valign:"middle"});
    T(s,st,{x:4.36,y,w:2.1,h:0.52,fontSize:11.5,color:i===2?RED:P5,valign:"middle"});
    R(s,{x:0.82,y:y+0.5,w:5.72,h:0.012,fill:{color:"EAEAEA"}}); });
  R(s,{x:0.82,y:4.8,w:5.72,h:1.5,fill:{color:"F6F9FC"},line:{color:"D8E4EF",width:1}});
  T(s,"건전성 검사 기준",{x:1.06,y:4.92,w:5.2,h:0.3,fontSize:13,bold:true,color:P2});
  T(s,"① 모든 픽셀이 같은 값이면 거부\n② 표준편차 1.0 미만이면 거부\n③ 렌즈 캡을 씌운 어두운 장면은 통과해야 한다",
    {x:1.06,y:5.26,w:5.2,h:0.9,fontSize:11.5,color:"444444",lineSpacing:18});
  R(s,{x:6.8,y:2.66,w:5.72,h:1.92,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"고장난 카메라가 통과시킨 검사들",{x:7.04,y:2.8,w:5.2,h:0.32,fontSize:13,bold:true,color:RED});
  [["/dev/video0 존재","✓ 생성됨"],["드라이버 바인딩","✓ bound"],["포맷 조회","✓ 3840×2160"],["프레임 캡처","✓ 성공"]]
    .forEach(([a,b],i)=>{ const y=3.2+i*0.32;
      T(s,a,{x:7.04,y,w:3.2,h:0.3,fontSize:11.5,color:"444444"});
      T(s,b,{x:10.3,y,w:2.0,h:0.3,fontSize:11.5,bold:true,color:"999999"}); });
  R(s,{x:6.8,y:4.8,w:5.72,h:1.5,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"그런데 픽셀을 보니",{x:7.04,y:4.92,w:5.2,h:0.3,fontSize:13,bold:true,color:P5});
  T(s,"min = max = mean = 4100,  std = 0.0",{x:7.04,y:5.26,w:5.2,h:0.34,fontSize:13.5,bold:true,color:RED});
  T(s,"830만 샘플이 전부 같은 값. 사진이 아니었다.",{x:7.04,y:5.62,w:5.2,h:0.34,fontSize:11.5,color:"444444"}); }

// 3-1 질문
{ const s=m3("3-1","질문 — 무지개 색은 어떻게 표현하지?","모델에게 색을 가르치려면 먼저 색을 정의해야 한다");
  R(s,{x:0.62,y:1.8,w:12.09,h:1.5,fill:{color:"F2F2F2"},line:{color:RULE,width:1}});
  T(s,"“무지개 색은 어떻게 표현하지?”",
    {x:0.62,y:1.8,w:12.09,h:1.5,fontSize:32,bold:true,color:INK,align:"center",valign:"middle"});
  grayBar(s,3.6,"가능한 답 — 어느 것이 모델에게 좋은가 (Which Representation)");
  numCols(s,4.36,[
    ["1","RGB 세 값","Three Channels","사람이 읽기 어렵다. 모델에게 “(255,128,0)” 을 고르라고 하면 범위를 벗어난다."],
    ["2","색 이름","Names","어휘가 유한하다. “연두” 와 “초록” 의 경계는 사람도 갈린다."],
    ["3","색상환의 각도","Hue","값 하나. 연속적이고 순환한다. 모델은 이름을, 기계는 각도를 쓴다."]]);
  s._foot(); }

// 3-2 색은 1차원
{ const s=m3("3-2","색은 1차원이다","한 바퀴 도는 숫자 하나");
  grayBar(s,1.52,"색상환 (Hue Wheel) — OpenCV 는 0–179");
  const colors=[[0,"FF0000","빨강"],[15,"FF8000","주황"],[30,"FFFF00","노랑"],[45,"80FF00",""],
    [60,"00FF00","초록"],[75,"00FF80",""],[90,"00FFFF","청록"],[105,"007FFF",""],
    [120,"0000FF","파랑"],[135,"8000FF",""],[150,"FF00FF","자홍"],[165,"FF007F",""]];
  colors.forEach(([h,hex,name],i)=>{ const x=0.62+i*1.0;
    R(s,{x,y:2.3,w:0.92,h:0.92,fill:{color:hex},line:{color:"DDDDDD",width:1}});
    T(s,String(h),{x,y:3.3,w:0.92,h:0.3,fontSize:12,bold:true,color:INK,align:"center"});
    if(name) T(s,name,{x:x-0.1,y:3.6,w:1.12,h:0.3,fontSize:10.5,color:MUTED,align:"center"}); });
  R(s,{x:0.62,y:4.1,w:12.09,h:1.1,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"⚠  0–179 입니다. 360 이 아닙니다.",{x:0.9,y:4.22,w:11.5,h:0.34,fontSize:14,bold:true,color:RED});
  T(s,"OpenCV 는 색상환을 180 단계로 담습니다. 360 을 기대하고 짠 코드는 모든 색을 절반씩 어긋나게 읽습니다.",
    {x:0.9,y:4.58,w:11.5,h:0.4,fontSize:12.5,color:"444444"});
  noteBox(s,5.42,[{text:"변환 사슬 — ",options:{color:MUTED}},
    {text:"“green” → hue 60 → RGB(0,255,0) → “RGB 0 255 0 / LEVEL 90 / ON”",options:{bold:true,color:INK}}]);
  s._foot(); }

// 3-3 빨강은 두 번
{ const s=m3("3-3","빨강은 두 번 나온다","평균을 내면 정확히 청록이 된다");
  grayBar(s,1.52,"순환하는 축의 함정 (The Wraparound Trap)");
  const sw=[[2,"FF0000","hue 2"],[175,"FF007F","hue 175"]];
  sw.forEach(([h,hex,label],i)=>{ const x=1.4+i*2.4;
    R(s,{x,y:2.3,w:1.8,h:1.2,fill:{color:hex},line:{color:"DDDDDD",width:1}});
    T(s,label,{x,y:3.56,w:1.8,h:0.32,fontSize:13,bold:true,color:INK,align:"center"});
    T(s,"둘 다 빨강",{x,y:3.88,w:1.8,h:0.3,fontSize:11.5,color:MUTED,align:"center"}); });
  T(s,"평균",{x:6.3,y:2.72,w:0.9,h:0.4,fontSize:14,bold:true,color:MUTED,align:"center"});
  T(s,"→",{x:6.3,y:3.06,w:0.9,h:0.4,fontSize:22,color:"AAAAAA",align:"center"});
  R(s,{x:7.5,y:2.3,w:1.8,h:1.2,fill:{color:"00FFFF"},line:{color:"DDDDDD",width:1}});
  T(s,"hue 88.5",{x:7.5,y:3.56,w:1.8,h:0.32,fontSize:13,bold:true,color:RED,align:"center"});
  T(s,"청록",{x:7.5,y:3.88,w:1.8,h:0.3,fontSize:11.5,bold:true,color:RED,align:"center"});
  R(s,{x:9.7,y:2.3,w:3.01,h:1.88,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"해법",{x:9.94,y:2.44,w:2.6,h:0.32,fontSize:13,bold:true,color:P5});
  T(s,"평균이 아니라 최빈값을 쓴다.\n히스토그램에서 가장 많이\n나온 각도를 고른다.",
    {x:9.94,y:2.8,w:2.6,h:1.0,fontSize:11.5,color:"444444",lineSpacing:18});
  noteBox(s,4.5,[{text:"(2 + 175) ÷ 2 = 88.5 — ",options:{color:"333333"}},
    {text:"빨강 두 개의 평균이 청록이다.",options:{bold:true,color:INK}},
    {text:"  순환하는 축에서는 산술 평균이 성립하지 않는다.",options:{color:"333333"}}]);
  blackBanner(s,5.42,"순환하는 값에 평균을 쓰지 마십시오");
  s._foot(); }

// 무지개 시연 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.1 · 3.1.1",
    crumbTitle:"규칙 베이스라인 — 시연: 색상환 순환 (AI 없음)",
    badge:"시연", c:P4, bg:P4BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.1 규칙 베이스라인",
    chips:[["주기","8초"],["단계","90"],["AI","사용 안 함"]],
    title:"먼저 AI 없이 돌려본다",
    sub:"./host/rainbow.py --period 8 — 색상환을 한 바퀴 도는 것뿐이다",
    banner:"이건 AI 가 아닙니다. 다음 장에서 AI 를 넣습니다", bannerRight:"Phase 3 · Step 3.1",
    note:"※ 카메라로 광학 검증: 색조 37 → 59 → 73 → 95 → 107 → 7 → 10 (한 바퀴)",
    deliv:"산출물 3.1.1 · P-AI 방법론 5-Phase"});
  const cols=[[0,"FF0000"],[15,"FF8000"],[30,"FFFF00"],[45,"80FF00"],[60,"00FF00"],[75,"00FF80"],
    [90,"00FFFF"],[105,"007FFF"],[120,"0000FF"],[135,"8000FF"],[150,"FF00FF"],[165,"FF007F"]];
  cols.forEach(([h,hex],i)=>{ const x=0.82+i*0.98;
    R(s,{x,y:2.7,w:0.9,h:0.9,fill:{color:hex},line:{color:"DDDDDD",width:1}});
    T(s,String(h),{x,y:3.66,w:0.9,h:0.28,fontSize:10.5,color:MUTED,align:"center"}); });
  R(s,{x:0.82,y:4.18,w:5.72,h:2.12,fill:{color:"FDF8F0"},line:{color:"E8D5B5",width:1}});
  T(s,"왜 이건 호스트가 타이밍을 쥐나",{x:1.06,y:4.32,w:5.2,h:0.32,fontSize:13,bold:true,color:P4});
  T(s,"뼈대 ① 의 의도적 예외다.\n\n① 펌웨어는 색 순환을 모른다. 넣으면 패턴을 바꿀 때마다 재플래싱해야 한다.\n② 페이드는 밀리초 정밀도가 필요 없다. 100ms 점멸을 망치던 지터가 여기선 보이지 않는다.",
    {x:1.06,y:4.68,w:5.2,h:1.5,fontSize:11.5,color:"444444",lineSpacing:17});
  R(s,{x:6.8,y:4.18,w:5.72,h:2.12,fill:{color:"F7F7F7"},line:{color:"DDDDDD",width:1}});
  T(s,"원칙에는 예외가 있다",{x:7.04,y:4.32,w:5.2,h:0.32,fontSize:13,bold:true,color:INK});
  T(s,"그리고 예외를 설명할 수 있어야\n원칙을 이해한 것이다.\n\n“왜 이건 MCU 가 안 하나요” 라는 질문이\n나오면 수업이 잘 된 것이다.",
    {x:7.04,y:4.68,w:5.2,h:1.5,fontSize:11.5,color:"444444",lineSpacing:17}); }

// 모델 선정서 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.2 · 3.2.1",
    crumbTitle:"AI 판단 도입 — 산출물 예시: 모델 선정서",
    badge:"산출물 예시", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.2 AI 판단",
    chips:[["선정","3B"],["여유","2.0 GB"],["속도","2.3배"]],
    title:"3B 가 타협이 아니었다",
    sub:"동일 조건에서 제어 루프와 카메라를 함께 돌리며 측정",
    banner:"더 빠르고, 정확하고, 유일하게 동작했습니다", bannerRight:"Phase 3 · Step 3.2",
    note:"※ 측정 조건: 제어 루프 60스텝 + VLM 추론 6회를 동시 실행",
    deliv:"산출물 3.2.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["항목",3.2],["7B Q4_K_M",4.2],["3B Q4_K_M",4.3]],
    [["가중치","5.15 GB","2.59 GB"],["색 판별","측정 불가 (크래시)","6/6 정확"],
     ["평균 지연","2,200 ~ 2,900 ms","943 ms"],["최저 가용 메모리","302 MB","1,974 MB"],
     ["동시 부하 결과","서버 사망","6/6 성공 · 생존"]],P3,0.56);
  R(s,{x:0.82,y:5.6,w:11.7,h:0.7,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
  T(s,[{text:"이 과제에서 7B 의 추가 용량은 ",options:{color:"444444"}},
       {text:"아무 이득이 없었습니다.",options:{bold:true,color:P3}},
       {text:"  정확도는 같고, 속도는 3B 가 2배 이상 빠르며, 메모리 여유는 6배입니다.",options:{color:"444444"}}],
    {x:1.08,y:5.6,w:11.2,h:0.7,fontSize:12.5,valign:"middle"}); }

// 서버 플래그 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.2 · 3.2.1",
    crumbTitle:"AI 판단 도입 — 점검표: 서버 기동 플래그",
    badge:"점검표", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.2 AI 판단",
    chips:[["플래그","4개"],["전부","필수"]],
    title:"플래그 네 개가 결정적이다",
    sub:"그리고 넷 다 직관과 어긋난다",
    banner:"/health 가 ok 라고 동작하는 게 아닙니다", bannerRight:"Phase 3 · Step 3.2",
    note:"※ 서버는 비전 버퍼 할당에 실패해도 model loaded 를 찍고 포트를 엽니다",
    deliv:"산출물 3.2.1 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,11.7,[["설정",3.4],["없으면 / 틀리면",4.8],["비고",3.5]],
    [["--parallel 1","슬롯 4개 → 첫 요청에서 사망","KV 캐시가 4배"],
     ["이미지 768×432","1280×720 은 batch 초과로 abort","작으면 인식 정확도 저하"],
     ["-c 4096","줄이면 오히려 깨진다","이미지 토큰이 배치에 들어가야 함"],
     ["GUI 끄기","가용 2.3GB → 6.4GB","multi-user.target"]],P3,0.62);
  R(s,{x:0.82,y:5.3,w:11.7,h:1.0,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"컨텍스트를 줄이는 것이 늘 이득은 아닙니다",{x:1.08,y:5.42,w:6.0,h:0.3,fontSize:12.5,bold:true,color:RED});
  T(s,"이미지 토큰이 배치 안에 들어가야 하므로, -c 를 낮추면 GGML_ASSERT 로 중단됩니다. 메모리를 아끼려다 아예 못 돌게 되는 전형적인 경우입니다.",
    {x:1.08,y:5.76,w:11.1,h:0.44,fontSize:12,color:"444444"}); }

// 12색 결과 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.2 · 3.2.2",
    crumbTitle:"AI 판단 도입 — 산출물 예시: 색 인식 정확도 측정",
    badge:"실측 데이터", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.2 AI 판단",
    chips:[["정확","6/12"],["한 칸 이내","12/12"],["평균","3.3초"]],
    title:"VLM 은 색을 얼마나 맞히나",
    sub:"색상환을 12단계로 돌며 매번 물었다. 모델은 명령값을 모르고 사진만 본다",
    banner:"“100% 정확” 이 아니라 “한 칸 안에서 정확” 입니다", bannerRight:"Phase 3 · Step 3.2",
    note:"※ 모델: Qwen2.5-VL-3B Q4_K_M · 이미지 768×432 · 화이트밸런스/노출 고정",
    deliv:"산출물 3.2.2 · P-AI 방법론 5-Phase"});
  const run=[[0,"FF0000","red","red",1],[15,"FF8000","orange","red",0],[30,"FFFF00","yellow","yellow",1],
    [45,"80FF00","yellow","green",0],[60,"00FF00","green","green",1],[75,"00FF80","green","green",1],
    [90,"00FFFF","cyan","green",0],[105,"007FFF","cyan","blue",0],[120,"0000FF","blue","blue",1],
    [135,"8000FF","purple","blue",0],[150,"FF00FF","purple","purple",1],[165,"FF007F","red","red",1]];
  R(s,{x:0.82,y:2.66,w:11.7,h:0.38,fill:{color:P3}});
  [["색조",0.96,1.0],["견본",2.0,1.0],["명령한 색",3.1,2.2],["모델의 답",5.4,2.2],["판정",7.7,1.6]]
    .forEach(([l,x,w])=>T(s,l,{x,y:2.66,w,h:0.38,fontSize:11,bold:true,color:"FFFFFF",valign:"middle"}));
  run.forEach(([h,hex,cmd,said,ok],i)=>{ const y=3.04+i*0.27;
    T(s,String(h),{x:0.96,y,w:1.0,h:0.27,fontSize:10.5,color:"444444",valign:"middle"});
    R(s,{x:2.0,y:y+0.04,w:0.72,h:0.19,fill:{color:hex},line:{color:"DDDDDD",width:1}});
    T(s,cmd,{x:3.1,y,w:2.2,h:0.27,fontSize:10.5,color:INK,valign:"middle"});
    T(s,said,{x:5.4,y,w:2.2,h:0.27,fontSize:10.5,bold:true,color:ok?P5:"C87F0A",valign:"middle"});
    T(s,ok?"정확":"이웃 한 칸",{x:7.7,y,w:1.6,h:0.27,fontSize:10.5,color:ok?P5:"C87F0A",valign:"middle"}); });
  R(s,{x:9.6,y:2.66,w:2.92,h:1.8,fill:{color:"F4F7F4"},line:{color:"D5E3D7",width:1}});
  T(s,"정확히 일치",{x:9.84,y:2.8,w:2.5,h:0.3,fontSize:12,color:"555555"});
  T(s,"6 / 12",{x:9.84,y:3.1,w:2.5,h:0.5,fontSize:30,bold:true,color:P5});
  T(s,"나머지 6개도 전부\n색상환에서 바로\n이웃한 이름이었다.",{x:9.84,y:3.62,w:2.5,h:0.74,fontSize:11,color:"444444",lineSpacing:16});
  R(s,{x:9.6,y:4.6,w:2.92,h:1.7,fill:{color:"FBF4F3"},line:{color:"EFD6D2",width:1}});
  T(s,"지표를 유리하게 고르면",{x:9.84,y:4.74,w:2.5,h:0.3,fontSize:12,bold:true,color:RED});
  T(s,"관용 채점하면 12/12 입니다.\n그러나 그건 틀린 교훈을\n줍니다 — 경계의 이름은\n사람도 갈립니다.",
    {x:9.84,y:5.06,w:2.5,h:1.0,fontSize:11,color:"444444",lineSpacing:16}); }

// 자동노출 두 방향 (M4)
{ const s=m4({crumb:"Phase 2 · Step 2.2 · 2.2.1",
    crumbTitle:"특징 설계 — 핵심 발견: 자동보정이 측정을 망치는 두 방향",
    badge:"실측 데이터", c:P2, bg:P2BG,
    phase:"PHASE 2 · Perceive", step:"STEP 2.2 특징 설계",
    chips:[["상쇄","+0.02"],["증폭","3.2배"]],
    title:"같은 기능이 두 방향으로 망친다",
    sub:"있는 것을 감추고, 없는 것을 보이게 한다",
    banner:"차분 기반 검출에서 노출 고정은 선택이 아니라 전제입니다", bannerRight:"Phase 2 · Step 2.2",
    note:"※ 측정: LED 최대 점등 시 전역 밝기 변화 / 정지 장면에서 LED 전환 시 차분 점수",
    deliv:"산출물 2.2.1 · P-AI 방법론 5-Phase"});
  [["전역 밝기로 LED 를 재면","상쇄","+0.02","LED 를 최대로 켰는데 화면 평균이 움직이지 않는다. 자동노출이 되돌린다.\n→ “카메라가 LED 를 못 본다” 는 틀린 결론에 도달한다.",RED,"FBF4F3","EFD6D2"],
   ["차분으로 움직임을 재면","증폭","3.2배","LED 가 켜지면 자동노출이 화면 전체를 다시 노출한다. 움직인 건 없는데 전 픽셀이 바뀐다.\n→ 구름이 지나가도 경보가 울린다.","C87F0A","FDF8F0","E8D5B5"]]
    .forEach(([t,verdict,val,d,c,bg,ln],i)=>{ const x=0.82+i*5.98;
      R(s,{x,y:2.66,w:5.72,h:3.1,fill:{color:bg},line:{color:ln,width:1}});
      T(s,t,{x:x+0.26,y:2.82,w:5.2,h:0.34,fontSize:13.5,bold:true,color:INK});
      T(s,verdict,{x:x+0.26,y:3.24,w:2.4,h:0.56,fontSize:28,bold:true,color:c});
      T(s,val,{x:x+2.8,y:3.34,w:2.6,h:0.44,fontSize:20,bold:true,color:c,align:"right"});
      T(s,d,{x:x+0.26,y:4.0,w:5.2,h:1.6,fontSize:11.5,color:"444444",lineSpacing:18}); });
  R(s,{x:0.82,y:5.9,w:11.7,h:0.4,fill:{color:"F6F9FC"},line:{color:"D8E4EF",width:1}});
  T(s,[{text:"같은 자동노출이 ",options:{color:"444444"}},
       {text:"모듈 3 에서는 LED 를 지우고, 여기서는 없는 움직임을 만들어냅니다.",options:{bold:true,color:P2}}],
    {x:1.08,y:5.9,w:11.2,h:0.4,fontSize:12,valign:"middle"}); }

// 노이즈 바닥 (M4)
{ const s=m4({crumb:"Phase 2 · Step 2.2 · 2.2.2",
    crumbTitle:"특징 설계 — 산출물 예시: 노이즈 바닥 측정표",
    badge:"산출물 예시", c:P2, bg:P2BG,
    phase:"PHASE 2 · Perceive", step:"STEP 2.2 특징 설계",
    chips:[["노이즈 p95","0.300"],["신호","3.245"],["여유","10.8배"]],
    title:"임계값은 추측하지 않고 잰다",
    sub:"정지 장면의 노이즈를 먼저 재고, 알려진 변화를 재고, 둘을 가르는 값을 고른다",
    banner:"오경보 0% 를 유지하는 가장 낮은 값을 고릅니다", bannerRight:"Phase 2 · Step 2.2",
    note:"※ 알려진 변화로 LED 점등/소등을 사용 — 언제 변했는지 정확히 알기 때문",
    deliv:"산출물 2.2.2 · P-AI 방법론 5-Phase"});
  m4Table(s,0.82,2.66,5.72,[["측정",2.4],["값",3.0]],
    [["정지 노이즈 p95","0.300"],["LED 전환 신호","3.245"],["여유","10.8 배"],["표본","정지 59 · 전환 12"]],P2,0.52);
  R(s,{x:6.8,y:2.66,w:5.72,h:0.42,fill:{color:P2}});
  [["임계값",0.2,1.6],["오경보",1.9,1.4],["검출",3.4,1.3]].forEach(([l,dx,w])=>
    T(s,l,{x:6.8+dx,y:2.66,w,h:0.42,fontSize:11.5,bold:true,color:"FFFFFF",valign:"middle"}));
  [["0.601  (p95×2)","0.0%","100%",true],["0.901  (p95×3)","0.0%","100%",false],
   ["1.501  (p95×5)","0.0%","100%",false]].forEach(([t,fp,tp,sel],i)=>{ const y=3.08+i*0.52;
    if(sel) R(s,{x:6.8,y,w:5.72,h:0.5,fill:{color:"E4F2EA"}});
    T(s,t,{x:7.0,y,w:1.8,h:0.5,fontSize:11.5,bold:sel,color:INK,valign:"middle"});
    T(s,fp,{x:8.7,y,w:1.4,h:0.5,fontSize:11.5,color:"444444",valign:"middle"});
    T(s,tp,{x:10.2,y,w:1.3,h:0.5,fontSize:11.5,color:"444444",valign:"middle"});
    if(sel) T(s,"← 선정",{x:11.4,y,w:1.0,h:0.5,fontSize:10.5,bold:true,color:P5,valign:"middle"});
    R(s,{x:6.8,y:y+0.5,w:5.72,h:0.012,fill:{color:"EAEAEA"}}); });
  R(s,{x:0.82,y:5.0,w:11.7,h:1.3,fill:{color:"F6F9FC"},line:{color:"D8E4EF",width:1}});
  T(s,"왜 가장 낮은 값인가",{x:1.08,y:5.14,w:5.0,h:0.3,fontSize:13,bold:true,color:P2});
  T(s,"셋 다 오경보 0% · 검출 100% 로 완벽합니다. 그렇다면 더 민감한 쪽이 낫습니다 — 임계값이 낮을수록 작은 변화를 잡아냅니다.\n반대로 노이즈 바닥을 재지 않고 추측했다면, 너무 낮게 잡아 오경보가 쏟아지거나 너무 높게 잡아 진짜 변화를 놓쳤을 것입니다.",
    {x:1.08,y:5.48,w:11.1,h:0.72,fontSize:12,color:"444444",lineSpacing:17}); }

// 전송 빈도 (M4)
{ const s=m4({crumb:"Phase 3 · Step 3.3 · 3.3.2",
    crumbTitle:"출력 안정화 — 산출물 예시: 전송 빈도 측정",
    badge:"산출물 예시", c:P3, bg:P3BG,
    phase:"PHASE 3 · Decide", step:"STEP 3.3 출력 안정화",
    chips:[["원본","18회"],["이력 적용","2회"]],
    title:"정지한 장면에서 20스텝 중 18회를 보냈다",
    sub:"센서 노이즈로 색조가 흔들리고, 정책이 그것을 충실히 따라간 결과",
    banner:"판단의 분해능을 관측의 신뢰도에 맞춥니다", bannerRight:"Phase 3 · Step 3.3",
    note:"※ 장면은 완전히 정지 상태. 변화는 전부 센서 노이즈에서 왔습니다",
    deliv:"산출물 3.3.2 · P-AI 방법론 5-Phase"});
  [["원본",18,"20스텝 중 18회","LED 가 미세하게 떨린다",RED],
   ["양자화",11,"20스텝 중 11회","경계 위에서 진동한다","C87F0A"],
   ["이력",2,"20스텝 중 2회","실제 색이 바뀔 때만",P5]].forEach(([t,v,label,d,c],i)=>{
    const y=2.76+i*1.08;
    T(s,t,{x:0.9,y,w:1.6,h:0.5,fontSize:14,bold:true,color:INK,valign:"middle"});
    R(s,{x:2.7,y:y+0.1,w:7.0,h:0.34,fill:{color:"F0F0F0"}});
    R(s,{x:2.7,y:y+0.1,w:7.0*v/18,h:0.34,fill:{color:c}});
    T(s,label,{x:9.9,y,w:2.4,h:0.5,fontSize:12,bold:true,color:INK,valign:"middle"});
    T(s,d,{x:2.7,y:y+0.5,w:7.0,h:0.3,fontSize:11,color:MUTED}); });
  R(s,{x:0.82,y:5.9,w:11.7,h:0.4,fill:{color:"F8F5FB"},line:{color:"E0D3EA",width:1}});
  T(s,[{text:"양자화만으로 부족한 이유 — ",options:{color:"444444"}},
       {text:"값이 스텝 경계 위에서 진동하면 양자화 결과도 함께 진동합니다.",options:{bold:true,color:P3}},
       {text:"  직전에 내보낸 값과 비교하면 고정된 경계가 없어집니다.",options:{color:"444444"}}],
    {x:1.08,y:5.9,w:11.2,h:0.4,fontSize:11.5,valign:"middle"}); }

// 3-4 요약
{ const s=m3("3-4","3부 요약","실습에서 배운 네 가지");
  grayBar(s,1.52,"요약 (Summary)");
  numCols(s,2.28,[
    ["①","색은 각도 하나","Hue","0–179. 빨강은 두 번 나오므로 평균이 아니라 최빈값을 쓴다."],
    ["②","AI 는 한 칸 안에서","6/12 · 12/12","정확 6, 이웃 한 칸 6. 한 칸을 넘어 틀린 적은 없었다."],
    ["③","측정이 결론을 만든다","AE","같은 자동노출이 있는 것을 감추고 없는 것을 만든다."],
    ["④","지표를 고르지 마라","Metric","관용 채점하면 12/12 다. 그러나 틀린 교훈을 준다."]]);
  noteBox(s,5.42,[{text:"다음 장 — ",options:{color:MUTED}},
    {text:"그래서 우리 조직은 무엇부터 해야 하는가.",options:{bold:true,color:INK}}]);
  s._foot(); }
};
