import mido, queue, threading
from bibliopixel.animation import matrix
from bibliopixel.colors import COLORS, conversions


class MidiAnimation(matrix.BaseMatrixAnim):
    def __init__(self, *args, ports=None, **kwds):
        super().__init__(*args, **kwds)
        ports = mido.get_input_names() if ports is None else ports
        ports = [mido.open_input(p) for p in ports]
        self.port = mido.ports.MultiPort(ports)
        self.queue = queue.Queue()
        self.loop = threading.Thread(target=self._midi_loop, daemon=True)
        self.loop.start()

        for t in self.MESSAGE_TYPES:
            assert hasattr(self, t), 'MidiAnimation has no callback for ' + t

    def cleanup(self, clean_layout=True):
        self.loop = None

    def _midi_loop(self):
        for msg in self.port:
            (msg.type in self.MESSAGE_TYPES) and self.queue.put(msg)

    def step(self, amt=1):
        while not self.queue.empty():
            msg = self.queue.get()
            try:
                getattr(self, msg.type)(msg)
            except Exception as e:
                print(e)


class WX7Animation(MidiAnimation):
    MESSAGE_TYPES = 'note_on', 'control_change'

    def __init__(self, *args, lowest_note=0, highest_note=127, **kwds):
        super().__init__(*args, **kwds)
        self.lowest_note = lowest_note
        note_range = highest_note - lowest_note + 1
        ratio = self.height / note_range
        self.note_map = [lowest_note + int(ratio * i) for i in range(note_range)]
        self.note_map.append(highest_note)

        self.note_x = -1

    def note_on(self, msg):
        if not msg.velocity:
            return
        self.note_x = (self.note_x + 1) % self.width
        note = msg.note - self.lowest_note
        self.note_y = self.note_map[max(0, min(len(self.note_map) - 1, note))]
        for y in range(self.height):
            self.layout.setRGB(self.note_x, y, *COLORS.black)

        self._redraw(msg.velocity)

    def control_change(self, msg):
        self.note_x >= 0 and self._redraw(msg.value)

    def _redraw(self, color):
        c = conversions.HUE_360[2 * color]
        self.layout.setRGB(self.note_x, self.note_y, *c)
