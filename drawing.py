#drawing.py
import cv2
import random
import time
import numpy as np

# Culori predefinite pentru clasele de obiecte detectate
CLASS_COLORS = {
    "face":        (0, 255, 0),   # verde
    "phone":       (255, 0, 0),   # albastru
    "bottle":      (0, 0, 255),   # rosu
    "wine glass":  (0, 0, 255),   # rosu
    "cup":         (0, 0, 255),   # rosu
}

PROMPT_TEXT_DRINK = "Drink some water!"
PROMPT_TEXT_DARK  = "It's too dark, open a light!"
PROMPT_TEXT_ANGRY = "Don't use the phone!"

# Deseneaza un buton pe ecran, cu text si stari vizuale diferite
def draw_button(canvas, base_rect_video, is_on, text_on, text_off,
                display_text=None, fully_visible=True, is_popup_option=False):

    bx_video, by_video, bw_video, bh_video = base_rect_video

    if bw_video <= 0 or bh_video <= 0:
        return
    
    # Definirea culorilor
    color_on = (45, 45, 45)
    color_off = (25, 25, 25)
    popup_option_color = (100, 100, 120)
    
    text_color_default_active = (255, 255, 255)
    text_color_inactive = (60, 60, 60)
    text_color_close_button = (60, 60, 60)

    is_close_button = (display_text == "X")

    solid_button_bg_color = None
    solid_text_color = None

    # Determina culoarea butonului si a textului in functie de stare
    if is_close_button:
        solid_button_bg_color = None
        solid_text_color = text_color_close_button
    elif is_popup_option:
        solid_button_bg_color = popup_option_color
        solid_text_color = text_color_default_active
    else:
        solid_button_bg_color = color_on if is_on else color_off
        solid_text_color = text_color_default_active if is_on else text_color_inactive

    text_to_display = display_text if display_text is not None else (text_on if is_on else text_off)

    # Logica de scalare a textului
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_scale = 0.6
    if bw_video > 0 and len(text_to_display) > 0:
        if len(text_to_display) == 1:
            text_scale = min(1.5, max(0.5, (bh_video / 30) * 0.8))
            if is_close_button:
                text_scale = min(1.8, max(0.6, (bh_video / 25) * 0.8))
        else:
            text_scale = min(1.0, max(0.3, (bw_video / len(text_to_display)) * \
                                      (0.10 if is_popup_option else 0.11)))
        
        (temp_w, _), _ = cv2.getTextSize(text_to_display, font, text_scale, 1)
        padding_factor = 0.80 if is_popup_option or is_close_button else 0.85
        while temp_w > (bw_video * padding_factor) and text_scale > 0.25:
            text_scale -= 0.05
            (temp_w, _), _ = cv2.getTextSize(text_to_display, font, text_scale, 1)
        text_scale = max(0.25, text_scale)

    text_thickness = 1 if text_scale < 0.6 else 2
    if is_close_button and text_scale > 1.0:
        text_thickness = 2
    
    (text_w_calc, text_h_calc), _ = cv2.getTextSize(text_to_display, font, text_scale, text_thickness)

    # Centreaza textul
    text_x_global = bx_video + (bw_video - text_w_calc) // 2
    text_y_global = by_video + (bh_video + text_h_calc) // 2
    text_x_global = max(bx_video, text_x_global)

    # Desenare cu transparenta sau solid
    if not fully_visible and not is_popup_option and not is_close_button:
        alpha_contribution = 0.25
        background_contribution = 1.0 - alpha_contribution

        roi_y_start = max(0, by_video)
        roi_y_end = min(canvas.shape[0], by_video + bh_video)
        roi_x_start = max(0, bx_video)
        roi_x_end = min(canvas.shape[1], bx_video + bw_video)
        
        actual_bh_video = roi_y_end - roi_y_start
        actual_bw_video = roi_x_end - roi_x_start

        if actual_bh_video > 0 and actual_bw_video > 0:
            num_channels = canvas.shape[2]
            solid_overlay = np.zeros((actual_bh_video, actual_bw_video, num_channels), dtype=canvas.dtype)

            if solid_button_bg_color is not None:
                cv2.rectangle(solid_overlay, (0, 0), (actual_bw_video, actual_bh_video), solid_button_bg_color, -1)

            text_x_local = (actual_bw_video - text_w_calc) // 2
            text_y_local = (actual_bh_video + text_h_calc) // 2
            text_x_local = max(0, text_x_local)

            cv2.putText(solid_overlay, text_to_display, (text_x_local, text_y_local), font, text_scale, solid_text_color, text_thickness, cv2.LINE_AA)
            
            roi = canvas[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
            
            if roi.shape[0] == solid_overlay.shape[0] and \
               roi.shape[1] == solid_overlay.shape[1] and \
               roi.ndim == solid_overlay.ndim:
                blended_roi = cv2.addWeighted(solid_overlay, alpha_contribution, roi, background_contribution, 0.0)
                canvas[roi_y_start:roi_y_end, roi_x_start:roi_x_end] = blended_roi
    else:
        if solid_button_bg_color is not None:
            cv2.rectangle(canvas, (bx_video, by_video), (bx_video + bw_video, by_video + bh_video), solid_button_bg_color, -1)
        
        cv2.putText(canvas, text_to_display, (text_x_global, text_y_global), font, text_scale, solid_text_color, text_thickness, cv2.LINE_AA)

# Deseneaza fereastra pop-up pentru selectarea duratei temporizatorului
def draw_timer_popup(canvas, popup_options_list, popup_option_rects_video_map, popup_bg_rect_video, buttons_are_fully_visible_main):
    
    px, py, pw, ph = popup_bg_rect_video

    # Creeaza un fundal semi-transparent
    overlay = canvas.copy()
    cv2.rectangle(overlay, (px, py), (px + pw, py + ph), (50, 50, 50), -1)
    alpha = 0.85
    cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

    # Deseneaza titlul pop-up-ului
    title_text = "Select duration:"
    font = cv2.FONT_HERSHEY_SIMPLEX
    title_scale = 1.2
    title_thickness = 2
    (tw, th), _ = cv2.getTextSize(title_text, font, title_scale, title_thickness)
    title_x = px + (pw - tw) // 2
    title_y = py + th + 40
    cv2.putText(canvas, title_text, (title_x, title_y), font, title_scale, (255,255,255), title_thickness, cv2.LINE_AA)

    # Deseneaza fiecare optiune ca un buton
    for display_text, duration_seconds in popup_options_list:
        opt_name = f"timer_opt_{duration_seconds}"
        if opt_name in popup_option_rects_video_map:
            rect = popup_option_rects_video_map[opt_name]
            draw_button(canvas, rect, False, display_text, display_text, display_text, True, is_popup_option=True)


# Deseneaza afisajul temporizatorului activ
def draw_active_timer(canvas, timer_text, canvas_width, canvas_height):
    
    if not timer_text:
        return

    font = cv2.FONT_HERSHEY_SIMPLEX
    text_scale = 1.8
    text_thickness = 2
    text_color = (255, 255, 255)
    (tw, th), _ = cv2.getTextSize(timer_text, font, text_scale, text_thickness)

    margin = 25
    text_x = canvas_width - tw - margin
    text_y = canvas_height - margin

    cv2.putText(canvas, timer_text, (text_x, text_y), font, text_scale, text_color, text_thickness, cv2.LINE_AA)


# Deseneaza un ochi al avatarului
def draw_eye(canvas, center, width, height, is_closed, angry=False, current_scale=1.0):

    eye_border_thickness = max(1, int(2 * current_scale))
    eye_border_color = (30, 30, 30)
    if angry: height = max(int(10 * current_scale), height // 2)

    x, y = center
    top_left = (x - width // 2, y - height // 2)
    bottom_right = (x + width // 2, y + height // 2)
    
    eye_white_color = (240, 240, 240)
    blink_color = (120, 120, 120)
    color = blink_color if is_closed else eye_white_color
    
    cv2.rectangle(canvas, top_left, bottom_right, color, thickness=-1, lineType=cv2.LINE_AA)
    cv2.rectangle(canvas, top_left, bottom_right, eye_border_color, thickness=eye_border_thickness, lineType=cv2.LINE_AA)

# Deseneaza o pupila in interiorul unui ochi
def draw_pupil(canvas, eye_center, eye_bbox, offset_x, offset_y, pupil_size, current_scale=1.0):
    
    x, y = eye_center
    x += offset_x
    y += offset_y

    (x0, y0), (x1, y1) = eye_bbox
    safe_pupil_size = max(1, pupil_size)

    # Mentine pupila in interiorul ochiului
    x = max(x0 + safe_pupil_size // 2, min(x1 - safe_pupil_size // 2, x))
    y = max(y0 + safe_pupil_size // 2, min(y1 - safe_pupil_size // 2, y))
    
    pupil_color = (10,10,10)
    cv2.rectangle(canvas, (x - safe_pupil_size // 2, y - safe_pupil_size // 2), (x + safe_pupil_size // 2, y + safe_pupil_size // 2), pupil_color, thickness=-1, lineType=cv2.LINE_AA)
    
    # Adauga o sclipire pupilei
    sparkle_sz = max(int(3*current_scale), safe_pupil_size // 3)
    sparkle_x_offset = -sparkle_sz // 4
    sparkle_y_offset = -sparkle_sz // 4
    sparkle_tl = (x + sparkle_x_offset - sparkle_sz // 2, y + sparkle_y_offset - sparkle_sz // 2)
    sparkle_br = (sparkle_tl[0] + sparkle_sz, sparkle_tl[1] + sparkle_sz)
    cv2.rectangle(canvas, sparkle_tl, sparkle_br, (255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)


# Deseneaza gura avatarului, animata pentru vorbire
def draw_mouth(canvas, center, width, height_closed, speaking, current_scale):

    x, y = center
    mouth_border_thickness = max(1, int(2 * current_scale))
    mouth_border_color = (30,30,30)
    mouth_fill_color = (220, 200, 200)
    
    current_width = width
    if speaking: # Animare gura deschisa
        speak_height_options = [
            int(20*current_scale), int(35*current_scale), int(50*current_scale)
        ]
        h = random.choice(speak_height_options)
        h = max(int(5*current_scale), h)
        if h > int(30*current_scale): current_width = int(width * 1.1)
    else:
        h = height_closed
            
    top_left = (x - current_width // 2, y - h // 2)
    bottom_right = (x + current_width // 2, y + h // 2)
    
    cv2.rectangle(canvas, top_left, bottom_right, mouth_fill_color, thickness=-1, lineType=cv2.LINE_AA)
    cv2.rectangle(canvas, top_left, bottom_right, mouth_border_color, thickness=mouth_border_thickness, lineType=cv2.LINE_AA)


# Gestioneaza desenarea avatarului, elementelor UI si alertelor pentru modul "tracking"
class TrackerDrawer:
    
    # Initializeaza setarile pentru desenare
    def __init__(self, blink_interval: int = 280, blink_duration: int = 4, smoothing_factor: float = 0.5, x_detection_bias: int = 25):
        
        self.blink_interval = blink_interval
        self.blink_duration = blink_duration
        self.smoothing_factor = smoothing_factor
        self.x_detection_bias = x_detection_bias
        self.show_drink_prompt = False
        self.show_dark_prompt = False
        self.frame_counter = 0
        self.speaking = False
        self.smoothed_x = None
        self.smoothed_y = None
        self.last_phone_time = 0.0


    # Deseneaza sprancene inclinate pentru o expresie "nervoasa"
    def _draw_angry_eyebrows(self, canvas, eye_center_x, eye_top_y, eye_width, current_scale, is_left_eye):
        
        eyebrow_color = (220, 220, 220)
        eyebrow_thickness = max(1, int(8 * current_scale))
        
        eyebrow_h_len_factor = 0.5
        eyebrow_lateral_extent = int(eye_width * eyebrow_h_len_factor)
        
        eyebrow_v_offset = int(100 * current_scale)
        y_anchor = eye_top_y - eyebrow_v_offset

        slant_amount = int(25 * current_scale)
        y_medial_relative = slant_amount // 2
        y_lateral_relative = -slant_amount // 2

        medial_shift_from_eye_center = int(eye_width * 0.33)
        lateral_point_adjustment = int(eye_width * 0.11)

        if is_left_eye: # Spranceana stanga
            x_medial = eye_center_x + medial_shift_from_eye_center
            x_lateral = eye_center_x - eyebrow_lateral_extent + lateral_point_adjustment
            y_medial_abs = y_anchor + y_medial_relative
            y_lateral_abs = y_anchor + y_lateral_relative
        else: # Spranceana dreapta
            x_medial = eye_center_x - medial_shift_from_eye_center
            x_lateral = eye_center_x + eyebrow_lateral_extent - lateral_point_adjustment
            y_medial_abs = y_anchor + y_medial_relative
            y_lateral_abs = y_anchor + y_lateral_relative
            
        cv2.line(canvas, (x_medial, y_medial_abs), (x_lateral, y_lateral_abs), eyebrow_color, eyebrow_thickness, cv2.LINE_AA)

    def draw_on_frame(self, canvas, detections,
                      all_button_states, all_button_base_rects_video, all_button_texts_map,
                      button_order_main_row_list,
                      enable_angry_phone_reaction_state=True,
                      draw_close_button_flag=False,
                      buttons_are_fully_visible=True,
                      should_show_timer_popup=False,
                      timer_popup_options_data=None,
                      timer_popup_option_rects_data_video=None,
                      timer_popup_bg_rect_data_video=None,
                      is_timer_active=False,
                      current_timer_display_text="",
                      force_eyes_closed_no_face=False):

        # Initializare
        canvas[:, :, :3] = (0, 0, 0) # Fundal negru
        h_canvas, w_canvas = canvas.shape[:2]
        self.frame_counter += 1
        angry_reaction_active = False

        # Desenare Avatar daca butonul 'monitor' este activ
        if all_button_states["monitor"]:
            # Scalare si parametri de baza ai avatarului
            base_avatar_scale = 0.9
            dynamic_factor = 1.0
            if w_canvas < 800: dynamic_factor = 0.75
            elif w_canvas > 1500: dynamic_factor = 1.05
            current_scale = base_avatar_scale * dynamic_factor

            eye_w = int(500*current_scale); eye_h = int(330*current_scale)
            pupil_size = int(110*current_scale)
            eye_spacing = int(700*current_scale)
            
            available_x_move = (eye_w/2)-(pupil_size/2)
            available_y_move = (eye_h/2)-(pupil_size/2)
            max_off_x = int(available_x_move*1.5); max_off_x = max(1,max_off_x)
            max_off_y = int(available_y_move*1.5); max_off_y = max(1,max_off_y)

            avatar_center_y = h_canvas//2 - int(80*current_scale)
            mouth_center_y_offset = int(310*current_scale)
            avatar_center_x = w_canvas//2
            
            mouth_center = (avatar_center_x, avatar_center_y + mouth_center_y_offset)
            mouth_w = int(280*current_scale); mouth_closed_h = int(18*current_scale)
            
            left_eye_center = (avatar_center_x - eye_spacing//2, avatar_center_y)
            right_eye_center = (avatar_center_x + eye_spacing//2, avatar_center_y)
            
            # Urmarirea pupilei pe baza detectiei fetei
            current_face_x_video, current_face_y_video = w_canvas//2, h_canvas//2
            
            if not force_eyes_closed_no_face:
                if detections:
                    face_dets = [d for d in detections if d[0]=="face"]
                    if face_dets:
                        _,(x0,y0,x1,y1),_ = face_dets[0]
                        current_face_x_video=(x0+x1)//2
                        current_face_y_video=(y0+y1)//2
                
                # Netezirea miscarii pupilei
                if self.smoothed_x is None:
                    self.smoothed_x, self.smoothed_y = current_face_x_video, current_face_y_video
                else:
                    self.smoothed_x = self.smoothing_factor*current_face_x_video + \
                                      (1-self.smoothing_factor)*self.smoothed_x
                    self.smoothed_y = self.smoothing_factor*current_face_y_video + \
                                      (1-self.smoothing_factor)*self.smoothed_y
            
            # Calculeaza deviatia pupilei
            pupil_offset_x, pupil_offset_y = 0, 0
            if not force_eyes_closed_no_face and self.smoothed_x is not None:
                smoothed_x_int = int(self.smoothed_x)
                smoothed_y_int = int(self.smoothed_y)
                
                calibrated_smoothed_x = smoothed_x_int + self.x_detection_bias
                mirrored_x = w_canvas - calibrated_smoothed_x
                
                dx = mirrored_x - avatar_center_x
                dy = smoothed_y_int - avatar_center_y
                
                norm_dx = dx/(w_canvas/2) if (w_canvas/2)!=0 else 0
                norm_dy = dy/(h_canvas/2) if (h_canvas/2)!=0 else 0
                off_x_factor = np.sign(norm_dx)*(abs(norm_dx)**1.1)
                off_y_factor = np.sign(norm_dy)*(abs(norm_dy)**1.1)
                
                pupil_offset_x = int(off_x_factor*max_off_x)
                pupil_offset_y = int(off_y_factor*max_off_y)
                
                pupil_offset_x = max(-max_off_x,min(max_off_x,pupil_offset_x))
                pupil_offset_y = max(-max_off_y,min(max_off_y,pupil_offset_y))
            
            # Starea ochilor
            regular_blink_active = (self.frame_counter % self.blink_interval) < self.blink_duration
            eyes_are_closed_final = regular_blink_active or force_eyes_closed_no_face
            
            # Reactie nervoasa la utilizarea telefonului
            if enable_angry_phone_reaction_state:
                phone_detected_this_frame = any(cls=="phone" for cls,*_ in detections)
                if phone_detected_this_frame: self.last_phone_time = time.time()
                if (time.time()-self.last_phone_time) < 2.5: # 2.5 secunde de reactie
                    angry_reaction_active = True

            # Desenare ochi si sprancene avatar
            for eye_c, is_left_eye_flag in [(left_eye_center,True),(right_eye_center,False)]:
                current_eye_h = max(int(10*current_scale),eye_h//2) if angry_reaction_active else eye_h
                eye_top_left = (eye_c[0]-eye_w//2, eye_c[1]-current_eye_h//2)
                eye_bottom_right = (eye_c[0]+eye_w//2, eye_c[1]+current_eye_h//2)
                
                draw_eye(canvas,eye_c,eye_w,eye_h,eyes_are_closed_final,angry_reaction_active,current_scale)
                
                if not eyes_are_closed_final:
                    draw_pupil(canvas,eye_c,(eye_top_left,eye_bottom_right),pupil_offset_x,pupil_offset_y,pupil_size,current_scale)
                
                if angry_reaction_active:
                    self._draw_angry_eyebrows(canvas,eye_c[0], eye_c[1] - current_eye_h // 2, eye_w, current_scale, is_left_eye_flag)
            
            # Animatie vorbire
            avatar_can_speak_now = not force_eyes_closed_no_face and angry_reaction_active
            if self.frame_counter%10==0:
                self.speaking = random.choices([True,False],weights=[0.4,0.6])[0] if avatar_can_speak_now else False
            draw_mouth(canvas,mouth_center,mouth_w,mouth_closed_h,self.speaking,current_scale)

        # Alerte text (Apa, Intuneric, Nervos)
        prompt_text_to_display = None
        prompt_color = (255, 255, 255)
        prompt_y_pos_factor = 0.93

        if angry_reaction_active:
            prompt_text_to_display = PROMPT_TEXT_ANGRY
        elif self.show_drink_prompt:
            prompt_text_to_display = PROMPT_TEXT_DRINK
        elif self.show_dark_prompt:
            prompt_text_to_display = PROMPT_TEXT_DARK

        if prompt_text_to_display:
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_scale_prompt = 2.5 if w_canvas > 800 else 1.8
            text_thick_prompt = 3 if text_scale_prompt > 2.0 else 2
            ((tw,th),_)=cv2.getTextSize(prompt_text_to_display,font,text_scale_prompt,text_thick_prompt)
            tx = (w_canvas-tw)//2
            ty = int(h_canvas * prompt_y_pos_factor)
            cv2.putText(canvas,prompt_text_to_display,(tx,ty),font,text_scale_prompt,prompt_color,text_thick_prompt,cv2.LINE_AA)

        # Desenare butoane principale UI
        for btn_name_ordered in button_order_main_row_list:
            state = all_button_states[btn_name_ordered]
            rect = all_button_base_rects_video[btn_name_ordered]
            texts = all_button_texts_map[btn_name_ordered]
            draw_button(canvas, rect, state, texts["on"], texts["off"], texts["display"], buttons_are_fully_visible)

        # Desenare buton Inchidere
        if draw_close_button_flag and "close" in all_button_base_rects_video:
            close_rect = all_button_base_rects_video["close"]
            close_texts = all_button_texts_map["close"]
            draw_button(canvas, close_rect, True, close_texts["on"], close_texts["off"], close_texts["display"], True)

        # Desenare pop-up temporizator sau afisaj temporizator activ
        if should_show_timer_popup and timer_popup_options_data and \
           timer_popup_option_rects_data_video and timer_popup_bg_rect_data_video:
            draw_timer_popup(canvas, timer_popup_options_data, timer_popup_option_rects_data_video, timer_popup_bg_rect_data_video, buttons_are_fully_visible)
        elif is_timer_active and current_timer_display_text:
            draw_active_timer(canvas, current_timer_display_text, w_canvas, h_canvas)


def draw_normal(canvas, detections, class_colors, show_drink_prompt, show_dark_prompt):

    if detections:
        for cls, (x0, y0, x1, y1), score in detections:
            label = f"{cls} {int(score * 100)}%"
            color = class_colors.get(cls, (0, 255, 0)) # Verde implicit
            cv2.rectangle(canvas, (x0, y0), (x1, y1), color, 2) # Chenar
            cv2.putText(canvas, label, (x0 + 5, y0 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)