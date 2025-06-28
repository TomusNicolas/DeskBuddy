# main.py
import os
import time
import cv2
from picamera2 import Picamera2

# Importa configuratiile si functiile de desenare
import config
from drawing import (
    TrackerDrawer, draw_normal, CLASS_COLORS, PROMPT_TEXT_DRINK,
    PROMPT_TEXT_DARK, draw_button, draw_timer_popup, draw_active_timer
)

# Aplica variabila de mediu pentru platforma Qt din config
os.environ["QT_QPA_PLATFORM"] = config.QT_PLATFORM

button_states = config.BUTTON_STATES_INITIAL.copy()

button_clickable_rect_preview = {}
all_button_base_rects_video = {}

# Flag pentru iesirea din aplicatie
should_exit_application = False

# Urmarirea activitatii UI pentru vizibilitatea butoanelor
last_activity_time = time.time()
buttons_fully_visible = True

# Starea temporizatorului
timer_active = False
timer_duration_selected = 0  # in secunde
timer_end_time = 0
show_timer_popup = False
timer_popup_rects_preview = {}
timer_popup_rects_video = {} 
timer_display_text = "00:00"

# Starea detectiei fetei pentru avatar
last_face_detected_time = time.time()
eyes_closed_due_to_no_face = False 


# Calcule Initiale pentru Layout-ul UI (derivate din Config)
_num_main_buttons = len(config.BUTTON_ORDER_MAIN_ROW)
_total_main_btns_width = (_num_main_buttons * config.BTN_ITEM_W) + \
                         ((_num_main_buttons - 1) * config.BTN_ITEM_SPACING)
_start_x_all_main_btns = (config.PREVIEW_W - _total_main_btns_width) // 2

# Zonele pentru butoanele principale (Coordonate Preview)
_current_x_pos = _start_x_all_main_btns
for btn_name in config.BUTTON_ORDER_MAIN_ROW:
    button_clickable_rect_preview[btn_name] = (
        _current_x_pos, config.BTN_MAIN_ROW_Y, config.BTN_ITEM_W, config.BTN_ITEM_H
    )
    _current_x_pos += config.BTN_ITEM_W + config.BTN_ITEM_SPACING

# Layout si zona clickabila pentru butonul de inchidere (Coordonate Preview)
_close_btn_x = config.CLOSE_BTN_MARGIN
_close_btn_y = config.PREVIEW_H - config.CLOSE_BTN_H - config.CLOSE_BTN_MARGIN
button_clickable_rect_preview["close"] = (
    _close_btn_x, _close_btn_y, config.CLOSE_BTN_W, config.CLOSE_BTN_H
)

# Layout si zonele pentru pop-up-ul temporizatorului (Coordonate Preview)
_popup_total_options_height = len(config.TIMER_POPUP_OPTIONS) * \
                              (config.POPUP_OPTION_BTN_H_PREVIEW + config.POPUP_OPTION_SPACING_Y_PREVIEW) - \
                              config.POPUP_OPTION_SPACING_Y_PREVIEW
popup_height_preview_calculated = config.POPUP_TITLE_HEIGHT_PREVIEW + _popup_total_options_height + \
                              (2 * config.POPUP_PADDING_PREVIEW)
popup_x_preview_calculated = (config.PREVIEW_W - config.POPUP_WIDTH_PREVIEW) // 2
popup_y_preview_calculated = (config.PREVIEW_H - popup_height_preview_calculated) // 2

_current_popup_y = popup_y_preview_calculated + config.POPUP_PADDING_PREVIEW + config.POPUP_TITLE_HEIGHT_PREVIEW
for i, (text, duration) in enumerate(config.TIMER_POPUP_OPTIONS):
    _option_x = popup_x_preview_calculated + config.POPUP_PADDING_PREVIEW
    _option_w = config.POPUP_WIDTH_PREVIEW - (2 * config.POPUP_PADDING_PREVIEW)
    timer_popup_rects_preview[f"timer_opt_{duration}"] = (
        _option_x, _current_popup_y, _option_w, config.POPUP_OPTION_BTN_H_PREVIEW
    )
    _current_popup_y += config.POPUP_OPTION_BTN_H_PREVIEW + config.POPUP_OPTION_SPACING_Y_PREVIEW


# Gestioneaza evenimentele de click de la mouse pe fereastra de previzualizare
def mouse_callback(event, x, y, flags, param):
    
    global button_states, should_exit_application, last_activity_time, buttons_fully_visible
    global show_timer_popup, timer_active, timer_duration_selected, timer_end_time

    last_activity_time = time.time()
    buttons_fully_visible = True

    if event == cv2.EVENT_LBUTTONDOWN:
        # Gestionare click pe pop-up-ul temporizatorului
        if show_timer_popup:
            for i, (text, duration) in enumerate(config.TIMER_POPUP_OPTIONS):
                opt_name = f"timer_opt_{duration}"
                if opt_name in timer_popup_rects_preview:
                    bx_popup, by_popup, bw_popup, bh_popup = timer_popup_rects_preview[opt_name]
                    if bx_popup <= x <= bx_popup + bw_popup and \
                       by_popup <= y <= by_popup + bh_popup:
                        timer_duration_selected = duration
                        timer_end_time = time.time() + timer_duration_selected
                        timer_active = True
                        button_states["timer"] = True
                        show_timer_popup = False
                        return

            pb_x, pb_y, pb_w, pb_h = (
                popup_x_preview_calculated, popup_y_preview_calculated,
                config.POPUP_WIDTH_PREVIEW, popup_height_preview_calculated
            )
            if not (pb_x <= x <= pb_x + pb_w and pb_y <= y <= pb_y + pb_h):
                show_timer_popup = False
            return

        # Gestionare click pe randul de butoane principale
        for btn_name in config.BUTTON_ORDER_MAIN_ROW:
            bx, by, bw, bh = button_clickable_rect_preview[btn_name]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if btn_name == "timer":
                    button_states["timer"] = not button_states["timer"]
                    if button_states["timer"] and not timer_active:
                        show_timer_popup = True
                    elif not button_states["timer"] and timer_active:
                        timer_active = False
                    elif button_states["timer"] and timer_active:
                        timer_active = False
                        show_timer_popup = True
                    else:
                        show_timer_popup = False
                else:
                    button_states[btn_name] = not button_states[btn_name]
                    display_name = config.BUTTON_TEXTS_MAP[btn_name]["display"]
                    state_text = "ON" if button_states[btn_name] else "OFF"
                return

        # Gestionare click pe butonul de inchidere
        bx_close, by_close, bw_close, bh_close = button_clickable_rect_preview["close"]
        if bx_close <= x <= bx_close + bw_close and \
           by_close <= y <= by_close + bh_close:
            should_exit_application = True
            return

# Functia principala care ruleaza aplicatia de monitorizare a soferului
def main():

    global button_states, all_button_base_rects_video, should_exit_application
    global last_activity_time, buttons_fully_visible
    global timer_active, timer_end_time, timer_display_text, show_timer_popup, timer_popup_rects_video
    global last_face_detected_time, eyes_closed_due_to_no_face

    # Initializeaza detectoarele de obiecte
    try:
        from detector.face_detector import FaceDetector
        from detector.phone_detector import PhoneDetector
        from detector.drinking_detector import DrinkingDetector
        face_detector = FaceDetector()
        phone_detector = PhoneDetector()
        drinking_detector = DrinkingDetector()
        model_w, model_h = face_detector.input_size
    except ImportError as e:
        class DummyDetector:
            def __init__(self, input_size=(320,240)): self.input_size = input_size
            def infer(self, frame): return []
        face_detector = DummyDetector()
        phone_detector = DummyDetector(input_size=face_detector.input_size)
        drinking_detector = DummyDetector(input_size=face_detector.input_size)
        model_w, model_h = face_detector.input_size

    # Factori de scalare pentru coordonatele detectiilor si elementele UI
    scale_detection_x = config.VIDEO_W / model_w
    scale_detection_y = config.VIDEO_H / model_h
    video_scale_x_for_ui = config.VIDEO_W / config.PREVIEW_W
    video_scale_y_for_ui = config.VIDEO_H / config.PREVIEW_H

    # Converteste dreptunghiurile UI din coordonate preview in coordonate video
    for name, (px, py, pw, ph) in button_clickable_rect_preview.items():
        all_button_base_rects_video[name] = (
            int(px * video_scale_x_for_ui), int(py * video_scale_y_for_ui),
            int(pw * video_scale_x_for_ui), int(ph * video_scale_y_for_ui)
        )
    timer_popup_rects_video.clear()
    for name, (px, py, pw, ph) in timer_popup_rects_preview.items():
        timer_popup_rects_video[name] = (
            int(px * video_scale_x_for_ui), int(py * video_scale_y_for_ui),
            int(pw * video_scale_x_for_ui), int(ph * video_scale_y_for_ui)
        )
    popup_rect_video = (
        int(popup_x_preview_calculated * video_scale_x_for_ui),
        int(popup_y_preview_calculated * video_scale_y_for_ui),
        int(config.POPUP_WIDTH_PREVIEW * video_scale_x_for_ui),
        int(popup_height_preview_calculated * video_scale_y_for_ui)
    )

    drawer = TrackerDrawer(x_detection_bias=25)

    last_drink_time_logic = time.time()
    last_dark_check_logic = time.time()
    dark_count = 0
    show_drink_prompt = False
    show_dark_prompt = False
    prompt_start_time = 0

    last_activity_time = time.time()
    last_face_detected_time = time.time()

    # Configurare Camera
    with Picamera2() as cam:
        main_cfg = {'size': (config.VIDEO_W, config.VIDEO_H), 'format': 'XRGB8888'}
        lores_cfg = {'size': (model_w, model_h), 'format': 'RGB888'}
        controls = {'FrameRate': config.FPS}
        picam_config = cam.create_preview_configuration(
            main=main_cfg, lores=lores_cfg, controls=controls, queue=False
        )
        cam.configure(picam_config)

        cv2.namedWindow(config.PREVIEW_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(config.PREVIEW_WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback(config.PREVIEW_WINDOW_NAME, mouse_callback)
        
        cam.start()

        # BUCLA PRINCIPALA DE PROCESARE
        while not should_exit_application:
            current_time = time.time()

            # Actualizeaza starile UI si temporizatorul
            if current_time - last_activity_time > config.BUTTON_VISIBILITY_TIMEOUT:
                buttons_fully_visible = False

            if timer_active:
                remaining_seconds = timer_end_time - current_time
                if remaining_seconds <= 0:
                    timer_active = False
                    button_states["timer"] = False
                    timer_display_text = "00:00"
                else:
                    minutes = int(remaining_seconds) // 60
                    seconds = int(remaining_seconds) % 60
                    timer_display_text = f"{minutes:02d}:{seconds:02d}"
            elif not show_timer_popup:
                timer_display_text = ""

            # Captura Cadru
            lores_frame = cam.capture_array('lores')
            main_frame_buffer = cam.capture_array('main')

            # Detectie Obiecte (daca monitorizarea e activa)
            raw_faces, raw_phones, raw_drinks = [], [], []
            if button_states["monitor"]:
                raw_faces = face_detector.infer(lores_frame)
                raw_phones = phone_detector.infer(lores_frame)
                raw_drinks = drinking_detector.infer(lores_frame)

            # Logica prezentei fetei (pentru avatar)
            if button_states["monitor"]:
                if raw_faces:
                    last_face_detected_time = current_time
                    eyes_closed_due_to_no_face = False
                elif (current_time - last_face_detected_time > config.NO_FACE_TIMEOUT):
                    eyes_closed_due_to_no_face = True
            else:
                eyes_closed_due_to_no_face = False

            # Logica pentru alerte (apa, intuneric)
            if button_states["dark"] and button_states["monitor"]:
                if current_time - last_dark_check_logic >= config.DARK_CHECK_INTERVAL:
                    last_dark_check_logic = current_time
                    gray_frame = cv2.cvtColor(lores_frame, cv2.COLOR_RGB2GRAY) if lores_frame.ndim == 3 and lores_frame.shape[2] == 3 else lores_frame
                    brightness = gray_frame.mean()
                    if brightness < config.DARK_THRESHOLD:
                        dark_count += 1
                    else:
                        dark_count = 0
                    if dark_count >= 2 and not show_dark_prompt and not show_drink_prompt:
                        show_dark_prompt = True
                        prompt_start_time = current_time
                        dark_count = 0
            if show_dark_prompt and (not button_states["dark"] or \
                                      not button_states["monitor"] or \
                                      (current_time - prompt_start_time) >= config.DARK_PROMPT_DURATION):
                show_dark_prompt = False

            if button_states["water"] and button_states["monitor"]:
                is_drinking_detected = any(raw_drinks)
                if is_drinking_detected:
                    last_drink_time_logic = current_time
                    show_drink_prompt = False
                else:
                    if not show_drink_prompt and not show_dark_prompt and \
                       (current_time - last_drink_time_logic) >= config.DRINK_INTERVAL:
                        show_drink_prompt = True
                        prompt_start_time = current_time
                    elif show_drink_prompt and (current_time - prompt_start_time) >= config.PROMPT_DURATION:
                        show_drink_prompt = False
                        last_drink_time_logic = current_time
            elif show_drink_prompt:
                show_drink_prompt = False

            # detectiile pentru desenare
            all_raw_detections_for_bboxes = []
            if button_states["monitor"]:
                all_raw_detections_for_bboxes = raw_faces + raw_phones + raw_drinks
            
            detections_for_drawing = [
                (cls,
                 (int(x0 * scale_detection_x), int(y0 * scale_detection_y),
                  int(x1 * scale_detection_x), int(y1 * scale_detection_y)),
                 sc)
                for cls, (x0, y0, x1, y1), sc in all_raw_detections_for_bboxes if sc > 0.1
            ]

            # Randeaza Cadrul (Mod Tracking/Normal)
            if config.MODE == "tracking":
                drawer.show_drink_prompt = show_drink_prompt
                drawer.show_dark_prompt = show_dark_prompt
                drawer.draw_on_frame(
                    main_frame_buffer,
                    detections_for_drawing if button_states["monitor"] else [],
                    button_states,
                    all_button_base_rects_video,
                    config.BUTTON_TEXTS_MAP,
                    config.BUTTON_ORDER_MAIN_ROW,
                    button_states["phone"],
                    True, # draw_close_button_flag
                    buttons_fully_visible,
                    show_timer_popup,
                    config.TIMER_POPUP_OPTIONS,
                    timer_popup_rects_video,
                    popup_rect_video,
                    timer_active,
                    timer_display_text,
                    eyes_closed_due_to_no_face
                )
            else: # config.MODE == "normal"
                main_frame_buffer[:,:,:3] = (0,0,0)
                if button_states["monitor"]:
                    draw_normal(
                        main_frame_buffer, detections_for_drawing, CLASS_COLORS,
                        show_drink_prompt, show_dark_prompt
                    )
                for btn_name_ordered in config.BUTTON_ORDER_MAIN_ROW:
                    state = button_states[btn_name_ordered]
                    rect = all_button_base_rects_video[btn_name_ordered]
                    texts = config.BUTTON_TEXTS_MAP[btn_name_ordered]
                    draw_button(main_frame_buffer, rect, state, texts["on"], texts["off"], texts["display"], buttons_fully_visible)
                close_rect = all_button_base_rects_video["close"]
                close_texts = config.BUTTON_TEXTS_MAP["close"]
                draw_button(main_frame_buffer, close_rect, True, close_texts["on"], close_texts["off"], close_texts["display"], True)

                if show_timer_popup:
                    draw_timer_popup(main_frame_buffer, config.TIMER_POPUP_OPTIONS, timer_popup_rects_video, popup_rect_video, buttons_fully_visible)
                if timer_active and timer_display_text:
                    draw_active_timer(main_frame_buffer, timer_display_text, config.VIDEO_W, config.VIDEO_H)
                
                if show_drink_prompt or show_dark_prompt:
                    text_to_show = PROMPT_TEXT_DRINK if show_drink_prompt else PROMPT_TEXT_DARK
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text_scale_prompt = 3.0 if config.VIDEO_W > 800 else 2.0
                    text_thick_prompt = 3 if text_scale_prompt > 2.0 else 2
                    ((tw, th), _) = cv2.getTextSize(text_to_show, font, text_scale_prompt, text_thick_prompt)
                    tx = (config.VIDEO_W - tw) // 2
                    ty = int(config.VIDEO_H * 0.9)
                    cv2.putText(main_frame_buffer, text_to_show, (tx, ty), font, text_scale_prompt, (255,255,255), text_thick_prompt, cv2.LINE_AA)

            # Afiseaza Cadrul si gestioneaza input-ul
            try:
                display_frame_bgr = cv2.cvtColor(main_frame_buffer, cv2.COLOR_RGBA2BGR)
            except cv2.error:
                display_frame_bgr = main_frame_buffer
            
            frame_for_fullscreen_display = cv2.resize(display_frame_bgr, (config.PREVIEW_W, config.PREVIEW_H))
            cv2.imshow(config.PREVIEW_WINDOW_NAME, frame_for_fullscreen_display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                should_exit_application = True

        cv2.destroyAllWindows()
        cam.stop()

if __name__ == "__main__":
    main()