from .. import log
import functools

MISSING_NOTE_ON_ERROR = 'Note off {0.note}:{0.channel} without note on'


class NoteCounter:
    def __init__(self):
        self.notes = {}

    def note_on(self, port, message):
        note = port.name, message.channel, message.note
        count = self.notes.get(note, 0)
        self.notes[note] = count + 1

    def note_off(self, port, message):
        note = port.name, message.channel, message.note
        count = self.notes.get(note, 0)
        if count > 1:
            self.notes[note] = count - 1
        elif count == 1:
            del self.notes[note]
        else:
            log.error(MISSING_NOTE_ON_ERROR.format(message))

    def combine(self, level=2):
        """Combines away n levels of a note counter."""
        result = {}
        for note, value in note_counter.items():
            note = note[level:]
            result[note] = result.get(note, 0) + value

        return result


def counter_callbacks(note_on, note_off=None):
    """
    Count the notes that are being held down into a dictionary.

    A note is represented by a triple:
        (port.name, message.channel, message.note)

    The note_counter dictionary maps notes to positive integer counts.

    Arguments:
        note_on, note_off: these are callback functions which expect to get
            two parameters: note, note_counter.

    """
    note_counter = NoteCounter()
    note_off = note_off or note_on

    @functools.wraps(note_on)
    def on(port, message):
        note_counter.note_on(port, message)
        note_on(note, note_counter)

    @functools.wraps(note_off)
    def off(port, message):
        note_counter.note_off(port, message)
        note_off(note, note_counter)

    return {'note_on': on, 'note_off': off}
