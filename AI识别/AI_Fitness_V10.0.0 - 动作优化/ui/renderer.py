"""
UI 总控制器 (Facade)
统一对外暴露接口，内部调用 Skeleton/Visuals/Widgets 子渲染器。
"""
from ui.skeleton import SkeletonRenderer
from ui.visuals import VisualFeedbackRenderer
from ui.widgets import WidgetRenderer

class UIRenderer:
    def __init__(self):
        self.skeleton = SkeletonRenderer()
        self.visuals = VisualFeedbackRenderer()
        self.widgets = WidgetRenderer()

    # --- Forwarding Methods ---
    def draw_skeleton(self, img, pts, is_avatar=False):
        self.skeleton.draw(img, pts, is_avatar)

    def draw_visuals(self, img, commands):
        self.visuals.draw_commands(img, commands)

    def draw_all_text_layers(self, img, mode, count, fps, menu, h_str, typing, msg, msg_col, errs, bad, vid, paused):
        self.widgets.draw_all_layers(img, mode, count, fps, menu, h_str, typing, msg, msg_col, errs, bad, vid, paused)

    def draw_video_bar(self, img, prog, paused):
        self.widgets.draw_video_bar(img, prog, paused)

    def draw_tuning_modal(self, img, mode, params, idx, is_open):
        self.widgets.draw_tuning_modal(img, mode, params, idx, is_open)

    def update_hover(self, x, y, menu_open, num=4, modal_open=False):
        self.widgets.update_hover(x, y, menu_open, num, modal_open)

    def hit_test(self, x, y, modal_open=False):
        return self.widgets.hit_test(x, y, modal_open)

    @property
    def hit_boxes(self):
        return self.widgets.hit_boxes
        
    @property
    def modal_anim_val(self):
        return self.widgets.modal_anim_val
        
    @modal_anim_val.setter
    def modal_anim_val(self, value):
        self.widgets.modal_anim_val = value