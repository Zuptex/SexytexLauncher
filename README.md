# SexytexBDO Launcher

A GUI launcher for **Black Desert Online** that switches NVIDIA GPU profiles via [nvidiaProfileInspector](https://github.com/Orbmu2k/nvidiaProfileInspector) before launching the game.

![SexytexBDO Launcher](.github/screenshot.png)

## Features

- 🎮 One-click launch BDO with the right GPU profile applied  
- ⚡ Switch between POTATO (max FPS) and NORMAL (balanced) profiles, or add your own  
- 🖥️ Choose Steam or Pearl Abyss launcher  
- 🔧 Custom CPU affinity mask (hex)  
- 📦 Add unlimited custom `.nip` profiles  
- 🔔 Auto-checks GitHub Releases for updates on launch  


**The exe must stay in the same folder as `nvidiaProfileInspector/` and `profiles/`.**

---

## Installation

1. Download the latest zip from [Releases](../../releases/latest)
2. Extract anywhere (e.g. `C:\SexytexBdoLauncher\`)
3. Run `SexytexBdoLauncher.exe` as Administrator (required for NPI to write GPU settings)

---

## Building from Source

Requirements: Python 3.10+

```bat
git clone https://github.com/Zuptex/SexytexLauncher
cd SexytexBdoLauncher
build.bat
```

Output: `dist\SexytexBdoLauncher.exe`

---

## CPU Affinity

The affinity field accepts a **hex bitmask**. Examples:

| Value  | Cores used          |
|--------|---------------------|
| `5550` | Default (9800X3D tuned) |
| `FFFF` | All cores           |
| `0`    | No affinity (OS decides) |

Use [this calculator](https://bitsum.com/tools/cpu-affinity-calculator/) to build your own mask.

---

## Adding Custom Profiles

In the launcher, click **+ ADD PROFILE**, give it a name, and browse to any `.nip` file. The file is copied into the `profiles/` folder automatically.
