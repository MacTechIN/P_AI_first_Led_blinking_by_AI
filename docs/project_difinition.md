프로젝트 정의 

정의 : Physical AI 기반 잡기 

사용 환경 : JetsonOrin Nano Super(8G) , Arduino Uno, ESP32 wroom 

Actuator : LEDs, Servo Motors, Steping motor , Input Sensors(Light, Smoke, Sound etc) 



Physical AI 기초 이론 확립 및 스터디를 목적으로 상기 환경과 재료를 사용하여 실제 화면에서 구현이 아닌 실제 생활에 나타나는 AI 가 사물을 스스로 제어하고 이용하도록 하기위한 기본 Frame work 개발 하기 위함.

Nvidia 에 모든 가용한 라이브러리 와 SDK, API , Local LLM을 이용해서 독립적인 환경 구축 



1. LED 컨트롤 - Jetson Orin 에 로컬 ai 판단 (Open AI 나 기타 외부 무료 AI 사용 가능) 하에 Arduino Serial 통신이나 SPI 통신을 이용해서 LED를 스스로 컨트롤(프로그램 불필요) 하도록 만든다. 이때 입력은 Orin Nano에 카메라 를 보고 카메라 에 이미지 분석후 led 등을 제어 하도록 한다(동일 색 표시, 방향 표시, ON/OFF 표시, 등 이 부분은 알아서 판단) 
2. 엑추에어터 활용 어떤 행동을 표시 하기 엑추에이터 구성은 사용자가 입력 함.



먼저 1번 부터 시작 

다음 프로젝트 내용 변경은 추후 검토 추가 

