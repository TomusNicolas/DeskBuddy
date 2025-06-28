# hailo_detector.py
from pathlib import Path

from picamera2.devices import Hailo


class HailoDetector:

    def __init__(self, model_path: Path, labels_path: Path, score_thresh: float = 0.5):
        
        self.model_path = Path(model_path).expanduser()
        self.labels_path = Path(labels_path).expanduser()
        self.score_thresh = score_thresh

        # Incarca numele claselor din fisierul cu etichete
        with open(self.labels_path, encoding="utf-8") as f:
            self.class_names = f.read().splitlines()

        # Initializeaza acceleratorul Hailo
        self.hailo = Hailo(str(self.model_path))
        # Preia intrarile intrarii modelului
        self.model_h, self.model_w, _ = self.hailo.get_input_shape()
       

    def infer(self, frame):

        # Trimite imaginea la cip si primeste un rezultat brut
        raw_hailo_output = self.hailo.run(frame)

        # Transforma rezultatul brut intr-o lista structurata
        return self._postprocess(raw_hailo_output, frame.shape[1], frame.shape[0])


    def _postprocess(self, hailo_out, original_frame_width: int, original_frame_height: int):

        results = []
        # parcurge rezultatele brute
        for class_id, detections_for_class in enumerate(hailo_out):
            for detection_details in detections_for_class:
                score = detection_details[4]
                if score < self.score_thresh:
                    continue

                y0_norm, x0_norm, y1_norm, x1_norm = detection_details[:4]
                
                # Coordonatele scalate primite de la infer()
                bbox_scaled_to_original = (
                    int(x0_norm * original_frame_width),   # x0
                    int(y0_norm * original_frame_height),  # y0
                    int(x1_norm * original_frame_width),   # x1
                    int(y1_norm * original_frame_height)   # y1
                )
                # calculeaza coordonatele chenarului
                results.append((self.class_names[class_id], bbox_scaled_to_original, score))
        return results


    @property
    def input_size(self):
        return self.model_w, self.model_h


    def __del__(self):

        # verifica daca conexiunea cu cipul chiar exista
        if hasattr(self, "hailo") and self.hailo is not None:
           
           # transmite cipului ca a terminat procesul
            if hasattr(self.hailo, '__exit__'):
                self.hailo.__exit__(None, None, None)

            self.hailo = None 
