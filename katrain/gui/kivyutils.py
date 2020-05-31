import json
import random
import re

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import *
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
    OptionProperty,
    ObjectProperty,
)
from kivy.uix.behaviors import ToggleButtonBehavior, ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserLayout, FileChooserListLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


# --new
from kivymd.app import MDApp
from kivymd.uix.behaviors import RectangularRippleBehavior, CircularRippleBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import BasePressedButton, BaseFlatButton
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivy.core.text import Label as CoreLabel

from katrain.core.constants import GAME_TYPES, AI_STRATEGIES_RECOMMENDED_ORDER, PLAYER_HUMAN, PLAYER_AI
from katrain.core.lang import i18n

#

# --- new mixins
from katrain.gui.style import WHITE, DEFAULT_FONT


class BackgroundMixin(Widget):
    background_color = ListProperty([0, 0, 0, 0])
    background_radius = NumericProperty(0)
    outline_color = ListProperty([0, 0, 0, 0])
    outline_width = NumericProperty(1)


class LeftButtonBehavior(ButtonBehavior):  # stops buttons etc activating on right click
    def __init__(self, **kwargs):
        self.register_event_type("on_left_release")
        self.register_event_type("on_left_press")
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        return super().on_touch_down(touch)

    def on_release(self):
        if not self.last_touch or self.last_touch.button == "left":
            self.dispatch("on_left_release")
        return super().on_release()

    def on_press(self):
        if not self.last_touch or self.last_touch.button == "left":
            self.dispatch("on_left_press")
        return super().on_press()

    def on_left_release(self):
        pass

    def on_left_press(self):
        pass


# -- resizeable buttons
class SizedButton(
    LeftButtonBehavior, RectangularRippleBehavior, BasePressedButton, BaseFlatButton, BackgroundMixin
):  # avoid baserectangular for sizing
    text = StringProperty("")
    text_color = ListProperty(WHITE)
    text_size = ListProperty([100, 100])
    halign = OptionProperty("center", options=["left", "center", "right", "justify", "auto"])
    label = ObjectProperty(None)
    padding_x = NumericProperty(6)
    padding_y = NumericProperty(0)
    _font_size = NumericProperty(None)
    font_name = StringProperty(DEFAULT_FONT)


class AutoSizedButton(SizedButton):
    pass


class SizedRectangleButton(SizedButton):
    pass


class AutoSizedRectangleButton(AutoSizedButton):
    pass


class ToggleButtonMixin(ToggleButtonBehavior):
    inactive_outline_color = ListProperty([0.5, 0.5, 0.5, 0])
    active_outline_color = ListProperty([1, 1, 1, 0])
    inactive_background_color = ListProperty([0.5, 0.5, 0.5, 1])
    active_background_color = ListProperty([1, 1, 1, 1])

    @property
    def active(self):
        return self.state == "down"


class SizedToggleButton(ToggleButtonMixin, SizedButton):
    pass


class SizedRectangleToggleButton(ToggleButtonMixin, SizedRectangleButton):
    pass


class AutoSizedRectangleToggleButton(ToggleButtonMixin, AutoSizedRectangleButton):
    pass


class TransparentIconButton(CircularRippleBehavior, Button):
    icon_size = ListProperty([25, 25])
    icon = StringProperty("")


class PauseButton(CircularRippleBehavior, LeftButtonBehavior, Widget):
    active = BooleanProperty(True)
    active_line_color = ListProperty([0.5, 0.5, 0.8, 1])
    inactive_line_color = ListProperty([1, 1, 1, 1])
    active_fill_color = ListProperty([0.5, 0.5, 0.5, 1])
    inactive_fill_color = ListProperty([1, 1, 1, 0])
    line_width = NumericProperty(5)
    fill_color = ListProperty([0.5, 0.5, 0.5, 1])
    line_color = ListProperty([0.5, 0.5, 0.5, 1])
    min_size = NumericProperty(100)


# -- basic styles
class LightLabel(Label):
    pass


class StatsLabel(MDBoxLayout):
    text = StringProperty("")
    label = StringProperty("")
    color = ListProperty([1, 1, 1, 1])
    hidden = BooleanProperty(False)
    font_name = StringProperty(DEFAULT_FONT)


class MyNavigationDrawer(MDNavigationDrawer):  # in PR - closes NavDrawer on any outside click
    def on_touch_down(self, touch):
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.status == "opened" and self.close_on_click and not self.collide_point(touch.ox, touch.oy):
            self.set_state("close", animation=True)
            return True
        return super().on_touch_up(touch)


class CircleWithText(Widget):
    text = StringProperty("0")
    player = OptionProperty("B", options=["B", "W"])
    min_size = NumericProperty(50)


class BGBoxLayout(BoxLayout, BackgroundMixin):
    pass


# -- new gui elements


class I18NSpinner(Spinner):
    __events__ = ["on_select"]
    sync_height_frac = NumericProperty(1.0)
    value_refs = ListProperty()
    selected_index = NumericProperty(0)
    font_name = StringProperty(DEFAULT_FONT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_dropdown_props, pos=self.update_dropdown_props, value_refs=self.i18n_values)
        self.i18n_values()
        MDApp.get_running_app().bind(language=self.i18n_values)

    @property
    def selected(self):
        try:
            selected = self.selected_index
            return selected, self.value_refs[selected], self.values[selected]
        except (ValueError, IndexError):
            return 0, "", ""

    def on_text(self, _widget, text):
        try:
            new_index = self.values.index(text)
            if new_index != self.selected_index:
                self.selected_index = new_index
                self.dispatch("on_select")
        except (ValueError, IndexError):
            pass

    def on_select(self, *args):
        pass

    def select_key(self, key):
        try:
            ix = self.value_refs.index(key)
            self.text = self.values[ix]
        except (ValueError, IndexError):
            pass

    def i18n_values(self, *_args):
        if self.value_refs:
            self.values = [i18n._(ref) for ref in self.value_refs]
            self.text = self.values[self.selected_index]
            self.font_name = i18n.font_name
            self.update_dropdown_props()

    def update_dropdown_props(self, *largs):
        if not self.sync_height_frac:
            return
        dp = self._dropdown
        if not dp:
            return
        container = dp.container
        if not container:
            return
        h = self.height
        fsz = self.font_size
        for item in container.children[:]:
            item.height = h * self.sync_height_frac
            item.font_size = fsz
            item.font_name = self.font_name


class PlayerSetup(MDBoxLayout):
    player = OptionProperty("B", options=["B", "W"])
    mode = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player_subtype_ai.value_refs = AI_STRATEGIES_RECOMMENDED_ORDER
        self.player_subtype_human.value_refs = GAME_TYPES
        self.setup_options()

    def setup_options(self, *_args):
        if self.player_type.selected[1] == self.mode:
            return
        self.mode = self.player_type.selected[1]
        self.update_global_player_info()

    @property
    def player_type_dump(self):
        if self.mode == PLAYER_AI:
            return {"player_type": self.player_type.selected[1], "player_subtype": self.player_subtype_ai.selected[1]}
        else:
            return {
                "player_type": self.player_type.selected[1],
                "player_subtype": self.player_subtype_human.selected[1],
            }

    def update_widget(self, player_type, player_subtype):
        self.player_type.select_key(player_type)  # should trigger setup options
        if self.mode == PLAYER_AI:
            self.player_subtype_ai.select_key(player_subtype)  # should trigger setup options
        else:
            self.player_subtype_human.select_key(player_subtype)  # should trigger setup options

    def update_global_player_info(self):
        if self.parent and self.parent.update_global:
            katrain = MDApp.get_running_app().gui
            if katrain.game and katrain.game.current_node:
                katrain.update_player(self.player, **self.player_type_dump)


class PlayerSetupBlock(MDBoxLayout):
    players = ObjectProperty(None)
    black = ObjectProperty(None)
    white = ObjectProperty(None)
    update_global = BooleanProperty(False)
    INSTANCES = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.black = PlayerSetup(player="B")
        self.white = PlayerSetup(player="W")
        self.players = {"B": self.black, "W": self.white}
        self.add_widget(self.black)
        self.add_widget(self.white)
        PlayerSetupBlock.INSTANCES.append(self)

    def update_players(self, bw, player_info):  # update sub widget based on gui state change
        self.players[bw].update_widget(player_type=player_info.player_type, player_subtype=player_info.player_subtype)


class PlayerInfo(MDBoxLayout, BackgroundMixin):
    captures = NumericProperty(0)
    player = OptionProperty("B", options=["B", "W"])
    player_type = StringProperty("Player")
    player_subtype = StringProperty("")
    active = BooleanProperty(True)


class Timer(BGBoxLayout):
    state = ListProperty([30, 5, 1])


class AnalysisToggle(MDBoxLayout):
    text = StringProperty("")
    default_active = BooleanProperty(False)
    font_name = StringProperty(DEFAULT_FONT)

    def trigger_action(self, *args, **kwargs):
        return self.checkbox.trigger_action(*args, **kwargs)

    @property
    def active(self):
        return self.checkbox.active


class MainMenuItem(RectangularRippleBehavior, LeftButtonBehavior, MDBoxLayout, BackgroundMixin):
    __events__ = ["on_action"]
    icon = StringProperty("")
    text = StringProperty("")
    shortcut = StringProperty("")
    font_name = StringProperty(DEFAULT_FONT)

    def on_left_release(self):
        self.anim_complete()  # kill ripple
        MDApp.get_running_app().gui.nav_drawer.set_state("close")
        self.dispatch("on_action")

    def on_action(self):
        pass


class CollapsablePanelHeader(MDBoxLayout):
    pass


class CollapsablePanelTab(AutoSizedRectangleToggleButton):
    pass


class CollapsablePanel(MDBoxLayout):
    __events__ = ["on_option_state"]

    options = ListProperty([])
    options_height = NumericProperty(25)
    options_spacing = NumericProperty(6)
    option_labels = ListProperty([])
    option_active = ListProperty([])
    option_colors = ListProperty([])

    closed_label = StringProperty("Closed Panel")

    size_hint_y_open = NumericProperty(1)
    height_open = NumericProperty(None)

    state = OptionProperty("open", options=["open", "close"])
    close_icon = "img/Previous-5.png"
    open_icon = "img/Next-5.png"

    def __init__(self, **kwargs):
        self.header, self.contents, self.open_close_button = None, None, None
        self.option_buttons = []
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.bind(
            options=self.build_options,
            option_colors=self.build_options,
            options_height=self.build_options,
            option_active=self.build_options,
            options_spacing=self.build_options,
        )
        self.bind(state=self.build, size_hint_y_open=self.build, height_open=self.build)
        MDApp.get_running_app().bind(language=lambda *_: Clock.schedule_once(self.build_options, 0))
        self.build_options()

    def build_options(self, *args, **kwargs):
        self.header = CollapsablePanelHeader(
            height=self.options_height, size_hint_y=None, spacing=self.options_spacing, padding=[1, 0, 0, 0]
        )
        self.option_buttons = []
        option_labels = self.option_labels or [i18n._(f"tab:{opt}") for opt in self.options]
        for ix, (lbl, opt_col, active) in enumerate(zip(option_labels, self.option_colors, self.option_active)):
            button = CollapsablePanelTab(
                text=lbl,
                font_name=i18n.font_name,
                active_outline_color=opt_col,
                height=self.options_height,
                state="down" if active else "normal",
            )
            self.option_buttons.append(button)
            button.bind(state=lambda *_args, _ix=ix: self.trigger_select(_ix))
        self.open_close_button = TransparentIconButton(  # <<  / >> collapse button
            icon=self.open_close_icon(),
            icon_size=[0.5 * self.options_height, 0.5 * self.options_height],
            width=0.75 * self.options_height,
            size_hint_x=None,
            on_press=lambda *_args: self.set_state("toggle"),
        )
        self.bind(state=lambda *_args: self.open_close_button.setter("icon")(None, self.open_close_icon()))
        self.build()

    def build(self, *args, **kwargs):
        self.header.clear_widgets()
        if self.state == "open":
            for button in self.option_buttons:
                self.header.add_widget(button)
            self.header.add_widget(Label())  # spacer
            self.trigger_select(ix=None)
        else:
            self.header.add_widget(
                Label(
                    text=i18n._(self.closed_label), font_name=i18n.font_name, halign="right", height=self.options_height
                )
            )
        self.header.add_widget(self.open_close_button)

        super().clear_widgets()
        super().add_widget(self.header)
        height, size_hint_y = 1, None
        if self.state == "open" and self.contents:
            super().add_widget(self.contents)
            if self.height_open:
                height = self.height_open
            else:
                size_hint_y = self.size_hint_y_open
        else:
            height = self.header.height
        self.height, self.size_hint_y = height, size_hint_y

    def open_close_icon(self):
        return self.open_icon if self.state == "open" else self.close_icon

    def add_widget(self, widget, index=0, **_kwargs):
        if self.contents:
            raise ValueError("CollapsablePanel can only have one child")
        self.contents = widget
        self.build()

    def set_state(self, state="toggle"):
        if state == "toggle":
            state = "close" if self.state == "open" else "open"
        self.state = state
        self.build()
        if self.state == "open":
            self.trigger_select(ix=None)

    def trigger_select(self, ix):
        if ix is not None and self.option_buttons:
            self.option_active[ix] = self.option_buttons[ix].state == "down"
        if self.state == "open":
            self.dispatch("on_option_state", {opt: btn.active for opt, btn in zip(self.options, self.option_buttons)})
        return False

    def on_option_state(self, options):
        pass


class StatsBox(MDBoxLayout, BackgroundMixin):
    winrate = StringProperty("...")
    score = StringProperty("...")
    points_lost = NumericProperty(None, allownone=True)
    player = StringProperty("")


class ClickableLabel(LeftButtonBehavior, Label):
    pass


class ScrollableLabel(ScrollView, BackgroundMixin):
    __events__ = ["on_ref_press"]
    outline_color = ListProperty([0, 0, 0, 0])  # mixin not working for some reason
    text = StringProperty("")
    line_height = NumericProperty(1)
    markup = BooleanProperty(False)

    def on_ref_press(self, ref):
        pass


def draw_text(pos, text, font_name=None, **kw):
    label = CoreLabel(text=text, bold=True, font_name=font_name or i18n.font_name, **kw)  #
    label.refresh()
    Rectangle(
        texture=label.texture,
        pos=(pos[0] - label.texture.size[0] / 2, pos[1] - label.texture.size[1] / 2),
        size=label.texture.size,
    )


def draw_circle(pos, r, col):
    Color(*col)
    Ellipse(pos=(pos[0] - r, pos[1] - r), size=(2 * r, 2 * r))
