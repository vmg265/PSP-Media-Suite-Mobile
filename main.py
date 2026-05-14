"""
PSP Media Suite — Android Mobile Port
Built with KivyMD (Material Design) + Kivy
Supports system dark/light mode, portrait-first layout
"""

import os
import sys
import threading
import time
import shutil

# ── Kivy config BEFORE any kivy import ──────────────────────────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.config import Config
Config.set("graphics", "resizable", "1")
Config.set("kivy", "keyboard_mode", "systemanddock")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (
    StringProperty, BooleanProperty, ListProperty,
    NumericProperty, ObjectProperty, DictProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDList, TwoLineAvatarIconListItem, IconLeftWidget,
    ILeftBody, IRightBodyTouch,
)
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomsheet import MDListBottomSheet
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.chip import MDChip
from kivymd.uix.spinner import MDSpinner

# ── Optional heavy imports (graceful fallback for dev env) ───────────────────
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

try:
    import requests
    from io import BytesIO
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── KV Layout ────────────────────────────────────────────────────────────────
KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import MDApp kivymd.app.MDApp

<RootLayout>:
    orientation: "vertical"
    spacing: 0

    MDTopAppBar:
        id: toolbar
        title: "PSP Media Suite"
        elevation: 4
        left_action_items: [["usb", lambda x: app.scan_drives()]]
        right_action_items:
            [["refresh", lambda x: app.scan_drives()],
             ["dots-vertical", lambda x: app.show_menu()]]

    # Drive selector banner
    MDCard:
        id: drive_banner
        orientation: "horizontal"
        padding: dp(12), dp(8)
        spacing: dp(8)
        size_hint_y: None
        height: dp(48)
        elevation: 2
        radius: [0]

        MDIconButton:
            icon: "usb"
            theme_icon_color: "Custom"
            icon_color: app.accent_color
            pos_hint: {"center_y": .5}
            size_hint: None, None
            size: dp(36), dp(36)

        MDLabel:
            id: drive_label
            text: "No PSP drive detected"
            font_style: "Caption"
            theme_text_color: "Secondary"
            pos_hint: {"center_y": .5}

        MDChip:
            id: drive_chip
            text: "Scan"
            on_release: app.scan_drives()
            pos_hint: {"center_y": .5}
            size_hint: None, None
            height: dp(28)

    MDBottomNavigation:
        id: bottom_nav
        panel_color: app.surface_color
        selected_color_background: app.accent_color

        MDBottomNavigationItem:
            name: "music"
            text: "Music"
            icon: "music-note"
            on_tab_press: app.switch_tab("music")
            MusicTab:
                id: music_tab

        MDBottomNavigationItem:
            name: "video"
            text: "Video"
            icon: "video"
            on_tab_press: app.switch_tab("video")
            VideoTab:
                id: video_tab

        MDBottomNavigationItem:
            name: "playlist"
            text: "Playlist"
            icon: "playlist-music"
            on_tab_press: app.switch_tab("playlist")
            PlaylistTab:
                id: playlist_tab

        MDBottomNavigationItem:
            name: "queue"
            text: "Queue"
            icon: "tray-arrow-up"
            badge_icon: "numeric-0-circle"
            on_tab_press: app.switch_tab("queue")
            QueueTab:
                id: queue_tab


# ── Shared search bar used by Music + Video tabs ─────────────────────────────
<SearchBar@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(72)
    padding: dp(12), dp(4)
    spacing: dp(4)

    MDTextField:
        id: search_field
        hint_text: "Search YouTube or paste URL…"
        mode: "rectangle"
        icon_left: "magnify"
        on_text_validate: root.do_search(self.text)


# ── Music Tab ─────────────────────────────────────────────────────────────────
<MusicTab@BoxLayout>:
    orientation: "vertical"
    padding: 0
    spacing: 0

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(72)
        padding: dp(12), dp(4)

        MDTextField:
            id: music_search
            hint_text: "Search YouTube or paste URL…"
            mode: "rectangle"
            icon_left: "magnify"
            on_text_validate: app.search(self.text, "audio")

    BoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(44)
        padding: dp(12), dp(4)
        spacing: dp(8)

        MDFlatButton:
            text: "LOCAL FILE"
            on_release: app.add_local_file("audio")
            theme_text_color: "Custom"
            text_color: app.accent_color

        MDFlatButton:
            text: "MANAGE"
            on_release: app.open_file_manager("audio")
            theme_text_color: "Custom"
            text_color: app.accent_color

    MDProgressBar:
        id: music_progress
        value: 0
        color: app.accent_color
        size_hint_y: None
        height: dp(2)

    ResultsView:
        id: music_results
        media_type: "audio"


# ── Video Tab ─────────────────────────────────────────────────────────────────
<VideoTab@BoxLayout>:
    orientation: "vertical"
    padding: 0
    spacing: 0

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(72)
        padding: dp(12), dp(4)

        MDTextField:
            id: video_search
            hint_text: "Search YouTube or paste URL…"
            mode: "rectangle"
            icon_left: "magnify"
            on_text_validate: app.search(self.text, "video")

    BoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(44)
        padding: dp(12), dp(4)
        spacing: dp(8)

        MDFlatButton:
            text: "LOCAL FILE"
            on_release: app.add_local_file("video")
            theme_text_color: "Custom"
            text_color: app.accent_color

        MDFlatButton:
            text: "MANAGE"
            on_release: app.open_file_manager("video")
            theme_text_color: "Custom"
            text_color: app.accent_color

    MDProgressBar:
        id: video_progress
        value: 0
        color: app.accent_color
        size_hint_y: None
        height: dp(2)

    ResultsView:
        id: video_results
        media_type: "video"


# ── Playlist Tab ──────────────────────────────────────────────────────────────
<PlaylistTab@BoxLayout>:
    orientation: "vertical"
    padding: 0
    spacing: 0

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(72)
        padding: dp(12), dp(4)

        MDTextField:
            id: pl_search
            hint_text: "Search YouTube playlist URL…"
            mode: "rectangle"
            icon_left: "magnify"
            on_text_validate: app.search(self.text, "playlist")

    BoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(44)
        padding: dp(12), dp(4)

        MDFlatButton:
            text: "MANAGE PLAYLISTS"
            on_release: app.open_playlist_manager()
            theme_text_color: "Custom"
            text_color: app.accent_color

    MDProgressBar:
        id: pl_progress
        value: 0
        color: app.accent_color
        size_hint_y: None
        height: dp(2)

    ResultsView:
        id: pl_results
        media_type: "playlist"


# ── Queue Tab ─────────────────────────────────────────────────────────────────
<QueueTab@BoxLayout>:
    orientation: "vertical"
    padding: 0
    spacing: 0

    BoxLayout:
        size_hint_y: None
        height: dp(52)
        padding: dp(12), dp(8)
        spacing: dp(8)

        MDLabel:
            text: "Transfer Queue"
            font_style: "H6"
            theme_text_color: "Primary"

        MDFlatButton:
            text: "CLEAR ALL"
            on_release: app.clear_queue()
            theme_text_color: "Custom"
            text_color: [0.94, 0.27, 0.27, 1]
            size_hint_x: None
            width: dp(100)

    ScrollView:
        MDList:
            id: queue_list

    # Footer send button
    MDCard:
        size_hint_y: None
        height: dp(72)
        padding: dp(16), dp(8)
        elevation: 8
        radius: [0]

        BoxLayout:
            orientation: "vertical"
            spacing: dp(4)

            MDProgressBar:
                id: send_progress
                value: 0
                color: app.accent_color

            MDRaisedButton:
                id: send_btn
                text: "SEND QUEUE TO PSP"
                icon: "tray-arrow-up"
                md_bg_color: app.accent_color
                size_hint_x: 1
                on_release: app.process_queue()


# ── Result card (RecycleView row) ─────────────────────────────────────────────
<ResultCard>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(80)
    padding: dp(12), dp(8)
    spacing: dp(12)
    ripple_behavior: True
    elevation: 1
    radius: [dp(8)]

    # Thumbnail placeholder
    MDCard:
        size_hint: None, None
        size: dp(100), dp(60)
        radius: [dp(6)]
        md_bg_color: app.surface_color
        pos_hint: {"center_y": .5}

        MDLabel:
            text: root.thumb_icon
            font_style: "H5"
            halign: "center"
            valign: "center"

    BoxLayout:
        orientation: "vertical"
        spacing: dp(2)
        pos_hint: {"center_y": .5}

        MDLabel:
            text: root.title
            font_style: "Subtitle2"
            theme_text_color: "Primary"
            shorten: True
            shorten_from: "right"

        MDLabel:
            text: root.duration
            font_style: "Caption"
            theme_text_color: "Secondary"

    MDIconButton:
        icon: "plus-circle"
        theme_icon_color: "Custom"
        icon_color: app.accent_color
        pos_hint: {"center_y": .5}
        size_hint: None, None
        size: dp(44), dp(44)
        on_release: app.add_to_queue_from_result(root.result_data, root.media_type)


# ── ResultsView (RecycleView wrapper) ────────────────────────────────────────
<ResultsView>:
    viewclass: "ResultCard"
    media_type: "audio"

    RecycleBoxLayout:
        default_size: None, dp(80)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: "vertical"
        spacing: dp(4)
        padding: dp(8), dp(4)


# ── Queue item ────────────────────────────────────────────────────────────────
<QueueItem>:
    size_hint_y: None
    height: dp(72)

    IconLeftWidget:
        icon: root.media_icon

    _no_ripple_effect: True

    BoxLayout:
        orientation: "horizontal"
        size_hint: (1, None)
        height: dp(72)
        pos_hint: {"center_y": .5}

        MDLabel:
            text: root.status_icon
            size_hint: None, None
            size: dp(28), dp(28)
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: root.status_color
            pos_hint: {"center_y": .5}

        MDIconButton:
            icon: "close-circle"
            theme_icon_color: "Custom"
            icon_color: [0.6, 0.6, 0.6, 1]
            size_hint: None, None
            size: dp(40), dp(40)
            pos_hint: {"center_y": .5}
            on_release: app.remove_from_queue(root.item_id)
"""


# ── Data classes ──────────────────────────────────────────────────────────────

class ResultCard(RecycleDataViewBehavior, MDCard):
    title       = StringProperty("Unknown")
    duration    = StringProperty("")
    thumb_icon  = StringProperty("▶")
    media_type  = StringProperty("audio")
    result_data = DictProperty({})
    index       = NumericProperty(0)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)


class ResultsView(RecycleView):
    media_type = StringProperty("audio")


class QueueItem(TwoLineAvatarIconListItem):
    media_icon   = StringProperty("music-note")
    status_icon  = StringProperty("·")
    status_color = ListProperty([0.6, 0.6, 0.6, 1])
    item_id      = StringProperty("")


# ── Dialogs ───────────────────────────────────────────────────────────────────

class TextInputDialog(ModalView):
    """Simple single-field input dialog (replaces simpledialog)."""
    def __init__(self, title, hint, initial="", callback=None, **kw):
        super().__init__(size_hint=(0.9, None), height=dp(200), **kw)
        self.callback = callback
        layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        layout.add_widget(MDLabel(text=title, font_style="H6", size_hint_y=None, height=dp(36)))
        self.field = MDTextField(hint_text=hint, text=initial, mode="rectangle", size_hint_y=None, height=dp(56))
        layout.add_widget(self.field)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_row.add_widget(MDFlatButton(text="CANCEL", on_release=lambda x: self.dismiss()))
        btn_row.add_widget(MDRaisedButton(text="OK", on_release=self._confirm))
        layout.add_widget(btn_row)
        self.add_widget(layout)

    def _confirm(self, *_):
        if self.callback:
            self.callback(self.field.text.strip())
        self.dismiss()


class FileManagerDialog(ModalView):
    """Lists files on PSP drive for a given media type."""
    def __init__(self, app_ref, media_type, **kw):
        super().__init__(size_hint=(0.95, 0.85), **kw)
        self.app_ref    = app_ref
        self.media_type = media_type
        self._build()

    def _build(self):
        drive = self.app_ref._get_drive_path()
        folder = os.path.join(drive, "MUSIC" if self.media_type == "audio" else "VIDEO") if drive else ""
        exts   = (".mp3",".ogg",".opus",".m4a",".wav") if self.media_type == "audio" else (".mp4",".avi",".mkv",".mov")

        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(48))
        icon = "🎵" if self.media_type == "audio" else "🎬"
        hdr.add_widget(MDLabel(
            text=f"{icon}  {'Music' if self.media_type=='audio' else 'Video'} on PSP",
            font_style="H6"
        ))
        hdr.add_widget(MDIconButton(icon="close", on_release=lambda x: self.dismiss(),
                                     size_hint_x=None, width=dp(44)))
        layout.add_widget(hdr)

        # File list
        sv = ScrollView()
        self.file_list = MDList()
        sv.add_widget(self.file_list)
        layout.add_widget(sv)

        # Action buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_row.add_widget(MDFlatButton(text="RENAME", on_release=lambda x: self._rename()))
        btn_row.add_widget(MDFlatButton(text="DELETE", on_release=lambda x: self._delete(),
                                         theme_text_color="Custom",
                                         text_color=[0.94, 0.27, 0.27, 1]))
        layout.add_widget(btn_row)
        self.add_widget(layout)

        self._folder  = folder
        self._exts    = exts
        self._selected = None
        self._load_files()

    def _load_files(self):
        self.file_list.clear_widgets()
        if not os.path.isdir(self._folder):
            self.file_list.add_widget(MDLabel(text="Folder not found", padding=(dp(16), 0)))
            return
        for f in sorted(os.listdir(self._folder)):
            if f.lower().endswith(self._exts):
                item = TwoLineAvatarIconListItem(
                    text=f,
                    secondary_text=self._file_size(os.path.join(self._folder, f)),
                    on_release=lambda x, fn=f: self._select(fn)
                )
                item.add_widget(IconLeftWidget(icon="music-note" if self.media_type == "audio" else "video"))
                self.file_list.add_widget(item)

    def _file_size(self, path):
        try:
            kb = os.path.getsize(path) / 1024
            return f"{kb/1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        except:
            return ""

    def _select(self, fname):
        self._selected = fname
        Snackbar(text=f"Selected: {fname[:40]}").open()

    def _rename(self):
        if not self._selected:
            Snackbar(text="Select a file first").open()
            return
        old = self._selected
        dlg = TextInputDialog(
            title="Rename File",
            hint="New name (without extension)",
            initial=os.path.splitext(old)[0],
            callback=lambda new: self._do_rename(old, new)
        )
        dlg.open()

    def _do_rename(self, old, new_base):
        if not new_base:
            return
        ext = os.path.splitext(old)[1]
        new = new_base + ext
        try:
            os.rename(os.path.join(self._folder, old), os.path.join(self._folder, new))
            self.app_ref.write_log(f"Renamed: {old} → {new}")
            self._selected = None
            self._load_files()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()

    def _delete(self):
        if not self._selected:
            Snackbar(text="Select a file first").open()
            return
        fname = self._selected
        dlg = MDDialog(
            title="Delete File",
            text=f"Delete '{fname}'? This cannot be undone.",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=[0.94, 0.27, 0.27, 1],
                    on_release=lambda x: (self._do_delete(fname), dlg.dismiss())
                ),
            ]
        )
        dlg.open()

    def _do_delete(self, fname):
        try:
            os.remove(os.path.join(self._folder, fname))
            self.app_ref.write_log(f"Deleted: {fname}")
            self._selected = None
            self._load_files()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()


class PlaylistManagerDialog(ModalView):
    """Playlist creation / song management dialog."""
    def __init__(self, app_ref, **kw):
        super().__init__(size_hint=(0.95, 0.9), **kw)
        self.app_ref     = app_ref
        self._current_pl = None
        self._build()

    def _build(self):
        drive = self.app_ref._get_drive_path()
        if not drive:
            self.add_widget(MDLabel(text="No PSP drive connected", halign="center"))
            return

        self._music_dir = os.path.join(drive, "MUSIC")
        self._pl_dir    = os.path.join(drive, "PSP", "PLAYLIST", "MUSIC")
        os.makedirs(self._music_dir, exist_ok=True)
        os.makedirs(self._pl_dir,    exist_ok=True)

        outer = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        # Title bar
        hdr = BoxLayout(size_hint_y=None, height=dp(48))
        hdr.add_widget(MDLabel(text="🎶  Playlist Manager", font_style="H6"))
        hdr.add_widget(MDIconButton(icon="close", on_release=lambda x: self.dismiss(),
                                     size_hint_x=None, width=dp(44)))
        outer.add_widget(hdr)

        # Two-pane layout (stacked on mobile for readability)
        panes = BoxLayout(orientation="vertical", spacing=dp(8))

        # ── Left pane: playlist list ──────────────────────────────────────
        left = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(220), spacing=dp(4))
        left.add_widget(MDLabel(text="Playlists", font_style="Overline", size_hint_y=None, height=dp(20)))

        pl_sv = ScrollView()
        self.pl_list = MDList()
        pl_sv.add_widget(self.pl_list)
        left.add_widget(pl_sv)

        pl_btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        pl_btns.add_widget(MDFlatButton(text="+ NEW",    on_release=lambda x: self._new_pl()))
        pl_btns.add_widget(MDFlatButton(text="RENAME",   on_release=lambda x: self._rename_pl()))
        pl_btns.add_widget(MDFlatButton(text="DELETE",   on_release=lambda x: self._delete_pl(),
                                         theme_text_color="Custom",
                                         text_color=[0.94, 0.27, 0.27, 1]))
        left.add_widget(pl_btns)
        panes.add_widget(left)

        # ── Right pane: songs in playlist ─────────────────────────────────
        right = BoxLayout(orientation="vertical", spacing=dp(4))
        self.songs_title = MDLabel(text="← Select a playlist", font_style="Overline",
                                    size_hint_y=None, height=dp(20))
        right.add_widget(self.songs_title)

        song_sv = ScrollView()
        self.song_list = MDList()
        song_sv.add_widget(self.song_list)
        right.add_widget(song_sv)

        song_btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        song_btns.add_widget(MDFlatButton(text="+ ADD",    on_release=lambda x: self._add_songs()))
        song_btns.add_widget(MDFlatButton(text="REMOVE",   on_release=lambda x: self._remove_songs(),
                                           theme_text_color="Custom",
                                           text_color=[0.94, 0.27, 0.27, 1]))
        song_btns.add_widget(MDFlatButton(text="▲",        on_release=lambda x: self._move(-1)))
        song_btns.add_widget(MDFlatButton(text="▼",        on_release=lambda x: self._move(1)))
        right.add_widget(song_btns)
        panes.add_widget(right)

        outer.add_widget(panes)
        self.add_widget(outer)
        self._load_playlists()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _pl_path(self, name): return os.path.join(self._pl_dir, name + ".m3u8")

    def _read_pl(self, name):
        p = self._pl_path(name)
        if not os.path.exists(p): return []
        with open(p, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]

    def _write_pl(self, name, lines):
        with open(self._pl_path(name), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _song_display(self, raw): return os.path.basename(raw.replace("\\", "/"))

    def _load_playlists(self):
        self.pl_list.clear_widgets()
        try:
            for f in sorted(os.listdir(self._pl_dir)):
                if f.lower().endswith(".m3u8"):
                    name = os.path.splitext(f)[0]
                    item = TwoLineAvatarIconListItem(
                        text=name,
                        secondary_text=f"{len(self._read_pl(name))} songs",
                        on_release=lambda x, n=name: self._select_pl(n)
                    )
                    item.add_widget(IconLeftWidget(icon="playlist-music"))
                    self.pl_list.add_widget(item)
        except Exception as e:
            self.app_ref.write_log(f"Load playlists error: {e}")

    def _select_pl(self, name):
        self._current_pl = name
        self.songs_title.text = f"Songs in: {name}"
        self._load_songs()

    def _load_songs(self):
        self.song_list.clear_widgets()
        self._song_widgets = []
        for line in self._read_pl(self._current_pl):
            disp = self._song_display(line)
            item = TwoLineAvatarIconListItem(text=disp, secondary_text=line,
                                              on_release=lambda x, d=disp: self._select_song(d))
            item.add_widget(IconLeftWidget(icon="music-note"))
            self.song_list.add_widget(item)
            self._song_widgets.append(disp)
        self._sel_song = None

    def _select_song(self, disp):
        self._sel_song = disp
        Snackbar(text=f"Selected: {disp[:40]}").open()

    def _new_pl(self):
        TextInputDialog("New Playlist", "Playlist name", callback=self._do_new_pl).open()

    def _do_new_pl(self, name):
        if not name: return
        if os.path.exists(self._pl_path(name)):
            Snackbar(text="Playlist already exists").open(); return
        self._write_pl(name, [])
        self.app_ref.write_log(f"Created playlist: {name}")
        self._load_playlists()

    def _rename_pl(self):
        if not self._current_pl: Snackbar(text="Select a playlist first").open(); return
        TextInputDialog("Rename Playlist", "New name", initial=self._current_pl,
                        callback=self._do_rename_pl).open()

    def _do_rename_pl(self, new):
        if not new: return
        try:
            os.rename(self._pl_path(self._current_pl), self._pl_path(new))
            self.app_ref.write_log(f"Renamed: {self._current_pl} → {new}")
            self._current_pl = new
            self.songs_title.text = f"Songs in: {new}"
            self._load_playlists()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()

    def _delete_pl(self):
        if not self._current_pl: Snackbar(text="Select a playlist first").open(); return
        name = self._current_pl
        dlg = MDDialog(
            title="Delete Playlist",
            text=f"Delete '{name}'?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="DELETE", md_bg_color=[0.94, 0.27, 0.27, 1],
                                on_release=lambda x: (self._do_delete_pl(name), dlg.dismiss()))
            ]
        )
        dlg.open()

    def _do_delete_pl(self, name):
        try:
            os.remove(self._pl_path(name))
            self._current_pl = None
            self.songs_title.text = "← Select a playlist"
            self.song_list.clear_widgets()
            self._load_playlists()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()

    def _add_songs(self):
        if not self._current_pl: Snackbar(text="Select a playlist first").open(); return
        try:
            avail = [f for f in sorted(os.listdir(self._music_dir)) if f.lower().endswith(".mp3")]
        except: avail = []
        if not avail: Snackbar(text="No .mp3 files in PSP MUSIC folder").open(); return

        existing = {self._song_display(l).lower() for l in self._read_pl(self._current_pl)}
        to_pick  = [f for f in avail if f.lower() not in existing]

        sheet = MDListBottomSheet()
        for f in to_pick[:30]:  # cap at 30 for readability
            sheet.add_item(f, lambda x, fn=f: self._do_add_song(fn), icon="music-note")
        sheet.open()

    def _do_add_song(self, fname):
        lines = self._read_pl(self._current_pl)
        lines.append(f"\\MUSIC\\{fname}")
        self._write_pl(self._current_pl, lines)
        self.app_ref.write_log(f"Added to {self._current_pl}: {fname}")
        self._load_songs()

    def _remove_songs(self):
        if not self._sel_song: Snackbar(text="Tap a song to select it first").open(); return
        lines    = self._read_pl(self._current_pl)
        new_lines = [l for l in lines if self._song_display(l) != self._sel_song]
        self._write_pl(self._current_pl, new_lines)
        self.app_ref.write_log(f"Removed {self._sel_song} from {self._current_pl}")
        self._sel_song = None
        self._load_songs()

    def _move(self, direction):
        if not self._sel_song: return
        lines = self._read_pl(self._current_pl)
        for i, l in enumerate(lines):
            if self._song_display(l) == self._sel_song:
                j = i + direction
                if 0 <= j < len(lines):
                    lines[i], lines[j] = lines[j], lines[i]
                    self._write_pl(self._current_pl, lines)
                    self._load_songs()
                    return


# ── Root layout ───────────────────────────────────────────────────────────────
class RootLayout(BoxLayout):
    pass


# ── Main App ──────────────────────────────────────────────────────────────────
class PSPMediaSuiteApp(MDApp):
    accent_color  = ListProperty([0.23, 0.51, 0.96, 1])   # Material Blue 500
    surface_color = ListProperty([0.12, 0.12, 0.12, 1])   # Dark surface

    def __init__(self, **kw):
        super().__init__(**kw)
        self.title        = "PSP Media Suite"
        self.drives       = {}
        self.queue        = []         # list[dict]
        self.queue_widgets= {}         # item_id → QueueItem widget
        self.is_processing= False
        self._log_lines   = []
        self._active_tab  = "music"

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _detect_system_theme(self):
        """
        On Android, query the system dark-mode flag.
        Falls back to 'Dark' on all other platforms (PSP app is media-heavy → dark preferred).
        """
        if platform == "android":
            try:
                from android.runnable import run_on_ui_thread  # type: ignore
                from jnius import autoclass                      # type: ignore
                Context     = autoclass("android.content.Context")
                Resources   = autoclass("android.content.res.Resources")
                Configuration = autoclass("android.content.res.Configuration")
                ctx = autoclass("org.kivy.android.PythonActivity").mActivity
                ui_mode = ctx.getResources().getConfiguration().uiMode
                night_mode = ui_mode & Configuration.UI_MODE_NIGHT_MASK
                if night_mode == Configuration.UI_MODE_NIGHT_YES:
                    return "Dark"
                else:
                    return "Light"
            except Exception:
                return "Dark"
        return "Dark"  # desktop dev default

    def _apply_material_colors(self, mode):
        """Set KivyMD theme palette based on dark/light and system accent."""
        self.theme_cls.theme_style = mode
        if platform == "android":
            try:
                from jnius import autoclass  # type: ignore
                TypedValue   = autoclass("android.util.TypedValue")
                R_attr       = autoclass("android.R$attr")
                ctx          = autoclass("org.kivy.android.PythonActivity").mActivity
                tv           = TypedValue()
                ctx.getTheme().resolveAttribute(R_attr.colorPrimary, tv, True)
                color_int    = tv.data
                r = ((color_int >> 16) & 0xFF) / 255.0
                g = ((color_int >>  8) & 0xFF) / 255.0
                b = ( color_int        & 0xFF) / 255.0
                self.accent_color = [r, g, b, 1]
            except Exception:
                pass  # keep default blue

        # Match surface_color to MD theme
        if mode == "Dark":
            self.theme_cls.primary_palette = "Blue"
            self.theme_cls.accent_palette  = "Orange"
            self.surface_color = [0.12, 0.12, 0.12, 1]
        else:
            self.theme_cls.primary_palette = "Blue"
            self.theme_cls.accent_palette  = "Orange"
            self.surface_color = [0.96, 0.96, 0.96, 1]

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def build(self):
        mode = self._detect_system_theme()
        self._apply_material_colors(mode)

        Builder.load_string(KV)
        self.root_layout = RootLayout()
        return self.root_layout

    def on_start(self):
        Clock.schedule_once(lambda dt: self.scan_drives(), 0.5)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def write_log(self, msg):
        self._log_lines.append(msg)
        print(f"[PSP] {msg}")   # visible in logcat on Android

    def show_snack(self, msg):
        Snackbar(text=msg[:80]).open()

    def switch_tab(self, tab):
        self._active_tab = tab

    def _get_drive_path(self):
        if not self.drives:
            return None
        # Return first found drive
        return next(iter(self.drives.values()))

    def _update_drive_label(self):
        lbl = self.root_layout.ids.drive_label
        if self.drives:
            name = next(iter(self.drives))
            lbl.text = f"PSP drive: {name}"
        else:
            lbl.text = "No PSP drive detected — connect PSP in USB mode"

    # ── Drive detection ───────────────────────────────────────────────────────
    def scan_drives(self):
        self.drives = {}
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        found = {}
        if PSUTIL_AVAILABLE:
            try:
                for part in psutil.disk_partitions(all=True):
                    try:
                        if os.path.exists(os.path.join(part.mountpoint, "PSP")):
                            found[part.mountpoint] = part.mountpoint
                    except: pass
            except: pass

        # Android: check common mount points
        for base in ["/storage", "/mnt/media_rw", "/run/media", "/media"]:
            if not os.path.exists(base): continue
            try:
                for entry in os.listdir(base):
                    p = os.path.join(base, entry)
                    if os.path.isdir(p) and os.path.exists(os.path.join(p, "PSP")):
                        found[entry] = p
            except: pass

        self.drives = found
        Clock.schedule_once(lambda dt: self._post_scan(), 0)

    def _post_scan(self):
        self._update_drive_label()
        if self.drives:
            self.show_snack(f"PSP drive found: {next(iter(self.drives))}")
            self.write_log(f"Drive detected: {next(iter(self.drives.values()))}")
        else:
            self.show_snack("No PSP drive found. Connect PSP in USB mode.")

    # ── Search ────────────────────────────────────────────────────────────────
    def search(self, query, media_type):
        if not query or not query.strip():
            return
        self.write_log(f"Searching [{media_type}]: {query[:50]}")
        self._set_tab_progress(media_type, 15)
        threading.Thread(target=self._search_thread, args=(query, media_type), daemon=True).start()

    def _search_thread(self, q, media_type):
        if not YT_DLP_AVAILABLE:
            Clock.schedule_once(lambda dt: self.show_snack("yt-dlp not available"), 0)
            return
        opts = {"quiet": True, "extract_flat": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                if q.startswith("http"):
                    info = ydl.extract_info(q, download=False)
                    entries = [info] if info.get("_type") != "playlist" else list(info.get("entries", [info]))
                else:
                    info    = ydl.extract_info(f"ytsearch20:{q}", download=False)
                    entries = list(info.get("entries", [info]))
            Clock.schedule_once(lambda dt: self._render_results(entries, media_type), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_snack(f"Search failed: {str(e)[:60]}"), 0)
            Clock.schedule_once(lambda dt: self._set_tab_progress(media_type, 0), 0)

    def _render_results(self, entries, media_type):
        self._set_tab_progress(media_type, 80)
        rv = self._get_results_view(media_type)
        if not rv: return

        icons = {"audio": "🎵", "video": "🎬", "playlist": "🎶"}
        data  = []
        for r in entries:
            if not r: continue
            url = r.get("url") or r.get("webpage_url") or r.get("original_url", "")
            if not url:
                vid_id = str(r.get("id", ""))
                url = f"https://www.youtube.com/watch?v={vid_id}"
            data.append({
                "title":       r.get("title", "Unknown")[:65],
                "duration":    self._fmt_time(r.get("duration", 0)),
                "thumb_icon":  icons.get(media_type, "▶"),
                "media_type":  media_type,
                "result_data": {
                    "title":          r.get("title", "Unknown"),
                    "url":            url,
                    "formatted_time": self._fmt_time(r.get("duration", 0)),
                    "raw_thumb_url":  r.get("thumbnail"),
                    "pil_image":      None,
                    "is_local":       False,
                },
            })
        rv.data = data
        self._set_tab_progress(media_type, 100)
        Clock.schedule_once(lambda dt: self._set_tab_progress(media_type, 0), 1.5)

    def _get_results_view(self, media_type):
        mapping = {
            "audio":    "music_results",
            "video":    "video_results",
            "playlist": "pl_results",
        }
        key = mapping.get(media_type)
        return self.root_layout.ids.get(key) if key else None

    def _set_tab_progress(self, media_type, val):
        mapping = {
            "audio":    "music_progress",
            "video":    "video_progress",
            "playlist": "pl_progress",
        }
        key = mapping.get(media_type)
        if key and key in self.root_layout.ids:
            self.root_layout.ids[key].value = val

    def _fmt_time(self, seconds):
        if not seconds: return ""
        try:
            s = int(seconds); m, s = divmod(s, 60); h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        except: return ""

    # ── Queue ─────────────────────────────────────────────────────────────────
    def add_to_queue_from_result(self, result_data, media_type):
        self.add_to_queue(result_data, media_type)

    def add_to_queue(self, item, media_type):
        icons = {"audio": "music-note", "video": "video", "playlist": "playlist-music"}
        item_id = f"{media_type}_{len(self.queue)}_{time.time():.0f}"

        q_data = {
            "id":       item_id,
            "status":   "pending",
            "type":     media_type,
            "url":      item.get("url", ""),
            "title":    item.get("title", "Unknown"),
            "thumb":    item.get("raw_thumb_url"),
            "is_local": item.get("is_local", False),
        }
        self.queue.append(q_data)

        wi = QueueItem(
            text=item.get("title", "Unknown")[:50],
            secondary_text=f"{media_type.upper()} · {item.get('formatted_time','') or 'Local'}",
            media_icon=icons.get(media_type, "music-note"),
            item_id=item_id,
        )
        wi.add_widget(IconLeftWidget(icon=icons.get(media_type, "music-note")))
        self.queue_widgets[item_id] = wi

        queue_list = self.root_layout.ids.queue_list
        queue_list.add_widget(wi)

        # Update badge on bottom nav
        self._update_queue_badge()
        self.write_log(f"Queued: {item.get('title','?')[:40]}")
        self.show_snack(f"Added to queue: {item.get('title','?')[:30]}")

    def remove_from_queue(self, item_id):
        if self.is_processing: return
        self.queue = [q for q in self.queue if q["id"] != item_id]
        if item_id in self.queue_widgets:
            self.root_layout.ids.queue_list.remove_widget(self.queue_widgets.pop(item_id))
        self._update_queue_badge()

    def clear_queue(self):
        if self.is_processing: return
        for w in list(self.queue_widgets.values()):
            self.root_layout.ids.queue_list.remove_widget(w)
        self.queue.clear()
        self.queue_widgets.clear()
        self._update_queue_badge()

    def _update_queue_badge(self):
        count = len(self.queue)
        # KivyMD badge on the Queue tab icon
        try:
            bn = self.root_layout.ids.bottom_nav
            for item in bn.children:
                if hasattr(item, "name") and item.name == "queue":
                    item.badge_icon = f"numeric-{min(count,9)}-circle" if count else ""
                    break
        except: pass

    def _set_queue_item_status(self, item_id, status):
        colors = {
            "pending":    [0.6, 0.6, 0.6, 1],
            "processing": [0.96, 0.62, 0.04, 1],
            "success":    [0.13, 0.77, 0.37, 1],
            "error":      [0.94, 0.27, 0.27, 1],
        }
        icons = {"pending":"·", "processing":"⏳", "success":"✓", "error":"✕"}
        if item_id in self.queue_widgets:
            wi = self.queue_widgets[item_id]
            wi.status_icon  = icons.get(status, "·")
            wi.status_color = colors.get(status, [0.6, 0.6, 0.6, 1])

    # ── Local file picker ─────────────────────────────────────────────────────
    def add_local_file(self, media_type):
        if platform == "android":
            self._android_file_picker(media_type)
        else:
            # Desktop fallback
            try:
                import tkinter as tk
                from tkinter import filedialog
                _root = tk.Tk(); _root.withdraw()
                ft = ([("Audio Files", "*.mp3 *.ogg *.opus *.m4a *.wav")]
                      if media_type == "audio" else [("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm")])
                paths = filedialog.askopenfilenames(filetypes=ft)
                _root.destroy()
                for path in paths:
                    name = os.path.splitext(os.path.basename(path))[0]
                    self.add_to_queue({"title": f"(Local) {name}", "url": path,
                                       "is_local": True, "pil_image": None,
                                       "formatted_time": "Local", "raw_thumb_url": None}, media_type)
            except Exception as e:
                self.show_snack(f"File picker error: {e}")

    def _android_file_picker(self, media_type):
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            from android import activity                                       # type: ignore
            from jnius import autoclass                                        # type: ignore

            request_permissions([Permission.READ_EXTERNAL_STORAGE])

            Intent         = autoclass("android.content.Intent")
            intent         = Intent(Intent.ACTION_GET_CONTENT)
            mime           = "audio/*" if media_type == "audio" else "video/*"
            intent.setType(mime)
            intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)

            def on_activity_result(request_code, result_code, data):
                RESULT_OK = -1
                if result_code != RESULT_OK or data is None:
                    return
                clip = data.getClipData()
                if clip:
                    for i in range(clip.getItemCount()):
                        uri  = clip.getItemAt(i).getUri()
                        path = str(uri)
                        name = path.split("/")[-1].split("%2F")[-1]
                        self.add_to_queue({"title": f"(Local) {name}", "url": path,
                                           "is_local": True, "pil_image": None,
                                           "formatted_time": "Local", "raw_thumb_url": None}, media_type)
                elif data.getData():
                    uri  = data.getData()
                    path = str(uri)
                    name = path.split("/")[-1]
                    self.add_to_queue({"title": f"(Local) {name}", "url": path,
                                       "is_local": True, "pil_image": None,
                                       "formatted_time": "Local", "raw_thumb_url": None}, media_type)

            activity.bind(on_activity_result=on_activity_result)
            activity.start_activity(intent, 1001)
        except Exception as e:
            self.show_snack(f"File picker error: {str(e)[:60]}")

    # ── File manager + Playlist manager ──────────────────────────────────────
    def open_file_manager(self, media_type):
        if not self._get_drive_path():
            self.show_snack("Connect your PSP first"); return
        FileManagerDialog(self, media_type).open()

    def open_playlist_manager(self):
        if not self._get_drive_path():
            self.show_snack("Connect your PSP first"); return
        PlaylistManagerDialog(self).open()

    # ── Queue processing ──────────────────────────────────────────────────────
    def process_queue(self):
        if self.is_processing:
            self.show_snack("Already processing…"); return
        if not self.queue:
            self.show_snack("Queue is empty"); return
        if not self._get_drive_path():
            self.show_snack("No PSP drive connected"); return
        self.is_processing = True
        self.root_layout.ids.send_btn.text = "PROCESSING…"
        self.root_layout.ids.send_btn.disabled = True
        threading.Thread(target=self._process_thread,
                         args=(self._get_drive_path(),), daemon=True).start()

    def _process_thread(self, drive_path):
        ff   = self._ffmpeg_path()
        total = len(self.queue)
        for i, item in enumerate(self.queue):
            if item["status"] == "success": continue
            prog = int((i / total) * 100)
            Clock.schedule_once(lambda dt, v=prog: self._set_send_progress(v), 0)
            Clock.schedule_once(lambda dt, id=item["id"]: self._set_queue_item_status(id, "processing"), 0)
            self.write_log(f"Processing: {item['title'][:40]}")

            try:
                if item["type"] == "audio":
                    self._process_audio(item, drive_path, ff)
                elif item["type"] == "video":
                    self._process_video(item, drive_path, ff)
                elif item["type"] == "playlist":
                    self._process_playlist(item, drive_path, ff)
                item["status"] = "success"
                Clock.schedule_once(lambda dt, id=item["id"]: self._set_queue_item_status(id, "success"), 0)
            except Exception as e:
                self.write_log(f"Error: {e}")
                item["status"] = "error"
                Clock.schedule_once(lambda dt, id=item["id"]: self._set_queue_item_status(id, "error"), 0)

            self._cleanup_temp()

        Clock.schedule_once(lambda dt: self._on_process_done(), 0)

    def _process_audio(self, item, drive_path, ff):
        target = os.path.join(drive_path, "MUSIC")
        os.makedirs(target, exist_ok=True)
        clean = self._clean_name(item["title"])

        if item.get("is_local"):
            import subprocess
            subprocess.run([ff, "-y", "-i", item["url"],
                            "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", "temp_raw.mp3"],
                           check=True)
        else:
            opts = {
                "format": "bestaudio/best", "ffmpeg_location": ff,
                "outtmpl": "temp_raw.%(ext)s", "nopart": True, "continuedl": False,
                "postprocessors": [{"key": "FFmpegExtractAudio",
                                    "preferredcodec": "mp3", "preferredquality": "192"}],
                "postprocessor_args": ["-map_metadata", "-1"],
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(item["url"], download=True)
            self._embed_thumbnail(info, item.get("thumb"))

        if MUTAGEN_AVAILABLE and os.path.exists("temp_raw.mp3"):
            audio = MP3("temp_raw.mp3", ID3=ID3)
            if audio.tags is None: audio.add_tags()
            else: audio.tags.clear()
            audio.tags.add(TIT2(encoding=3, text=item["title"]))
            audio.tags.add(TPE1(encoding=3, text="YouTube Audio" if not item.get("is_local") else "Local"))
            audio.tags.add(TALB(encoding=3, text="PSP Media Suite"))
            if os.path.exists("cover.jpg"):
                with open("cover.jpg", "rb") as cf:
                    audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cf.read()))
            audio.save(v2_version=3, v1=2)

        if os.path.exists("temp_raw.mp3"):
            shutil.move("temp_raw.mp3", os.path.join(target, clean + ".mp3"))

    def _process_video(self, item, drive_path, ff):
        import subprocess
        target = os.path.join(drive_path, "VIDEO")
        os.makedirs(target, exist_ok=True)
        clean = self._clean_name(item["title"])

        if item.get("is_local"):
            subprocess.run([ff, "-y", "-i", item["url"],
                            "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
                            "-pix_fmt", "yuv420p", "-vf", "scale=480:272",
                            "-b:v", "768k", "-c:a", "aac", "-b:a", "128k",
                            "-ar", "48000", "temp.mp4"], check=True)
        else:
            opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "ffmpeg_location": ff, "outtmpl": "temp_raw.%(ext)s",
                "nopart": True, "continuedl": False,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(item["url"], download=True)
            raw = next((f for f in os.listdir(".") if f.startswith("temp_raw.") and not f.endswith(".mp3")), None)
            if raw:
                subprocess.run([ff, "-y", "-i", raw,
                                "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
                                "-pix_fmt", "yuv420p", "-vf", "scale=480:272",
                                "-b:v", "768k", "-c:a", "aac", "-b:a", "128k",
                                "-ar", "48000", "temp.mp4"], check=True)
            self._save_thumbnail(info, item.get("thumb"), os.path.join(target, clean + ".thm"))

        if os.path.exists("temp.mp4"):
            shutil.move("temp.mp4", os.path.join(target, clean + ".mp4"))

    def _process_playlist(self, item, drive_path, ff):
        target   = os.path.join(drive_path, "MUSIC")
        pl_dir   = os.path.join(drive_path, "PSP", "PLAYLIST", "MUSIC")
        os.makedirs(target, exist_ok=True); os.makedirs(pl_dir, exist_ok=True)
        clean_pl = self._clean_name(item["title"])
        m3u8     = []

        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            info    = ydl.extract_info(item["url"], download=False)
            entries = info.get("entries", [info])

        for entry in entries:
            if not entry: continue
            e_url   = entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
            e_title = entry.get("title", "Track")
            clean_e = self._clean_name(e_title)
            self.write_log(f"  ↳ {e_title[:30]}")
            opts = {
                "format": "bestaudio/best", "ffmpeg_location": ff,
                "outtmpl": "temp_raw.%(ext)s", "nopart": True, "continuedl": False,
                "postprocessors": [{"key": "FFmpegExtractAudio",
                                    "preferredcodec": "mp3", "preferredquality": "192"}],
                "postprocessor_args": ["-map_metadata", "-1"],
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl2:
                    einfo = ydl2.extract_info(e_url, download=True)
                self._embed_thumbnail(einfo, entry.get("thumbnail"))
                if MUTAGEN_AVAILABLE and os.path.exists("temp_raw.mp3"):
                    audio = MP3("temp_raw.mp3", ID3=ID3)
                    if audio.tags is None: audio.add_tags()
                    else: audio.tags.clear()
                    audio.tags.add(TIT2(encoding=3, text=e_title))
                    audio.tags.add(TPE1(encoding=3, text="YouTube Audio"))
                    audio.tags.add(TALB(encoding=3, text=item["title"]))
                    if os.path.exists("cover.jpg"):
                        with open("cover.jpg", "rb") as cf:
                            audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cf.read()))
                    audio.save(v2_version=3, v1=2)
                if os.path.exists("temp_raw.mp3"):
                    shutil.move("temp_raw.mp3", os.path.join(target, clean_e + ".mp3"))
                    m3u8.append(f"\\MUSIC\\{clean_e}.mp3")
            except Exception as e:
                self.write_log(f"  ✕ {e_title[:20]}: {str(e)[:40]}")
            self._cleanup_temp()

        if m3u8:
            with open(os.path.join(pl_dir, clean_pl + ".m3u8"), "w", encoding="utf-8") as f:
                f.write("\n".join(m3u8))

    # ── Thumbnail helpers ─────────────────────────────────────────────────────
    def _embed_thumbnail(self, info_dict, fallback_url):
        if not PIL_AVAILABLE or not REQUESTS_AVAILABLE: return
        img = self._get_best_thumbnail(info_dict, fallback_url)
        if not img: return
        try:
            w, h = img.size; s = min(w, h)
            img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))
            img = img.resize((600, 600), Image.Resampling.LANCZOS)
            img.convert("RGB").save("cover.jpg", "JPEG", quality=85)
        except: pass

    def _save_thumbnail(self, info_dict, fallback_url, out_path):
        if not PIL_AVAILABLE or not REQUESTS_AVAILABLE: return
        img = self._get_best_thumbnail(info_dict, fallback_url)
        if not img: return
        try:
            w, h = img.size; ratio = 160/120
            if w/h > ratio:
                nw = int(ratio*h); img = img.crop(((w-nw)//2, 0, (w+nw)//2, h))
            else:
                nh = int(w/ratio); img = img.crop((0, (h-nh)//2, w, (h+nh)//2))
            img.resize((160, 120), Image.Resampling.LANCZOS).convert("RGB").save(out_path, "JPEG")
        except: pass

    def _get_best_thumbnail(self, info_dict, fallback_url):
        if not REQUESTS_AVAILABLE: return None
        urls = []
        if info_dict:
            for t in reversed(info_dict.get("thumbnails", [])):
                if t.get("url"): urls.append(t["url"])
            if info_dict.get("thumbnail"): urls.append(info_dict["thumbnail"])
        if fallback_url: urls.append(fallback_url)
        from io import BytesIO
        for u in urls:
            if not u.startswith("http"): continue
            try:
                r = requests.get(u, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)); img.verify()
                    return Image.open(BytesIO(r.content))
            except: pass
        return None

    # ── Misc helpers ──────────────────────────────────────────────────────────
    def _clean_name(self, title):
        base = os.path.splitext(title)[0]
        return "".join(c for c in base if c.isalnum() or c in " .-_")[:100]

    def _ffmpeg_path(self):
        # On Android, ffmpeg must be bundled or available via PATH
        if platform == "android":
            # Buildozer recipe bundles ffmpeg to app dir
            app_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(app_dir, "ffmpeg"),
                "/data/data/com.vmg265.pspmediasuite/files/app/ffmpeg",
                "ffmpeg",
            ]
        else:
            candidates = ["ffmpeg", "./ffmpeg", "./ffmpeg.exe"]
        for c in candidates:
            if os.path.exists(c) or c == "ffmpeg": return c
        return "ffmpeg"

    def _cleanup_temp(self):
        for f in os.listdir("."):
            if f.startswith("temp.") or f.startswith("temp_raw.") or f in ("temp_thumb.jpg", "cover.jpg"):
                try: os.remove(f)
                except: pass

    def _set_send_progress(self, val):
        self.root_layout.ids.send_progress.value = val

    def _on_process_done(self):
        self.is_processing = False
        self.root_layout.ids.send_btn.text     = "SEND QUEUE TO PSP"
        self.root_layout.ids.send_btn.disabled = False
        self._set_send_progress(100)
        Clock.schedule_once(lambda dt: self._set_send_progress(0), 2)
        self.write_log("✔ All done!")
        Snackbar(text="All done! Check queue for statuses.").open()

    # ── Menu / About ─────────────────────────────────────────────────────────
    def show_menu(self):
        import webbrowser
        sheet = MDListBottomSheet()
        sheet.add_item("⭐  GitHub",         lambda x: webbrowser.open("https://github.com/vmg265/PSP-Media-Suite"), icon="github")
        sheet.add_item("☕  Buy me a tea",   lambda x: webbrowser.open("https://rzp.io/rzp/pFrhgY8"), icon="coffee")
        sheet.add_item("🔧  Troubleshooter", lambda x: self._show_troubleshooter(), icon="wrench")
        sheet.add_item("About v1.6",         lambda x: self._show_about(), icon="information")
        sheet.open()

    def _show_about(self):
        dlg = MDDialog(
            title="PSP Media Suite",
            text="by vmg265  ·  v1.6\n\nDownload YouTube audio & video,\ntransfer directly to your PSP.",
            buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: dlg.dismiss())]
        )
        dlg.open()

    def _show_troubleshooter(self):
        from kivy.uix.popup import Popup
        ts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "troubleshooter_box.txt")
        content = ""
        if os.path.exists(ts_path):
            try:
                with open(ts_path, "r", encoding="utf-8") as f: content = f.read()
            except: content = "Could not read troubleshooter file."
        else:
            content = "troubleshooter_box.txt not found."

        sv = ScrollView()
        lbl = MDLabel(text=content, size_hint_y=None, padding=(dp(12), dp(12)))
        lbl.bind(texture_size=lbl.setter("size"))
        sv.add_widget(lbl)
        popup = Popup(title="Troubleshooter", content=sv, size_hint=(0.95, 0.85))
        popup.open()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PSPMediaSuiteApp().run()
