"""
用户界面组件模块 (Widgets)
V8.3.0: 修复统计项截断问题 & 优化弹窗边框消隐
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
from core.config import AppConfig, ColorConfig, TextConfig, ERR_NAMES_MAP, TUNING_TREE, PARAM_TIPS
from ui.utils import draw_box_with_alpha, draw_text_shadow, draw_centered_text, bgr2rgb

class WidgetRenderer:
    def __init__(self):
        try:
            self.font_lg = ImageFont.truetype(AppConfig.FONT, 42)
            self.font_md = ImageFont.truetype(AppConfig.FONT, 26)
            self.font_sm = ImageFont.truetype(AppConfig.FONT, 18)
            self.font_xs = ImageFont.truetype(AppConfig.FONT, 14)
        except:
            self.font_lg = self.font_md = self.font_sm = self.font_xs = ImageFont.load_default()
        
        self.menu_anim_val = 0.0 
        self.modal_anim_val = 0.0
        self.hover_anims = {} 
        self.scroll_y = 0
        self.max_scroll = 0
        
        self.hit_boxes = {} 
        self.hit_boxes['menu_items'] = [] 
        self.tuning_boxes = {}
        
        self.hover_keys = [
            "menu_btn", "height_input", "seek_bar", "btn_play",
            "btn_cam", "btn_video", "btn_tune",
            "modal_confirm", "modal_cancel", "modal_close"
        ]
        self.hover = {k: False for k in self.hover_keys}
        
        for i in range(100):
            self.hover[f"i{i}"] = False
            self.hover[f"input_{i}"] = False
            self.hover[f"tooltip_{i}"] = False
            
        self.update_layout(False, 4)

    def _update_anim(self, key, is_active, speed=0.2):
        current = self.hover_anims.get(key, 0.0)
        target = 1.0 if is_active else 0.0
        if abs(target - current) < 0.01: self.hover_anims[key] = target
        else: self.hover_anims[key] = current + (target - current) * speed
        return self.hover_anims[key]

    def _get_anim_color(self, base_col, active_col, progress):
        c1 = np.array(base_col); c2 = np.array(active_col)
        res = c1 * (1 - progress) + c2 * progress
        return (int(res[0]), int(res[1]), int(res[2]))

    def _ease_out_cubic(self, x): return 1 - (1 - x) ** 3

    def _apply_alpha(self, color, alpha, bg_color=(30, 30, 35)):
        c = np.array(color); bg = np.array(bg_color)
        res = c * alpha + bg * (1.0 - alpha)
        return (int(res[2]), int(res[1]), int(res[0]))

    def update_layout(self, menu_open, num_actions):
        self.hit_boxes['menu_btn'] = (20, 20, 240, 70)
        self.hit_boxes['height_input'] = (260, 20, 480, 70)
        self.hit_boxes['seek_bar'] = (60, AppConfig.H-40, AppConfig.HALF_W-20, AppConfig.H-20)
        self.hit_boxes['btn_play'] = (10, AppConfig.H-45, 50, AppConfig.H-15)
        by = AppConfig.H - 80
        self.hit_boxes['btn_cam'] = (20, by, 100, by+30)
        self.hit_boxes['btn_video'] = (120, by, 220, by+30)
        self.hit_boxes['btn_tune'] = (240, by, 340, by+30)
        self.hit_boxes['menu_items'] = []
        if menu_open or self.menu_anim_val > 0.01:
            for i in range(num_actions):
                y = 75 + i * 55
                self.hit_boxes['menu_items'].append((20, y, 240, y + 50))

    def hit_test(self, x, y, modal_open=False):
        if modal_open:
            for name, rect in self.tuning_boxes.items():
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]: return name
            return None 
        for i, rect in enumerate(self.hit_boxes.get('menu_items', [])):
            if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]: return f"menu_item_{i}"
        for name, rect in self.hit_boxes.items():
            if name == 'menu_items': continue
            if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]: return name
        return None

    def update_hover(self, x, y, menu_open, num_actions=5, modal_open=False):
        self.update_layout(menu_open, num_actions)
        for k in self.hover: self.hover[k] = False
        hit = self.hit_test(x, y, modal_open)
        if hit:
             if hit.startswith("menu_item_"):
                 idx = hit.split("_")[2]
                 self.hover[f"i{idx}"] = True
             else: self.hover[hit] = True

    def draw_all_layers(self, img, mode, count, fps, menu, h_str, typing, msg, msg_color, error_stats, bad_reps, vid, paused, menu_items=None):
        self.update_layout(menu, 5)
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        
        target = 1.0 if menu else 0.0
        if target == 0.0: self.menu_anim_val = 0.0
        else: self.menu_anim_val += (target - self.menu_anim_val) * 0.2
        if abs(self.menu_anim_val - target) < 0.001: self.menu_anim_val = target

        self._draw_stats(draw, count, bad_reps, error_stats, msg)
        self._draw_top_bar(draw, img, mode, h_str, typing)
        self._draw_dropdown(draw, img, menu_items)
        self._draw_bottom_bar(draw, img, fps)
        if msg: self._draw_message(draw, img, msg, msg_color)
        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    def draw_video_bar(self, img, prog, paused):
        h, w = img.shape[:2]; by = h - 25
        c_play = self._get_anim_color(ColorConfig.TEXT_MAIN, ColorConfig.NEON_YELLOW, self._update_anim('btn_play', self.hover['btn_play']))
        if paused:
            pts = np.array([[20, by-8], [20, by+8], [36, by]], np.int32)
            cv2.fillPoly(img, [pts], c_play)
        else:
            cv2.rectangle(img, (20, by-8), (24, by+8), c_play, -1); cv2.rectangle(img, (28, by-8), (32, by+8), c_play, -1)
        bx, bw = 60, w - 80
        cv2.rectangle(img, (bx, by-4), (bx+bw, by+4), (40,40,50), -1)
        fw = int(bw * prog)
        c_bar = ColorConfig.NEON_YELLOW if self.hover['seek_bar'] else ColorConfig.NEON_BLUE
        cv2.rectangle(img, (bx, by-4), (bx+fw, by+4), c_bar, -1)
        cv2.circle(img, (bx+fw, by), 6, (255,255,255), -1)
        if self.hover['seek_bar']: cv2.circle(img, (bx+fw, by), 10, (255,255,255), 1)

    def _draw_stats(self, draw, count, bad_reps, error_stats, msg):
        Y_LBL = 22; Y_VAL = 10; rx_count = AppConfig.W - 200 
        draw_text_shadow(draw, rx_count, Y_LBL, TextConfig.LABEL_COUNT, self.font_sm, ColorConfig.TEXT_DIM)
        draw_text_shadow(draw, rx_count + 80, Y_VAL, str(count or 0), self.font_lg, ColorConfig.NEON_YELLOW)
        rx_acc = rx_count - 220; acc_str = "-"
        acc_col = ColorConfig.NEON_YELLOW
        if count > 0:
            acc_val = int(((count - bad_reps) / count) * 100); acc_val = max(0, min(100, acc_val))
            acc_str = f"{acc_val}%"
            acc_col = ColorConfig.NEON_GREEN if acc_val >= 80 else (ColorConfig.NEON_ORANGE if acc_val >= 60 else ColorConfig.NEON_RED)
        draw_text_shadow(draw, rx_acc, Y_LBL, TextConfig.LABEL_ACC, self.font_sm, ColorConfig.TEXT_DIM)
        draw_text_shadow(draw, rx_acc + 80, Y_VAL, acc_str, self.font_lg, acc_col)
        
        rx_stat = rx_acc - 180
        display_keys = set([k for k, v in error_stats.items() if v > 0])
        for k in error_stats.keys():
            if k in msg: display_keys.add(k)
            
        for k in display_keys:
             v = error_stats.get(k, 0)
             name = ERR_NAMES_MAP.get(k, k)
             draw_text_shadow(draw, rx_stat, Y_LBL+2, name, self.font_sm, ColorConfig.NEON_RED)
             draw_text_shadow(draw, rx_stat + 90, Y_LBL-4, str(v), self.font_md, ColorConfig.NEON_RED)
             rx_stat -= 160
             # [Fix] Relaxed cutoff limit to allow more error types to show
             if rx_stat < AppConfig.W // 10: break

    def _draw_top_bar(self, draw, img, mode, h_str, typing):
        prog = self._update_anim('menu_btn', self.hover['menu_btn'])
        c_menu = self._get_anim_color(ColorConfig.UI_BORDER_NORMAL, ColorConfig.UI_BORDER_ACTIVE, prog)
        rect_m = self.hit_boxes['menu_btn']
        draw_box_with_alpha(img, rect_m, c_menu) 
        draw.rectangle(rect_m, outline=bgr2rgb(c_menu), width=2)
        draw_centered_text(draw, rect_m, mode, self.font_md, ColorConfig.NEON_YELLOW)
        draw.text((200, 45), "▼", font=self.font_sm, fill=bgr2rgb(ColorConfig.TEXT_DIM), anchor="mm")
        
        prog_h = self._update_anim('height_input', typing or self.hover['height_input'])
        c_h = self._get_anim_color(ColorConfig.UI_BORDER_NORMAL, ColorConfig.UI_BORDER_ACTIVE, prog_h)
        rect_h = self.hit_boxes['height_input']
        draw_box_with_alpha(img, rect_h, c_h)
        draw.rectangle(rect_h, outline=bgr2rgb(c_h), width=2)
        draw_text_shadow(draw, 270, 32, "身高", self.font_sm, ColorConfig.TEXT_DIM)
        disp_h = h_str + ("|" if (typing and time.time()%1>0.5) else "")
        draw_text_shadow(draw, 330, 27, disp_h, self.font_md, ColorConfig.TEXT_MAIN)
        draw_text_shadow(draw, 420, 32, "cm", self.font_sm, ColorConfig.TEXT_DIM)

    def _draw_dropdown(self, draw, img, menu_items=None):
        if self.menu_anim_val > 0.01:
            # [Fix] 使用传入的菜单项，如果未传入则使用默认全集
            opts = menu_items if menu_items else [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE, TextConfig.ACT_LUNGE, TextConfig.ACT_LATERAL_RAISE]
            visible_h = int(self.menu_anim_val * (len(opts) * 55))
            y = 75
            for i, m in enumerate(opts):
                if (y - 75) > visible_h: break
                rect = (20, y, 240, y+50)
                key = f"i{i}"
                is_hover = self.hover[key]
                prog = self._update_anim(key, is_hover, speed=0.3)
                draw_box_with_alpha(img, rect, (20,20,25), alpha=0.9)
                border_col = self._get_anim_color(ColorConfig.UI_BORDER_NORMAL, ColorConfig.UI_BORDER_ACTIVE, prog)
                draw.rectangle(rect, outline=bgr2rgb(border_col), width=2)
                draw_centered_text(draw, rect, m, self.font_md, ColorConfig.TEXT_MAIN)
                y += 55

    def _draw_bottom_bar(self, draw, img, fps):
        draw_text_shadow(draw, 20, AppConfig.H - 105, f"{TextConfig.LABEL_FPS}: {fps}", self.font_xs, ColorConfig.FPS)
        def draw_btn(key, text):
            prog = self._update_anim(key, self.hover[key])
            col = self._get_anim_color(ColorConfig.UI_BORDER_NORMAL, ColorConfig.UI_BORDER_ACTIVE, prog)
            rect = self.hit_boxes[key]
            draw_box_with_alpha(img, rect, col)
            draw.rectangle(rect, outline=bgr2rgb(col), width=2)
            draw_centered_text(draw, rect, text, self.font_xs, ColorConfig.TEXT_MAIN)
        draw_btn('btn_cam', TextConfig.BTN_CAM)
        draw_btn('btn_video', TextConfig.BTN_VIDEO)
        draw_btn('btn_tune', TextConfig.BTN_TUNE)

    def _draw_message(self, draw, img, msg, msg_color):
        bbox = draw.textbbox((0,0), msg, font=self.font_lg)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        pad = 40
        cx, cy = AppConfig.W//2, AppConfig.H-100
        rect_msg = (cx - tw//2 - pad, cy - th//2 - pad, cx + tw//2 + pad, cy + th//2 + pad)
        draw_box_with_alpha(img, rect_msg, msg_color) 
        draw_centered_text(draw, rect_msg, msg, self.font_lg, msg_color, shadow=False)

    def draw_tuning_modal(self, img, mode, temp_params, active_idx, is_open):
        target = 1.0 if is_open else 0.0
        speed = 0.15 if is_open else 0.25
        self.modal_anim_val += (target - self.modal_anim_val) * speed
        if not is_open and self.modal_anim_val < 0.01: self.modal_anim_val = 0.0
        if self.modal_anim_val < 0.01: return

        t = self.modal_anim_val; eased_t = self._ease_out_cubic(t)
        slide_dist = 100; y_offset = int(slide_dist * (1.0 - eased_t)); alpha = t

        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (AppConfig.W, AppConfig.H), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.7 * alpha, img, 1.0 - (0.7 * alpha), 0, img)
        
        mw, mh = 600, 500
        mx = (AppConfig.W - mw) // 2
        base_my = (AppConfig.H - mh) // 2
        my = base_my + y_offset
        bg = (30, 30, 35)
        
        draw_box_with_alpha(img, (mx, my, mx+mw, my+mh), bg, alpha=1.0 * alpha)
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        
        c_border = self._apply_alpha(ColorConfig.UI_BORDER_NORMAL, alpha, bg)
        draw.rectangle((mx, my, mx+mw, my+mh), outline=c_border, width=2)
        
        if alpha > 0.05:
            c_title = self._apply_alpha(ColorConfig.NEON_YELLOW, alpha, bg)
            draw.text((mx+50, my+30), f"{TextConfig.LBL_TUNING}: {mode}", font=self.font_md, fill=c_title, anchor="lm")
            
            close_x, close_y = mx + mw - 50, my + 10
            self.tuning_boxes['modal_close'] = (close_x, close_y, close_x+40, close_y+40)
            c_close = self._apply_alpha(ColorConfig.NEON_RED if self.hover['modal_close'] else ColorConfig.TEXT_DIM, alpha, bg)
            draw_centered_text(draw, self.tuning_boxes['modal_close'], "X", self.font_md, c_close, shadow=False)
            
            groups = TUNING_TREE.get(mode, [])
            row_h = 55
            total_content_h = 0
            for grp in groups:
                total_content_h += row_h 
                if grp.get('switch'):
                    val = temp_params.get(grp['switch'], 'True')
                    if val == 'True': total_content_h += len(grp['params']) * row_h
            
            view_h = mh - 160
            self.max_scroll = max(0, total_content_h - view_h)
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            
            content_y_start = my + 100
            content_y_end = my + mh - 70
            curr_y = content_y_start - self.scroll_y
            
            flat_idx = 0 
            active_tooltip = None
            tooltip_y = 0
            
            for grp in groups:
                if curr_y + row_h > content_y_start and curr_y < content_y_end:
                    switch_key = grp.get('switch')
                    header_txt = grp['name']
                    
                    if switch_key:
                        s_val = str(temp_params.get(switch_key, 'True'))
                        is_on = (s_val == 'True')
                        bx, by = mx + 40, curr_y + 16
                        sw_rect = (bx, by, bx+24, by+24)
                        self.tuning_boxes[f"input_{flat_idx}"] = sw_rect 
                        
                        is_sw_hover = self.hover.get(f"input_{flat_idx}", False)
                        c_sw_outline = self._apply_alpha(ColorConfig.NEON_BLUE if is_sw_hover else (ColorConfig.UI_BORDER_ACTIVE if is_on else ColorConfig.TEXT_DIM), alpha, bg)
                        draw.rectangle(sw_rect, outline=c_sw_outline, width=2)
                        
                        if is_on:
                            inner = (bx+4, by+4, bx+20, by+20)
                            draw.rectangle(inner, fill=self._apply_alpha(ColorConfig.NEON_GREEN, alpha, bg))
                        
                        c_head = self._apply_alpha(ColorConfig.TEXT_MAIN, alpha, bg)
                        draw.text((bx+40, curr_y+28), header_txt, font=self.font_sm, fill=c_head, anchor="lm")
                        
                        label_w = draw.textlength(header_txt, font=self.font_sm)
                        qm_x = bx + 40 + label_w + 20
                        qm_y = curr_y + 28
                        tooltip_key = f"tooltip_{flat_idx}"
                        self.tuning_boxes[tooltip_key] = (bx+30, curr_y, qm_x+20, curr_y+row_h)
                        
                        is_row_hover = self.hover.get(tooltip_key, False)
                        c_qm = self._apply_alpha(ColorConfig.NEON_BLUE if is_row_hover else ColorConfig.TEXT_DIM, alpha, bg)
                        draw.ellipse((qm_x-9, qm_y-9, qm_x+9, qm_y+9), outline=c_qm, width=1)
                        draw.text((qm_x, qm_y), "?", font=self.font_xs, fill=c_qm, anchor="mm")
                        
                        if is_row_hover:
                            active_tooltip = PARAM_TIPS.get(switch_key, "暂无说明")
                            tooltip_y = qm_y

                        prio_key = grp.get('prio')
                        if prio_key:
                            prio_val = str(temp_params.get(prio_key, "1"))
                            px = mx + 500; py = curr_y + 12
                            prio_rect = (px, py, px+50, py+30)
                            self.tuning_boxes[f"input_{flat_idx+1}"] = prio_rect
                            is_prio_active = ((flat_idx+1) == active_idx)
                            c_prio = self._apply_alpha(ColorConfig.NEON_BLUE if is_prio_active else ColorConfig.UI_BORDER_NORMAL, alpha, bg)
                            draw.rectangle(prio_rect, outline=c_prio, width=2)
                            
                            draw.text((px-5, py+15), "优先级:", font=self.font_sm, fill=self._apply_alpha(ColorConfig.TEXT_DIM, alpha, bg), anchor="rm")
                            draw.text((px+25, py+15), prio_val + ("|" if is_prio_active and time.time()%1>0.5 else ""), font=self.font_sm, fill=self._apply_alpha(ColorConfig.TEXT_MAIN, alpha, bg), anchor="mm")

                    else:
                        c_head = self._apply_alpha(ColorConfig.NEON_BLUE, alpha, bg)
                        draw.text((mx+40, curr_y+28), header_txt, font=self.font_sm, fill=c_head, anchor="lm")
                        
                curr_y += row_h
                flat_idx += 1
                if grp.get('prio'): flat_idx += 1 
                
                if grp.get('switch') and temp_params.get(grp['switch'], 'True') == 'False':
                    continue 
                
                for param_key, param_lbl in grp['params']:
                    if curr_y + row_h > content_y_start and curr_y < content_y_end:
                        val = str(temp_params.get(param_key, ""))
                        
                        line_col = self._apply_alpha(ColorConfig.UI_BORDER_NORMAL, alpha, bg)
                        draw.line([(mx+52, curr_y-15), (mx+52, curr_y+25)], fill=line_col, width=1)
                        draw.line([(mx+52, curr_y+25), (mx+70, curr_y+25)], fill=line_col, width=1)
                        
                        tooltip_key = f"tooltip_{flat_idx}"
                        is_row_hover = self.hover.get(tooltip_key, False)
                        
                        c_lbl = self._apply_alpha(ColorConfig.NEON_YELLOW if is_row_hover else ColorConfig.TEXT_DIM, alpha, bg)
                        draw.text((mx+80, curr_y+28), param_lbl, font=self.font_sm, fill=c_lbl, anchor="lm")
                        
                        lbl_w = draw.textlength(param_lbl, font=self.font_sm)
                        qm_x = mx + 80 + lbl_w + 20
                        qm_y = curr_y + 28
                        
                        self.tuning_boxes[tooltip_key] = (mx+70, curr_y, qm_x+20, curr_y+row_h)
                        
                        c_qm = self._apply_alpha(ColorConfig.NEON_BLUE if is_row_hover else ColorConfig.TEXT_DIM, alpha, bg)
                        draw.ellipse((qm_x-9, qm_y-9, qm_x+9, qm_y+9), outline=c_qm, width=1)
                        draw.text((qm_x, qm_y), "?", font=self.font_xs, fill=c_qm, anchor="mm")
                        
                        if is_row_hover:
                            active_tooltip = PARAM_TIPS.get(param_key, "暂无说明")
                            tooltip_y = qm_y

                        ib_rect = (mx+410, curr_y+10, mx+550, curr_y+40)
                        self.tuning_boxes[f"input_{flat_idx}"] = ib_rect
                        
                        is_active = (flat_idx == active_idx)
                        c_ib = self._apply_alpha(ColorConfig.NEON_BLUE if is_active else (ColorConfig.UI_BORDER_NORMAL if not self.hover[f"input_{flat_idx}"] else ColorConfig.TEXT_DIM), alpha, bg)
                        draw.rectangle(ib_rect, outline=c_ib, width=2)
                        
                        c_val = self._apply_alpha(ColorConfig.TEXT_MAIN, alpha, bg)
                        blink = "|" if is_active and time.time()%1>0.5 else ""
                        draw.text((mx+420, curr_y+25), val + blink, font=self.font_sm, fill=c_val, anchor="lm")
                    
                    curr_y += row_h
                    flat_idx += 1

            if self.max_scroll > 0:
                sb_h = int((view_h / total_content_h) * view_h)
                sb_h = max(20, sb_h)
                sb_y = content_y_start + int((self.scroll_y / self.max_scroll) * (view_h - sb_h))
                sb_x = mx + mw - 8
                draw.rectangle((sb_x, sb_y, sb_x+4, sb_y+sb_h), fill=self._apply_alpha(ColorConfig.UI_BORDER_ACTIVE, alpha, bg))

            btn_y = my + mh - 80
            
            c_rect = (mx+100, btn_y, mx+260, btn_y+50)
            self.tuning_boxes['modal_cancel'] = c_rect
            is_c_hover = self.hover['modal_cancel']
            # [Fix] Cancel Red Hover
            col_c = self._apply_alpha(ColorConfig.NEON_RED if is_c_hover else ColorConfig.UI_BORDER_NORMAL, alpha, bg)
            txt_c = self._apply_alpha(ColorConfig.NEON_RED if is_c_hover else ColorConfig.TEXT_DIM, alpha, bg)
            draw.rectangle(c_rect, outline=col_c, width=2)
            draw_centered_text(draw, c_rect, TextConfig.BTN_CANCEL, self.font_sm, txt_c)
            
            k_rect = (mx+340, btn_y, mx+500, btn_y+50)
            self.tuning_boxes['modal_confirm'] = k_rect
            is_k_hover = self.hover['modal_confirm']
            # [Fix] Confirm Green Hover
            col_k = self._apply_alpha(ColorConfig.NEON_GREEN if is_k_hover else ColorConfig.UI_BORDER_NORMAL, alpha, bg)
            txt_k = self._apply_alpha(ColorConfig.NEON_GREEN if is_k_hover else ColorConfig.TEXT_DIM, alpha, bg)
            draw.rectangle(k_rect, outline=col_k, width=2)
            draw_centered_text(draw, k_rect, TextConfig.BTN_CONFIRM, self.font_sm, txt_k)
            
            if active_tooltip:
                lines = []
                line = ""
                for char in active_tooltip:
                    if char == '\n': lines.append(line); line = ""
                    else:
                        line += char
                        if len(line) > 18: lines.append(line); line = ""
                if line: lines.append(line)
                
                tip_w = 300
                tip_h = 20 + len(lines) * 25
                tx = mx + 620 
                if tx + tip_w > AppConfig.W: tx = mx + 200 
                ty = tooltip_y
                tip_bg = (40, 40, 45)
                draw.rectangle((tx, ty, tx+tip_w, ty+tip_h), fill=tip_bg, outline=self._apply_alpha(ColorConfig.UI_BORDER_ACTIVE, alpha, bg), width=1)
                t_y = ty + 10
                for l in lines:
                    draw.text((tx+10, t_y), l, font=self.font_xs, fill=(255,255,255))
                    t_y += 25

        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)