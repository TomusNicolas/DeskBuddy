#phone_detector.py
from pathlib import Path
from .hailo_detector import HailoDetector

# Definirea locatiei modelelor si a fisierelor cu etichete
BASE   = Path(__file__).parent
MODELS = BASE / "models"

class PhoneDetector(HailoDetector):
   
    def __init__(self):

        super().__init__(
            model_path=MODELS / "yolov11s_h8l.hef", # Calea catre modelul general .hef
            labels_path=MODELS / "coco_labels.txt", # Calea catre fisierul cu etichete
            score_thresh=0.5, # Pragul de incredere
        )

    def infer(self, frame):
      
        # Se obtin toate detectiile de la modelul general
        all_detections = super().infer(frame)
        
        # Se pastreaza doar cele a caror eticheta este "phone"
        phone_detections = [d for d in all_detections if d[0] == "phone"]
        return phone_detections
