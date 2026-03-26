# ✿ KDC — Kawaii Distro Chooser ✿

> **(ﾉ◕ヮ◕)ﾉ\*:･ﾟ✧ Let me find your perfect Linux distro~ ✧ﾟ･:\*ヽ(◕ヮ◕ヽ)**

KDC is a kawaii-themed Linux distro recommender that **scans your hardware** and suggests the best Linux distribution for your machine — complete with animated catgirls, a rainbow sweep reveal, and floating sparkle particles.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-ff69b4?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Linux-9b59b6?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

- 🐱 **Auto hardware detection** — reads your CPU, RAM, GPU, disk, and BIOS type
- 🌐 **Live data** — scrapes [DistroWatch](https://distrowatch.com) and Reddit for up-to-date recommendations
- 🎨 **Kawaii GUI** — custom-painted animated catgirls, rainbow sweep transition, and sparkle particles
- 🐧 **Smart scoring** — weighs RAM, GPU vendor, CPU generation, and core count to pick the best fit
- 🔁 **Scan again** — re-run any time without restarting the app

---

## 📸 Screenshots

| Start Screen | Loading | Result |
|:---:|:---:|:---:|
| *(scan button + sparkles)* | *(neko oracle spinner)* | *(catgirls celebrate your distro)* |

---

## 🛠️ Requirements

### System
- **Linux** (uses `/proc/cpuinfo`, `/proc/meminfo`, `/sys/firmware/efi`, `lspci`)
- `bash` (pre-installed on all Linux distros)
- `python3` ≥ 3.10
- `pciutils` — for GPU detection (`lspci`)
  ```bash
  # Debian/Ubuntu
  sudo apt install pciutils

  # Arch/Manjaro
  sudo pacman -S pciutils

  # Fedora
  sudo dnf install pciutils
  ```

### Python packages
```bash
pip install PyQt6 requests beautifulsoup4
```

Or install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 🚀 Installation & Running

```bash
# 1. Clone the repo
git clone https://github.com/AmoiiKane/KDC-KawaiiDistroChooser.git
cd KDC-KawaiiDistroChooser

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Make the detection script executable
chmod +x detect_specs.sh

# 4. Run!
python main.py
```

> **Note:** An internet connection is needed to scrape DistroWatch and Reddit for recommendations. The app works offline too — it falls back to a built-in scoring system.

---

## 📁 Project Structure

```
KDC-KawaiiDistroChooser/
├── main.py            # Entry point
├── gui.py             # PyQt6 GUI — screens, animations, catgirls
├── scraper.py         # DistroWatch + Reddit scraper & scoring engine
├── detect_specs.sh    # Bash hardware detection script (outputs JSON)
├── bg_start.jpg       # Background image for start screen
├── bg_loading.jpg     # Background image for loading screen
└── requirements.txt   # Python dependencies
```

---

## 🧠 How It Works

1. **`detect_specs.sh`** reads `/proc` and `lspci` to collect hardware info and outputs it as JSON.
2. **`scraper.py`** takes that JSON, scores distros based on your specs (RAM, GPU vendor, CPU age, disk size), then boosts scores using live Reddit mentions for your hardware tier.
3. **`gui.py`** runs the scan in a background thread, animates the loading screen, then does a rainbow sweep reveal of your recommended distro — with dancing catgirls.

---

## 🐧 Supported Distros

KDC can recommend any of the following:

| Distro | Best for |
|--------|----------|
| Ubuntu | General use, NVIDIA GPUs |
| Fedora | Modern hardware, AMD GPUs |
| Arch Linux | Power users, cutting-edge |
| Linux Mint | Low-to-mid RAM, beginners |
| Manjaro | Mid-range, user-friendly Arch |
| Pop!_OS | NVIDIA GPUs, developers |
| Debian | Stability, very low RAM |
| Zorin OS | Windows switchers |
| EndeavourOS | Modern AMD, Arch-based |
| Lubuntu | Very old or low-RAM machines |
| Void Linux | Minimal, old hardware |
| openSUSE | Enterprise-style stability |

---

## ⚙️ Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt6` | GUI framework |
| `requests` | HTTP requests for scraping |
| `beautifulsoup4` | HTML parsing (DistroWatch) |

---

## 🤝 Contributing

Pull requests are welcome! Some ideas for contributions:

- Add more distros to the scoring engine
- Improve the catgirl art (more outfits, expressions!)
- Add a manual spec override mode (for users who want to check compatibility before switching)
- Package as a `.AppImage` or AUR package

---

## 📄 License

MIT — do whatever you want with it, just keep it kawaii~ (ﾉ◕ヮ◕)ﾉ

---

<p align="center">Made with 💖 by <a href="https://github.com/AmoiiKane">AmoiiKane</a></p>
