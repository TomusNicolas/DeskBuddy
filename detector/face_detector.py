# face_detector.py
from pathlib import Path
from .hailo_detector import HailoDetector

# Definirea locatiei modelelor si a fisierelor cu etichete
BASE = Path(__file__).parent
MODELS = BASE / "models"

class FaceDetector(HailoDetector):

    def __init__(self):
        
        super().__init__(
            model_path=MODELS / "face_yolov11s.hef", # Calea catre modelul specific de detectare a fetei .hef
            labels_path=MODELS / "face_labels.txt", # Calea catre fisierul cu etichete
            score_thresh=0.5, 
        )