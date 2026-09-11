# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

This project is at the pre-code stage. The entire tree is:

```
docs/research.md   # placeholder: "100% Physical AI 로만 구성된 기술 리서치 내용 삽입"
```

There is no source code, build system, test suite, dependency manifest, or git repository yet.
Do not describe build/lint/test commands or architecture here until they actually exist —
update this file in the same change that introduces them.

## Intent

Working directory name and the research placeholder indicate the goal: an LED-blinking project
driven by AI, framed as Physical AI (AI controlling physical hardware). The host is an NVIDIA
Jetson (Linux 5.15.x-tegra, aarch64), so GPIO/hardware work should target Jetson conventions
rather than Raspberry Pi ones.

The `docs/research.md` placeholder is written in Korean; the user communicates in Korean.
