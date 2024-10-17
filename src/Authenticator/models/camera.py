"""
 Copyright © 2024 Bardia Moshiri <fakeshell@bardia.tech>

 This file is part of Authenticator.

 Authenticator is free software: you can redistribute it and/or
 modify it under the terms of the GNU General Public License as published
 by the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Authenticator is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Authenticator. If not, see <http://www.gnu.org/licenses/>.
"""

import gi
import tempfile
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, GLib, GObject, Gdk

Gst.init(None)

class GstCamera(Gtk.Window):
    __gsignals__ = {
        'picture-taken': (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, parent_widget):
        Gtk.Window.__init__(self, title="Camera")
        self.set_modal(True)

        # find the top level to get focus
        toplevel = parent_widget.get_toplevel()
        if toplevel.is_toplevel():
            self.set_transient_for(toplevel)

        self.set_keep_above(True)
        self.connect("destroy", self.on_window_closed)
        self.overlay = Gtk.Overlay()
        self.add(self.overlay)
        self.button = Gtk.Button(label="Take Picture")
        self.button.connect("clicked", self.on_take_picture)
        self.button.set_valign(Gtk.Align.END)
        self.button.set_halign(Gtk.Align.CENTER)
        self.button.set_margin_bottom(10)
        self.video_widget = Gtk.Box()
        self.overlay.add(self.video_widget)
        self.overlay.add_overlay(self.button)
        self.set_default_size(640, 480)

        self.pipeline = Gst.parse_launch(
            "droidcamsrc camera_device=0 mode=2 ! tee name=t "
            "t. ! queue ! video/x-raw, width=1920, height=1080 ! videoconvert ! "
            "videoflip video-direction=auto ! gtksink name=sink "
            "t. ! queue ! videoconvert ! videoflip video-direction=auto ! jpegenc ! fakesink name=pic_sink"
        )
        self.sink = self.pipeline.get_by_name("sink")
        self.pic_sink = self.pipeline.get_by_name("pic_sink")
        sink_widget = self.sink.get_property("widget")
        self.video_widget.pack_start(sink_widget, True, True, 0)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_take_picture(self, button):
        sample = self.pic_sink.get_property("last-sample")
        if sample:
            buffer = sample.get_buffer()
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    temp_file.write(map_info.data)
                    print(f"Picture saved to: {temp_file.name}")
                buffer.unmap(map_info)
                self.emit('picture-taken', temp_file.name)
                self.close()

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.close()

    def on_window_closed(self, *args):
        self.pipeline.set_state(Gst.State.NULL)
        self.destroy()
