# https://github.com/TomusNicolas/DeskBuddy

# DeskBuddy

## Descriere
DeskBuddy este o aplicatie de monitorizare „desk companion” pentru Raspberry Pi 5 pentru formarea obiceiurilor bune precum luarea de pauze, hidratarea si atentionarea pentru distrageri folosind un modul Hailo-8

## Cerinte
- Raspberry Pi 5 cu Raspberry Pi OS (64-bit)  
- Card microSD (min. 16 GB)  
- Conexiune la internet si VNC activat  
- Python 3.11 (+ optional Conda)  
- Camera compatibila cu picamera2  
- Fisier model `yolov11s_h8l.hef`

## Instalare

```bash
# 1. Pregatire OS pe microSD
#    - Scrie Raspberry Pi OS (64-bit) cu Raspberry Pi Imager

# 2. Boot si VNC
#    - Conecteaza Pi la retea, activeaza VNC in `sudo raspi-config`

# 3. Drivere Hailo & SDK
sudo ./install_hailo_drivers.sh
sudo ./install_hailo_sdk.sh
sudo reboot

# 4. Clone repo si intra in director
git clone https://github.com/TomusNicolas/DeskBuddy
cd DeskBuddy

# 5. Configurare Python
# (optional cu Conda)
conda create -n deskbuddy python=3.11
conda activate deskbuddy

# 6. Ruleaza aplicatia
python main.py
