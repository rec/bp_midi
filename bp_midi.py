import mido, queue
from bibliopixel.animation import matrix


class MidiAnimation(matrix.BaseMatrixAnim):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.queue = queue.Queue()
        self.loop = threading.Thread(self._midi_loop, daemon=True)
        self.loop.start()

        for t in self.MESSAGE_TYPES:
            assert hasattr(self, t), 'MidiAnimation has no callback for ' + t


    def cleanup(self, clean_layout=True):
        self.loop.stop()

    def _midi_loop(self):
        for msg in mido.ports.MultiPort(mido.get_input_names()):
            (msg.type in self.MESSAGE_TYPES) and self.queue.put(msg)

    def step(self, amt=1):
        while not queue.empty():
            msg = queue.get()
            getattr(self, msg.type)(msg)


class WX7Animation(MidiAnimation):
    MESSAGE_TYPES = 'note_on', 'control_change'

    def __init__(self, *args, lowest_note=0, highest_note=127, **kwds):
        self.lowest_note = lowest_note
        note_range = highest_note - lowest_note + 1
        ratio = self.height / self.range
        self.note_map = [int(ratio * i) for i in range(note_range)]
        self.note_map.append(self.highest_note)

        self.note_x = -1
        super().__init__(*args, **kwds)

    def note_on(self, msg):
        if not msg.velocity:
            return
        self.note_x = (self.note_x + 1) % self.width
        self.note_y = self.note_map[msg.note]
        for y in range(self.height):
            self.layout.setRGB(self.note_x, y, *COLORS.black)

        self._redraw(msg.velocity)

    def control_change(self, msg):
        self.note_x >= 0 and self._redraw(msg.value)

    def _redraw(self, color):
        self.layout.setRGB(self.note_x, self.note_y, *HUE_360[2 * color])
