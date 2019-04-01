# -*- coding: utf-8 -*-

import datetime
import glob
import os
import subprocess as spr
import sys
import time
import sqlite3


try:
    input = raw_input
except NameError:
    pass


APP_NAME = 'PomoP: Poor man Pomodoro'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def write_finish_page(start, stop):
    import tempfile
    _, name = tempfile.mkstemp()
    name = name + '-pomop.html'

    # clean up old tmp files
    tempdir = os.path.dirname(name)

    for fn in glob.glob(os.path.join(tempdir, '*-pomop.html')):
        print("Found {}".format(fn))
        if fn != name:
            print("Removing {}".format(fn))
            os.remove(fn)

    html = """<html><body style="background: #696969; color:tan;"><h1>DONE POMODORO</h1>
    <h2>Start at: {}</h2>
    <h2>End at: {}</h2>
    </body></html>""".format(
        start.strftime("%Y-%m-%d %H:%M:%S"),
        stop.strftime("%Y-%m-%d %H:%M:%S")
    )
    with open(name, 'w') as fd:
        fd.write(html)

    import webbrowser
    webbrowser.open("file:///{}".format(name))


def _generate_sound_file(filename='noise.wav'):
    RATE = 44100

    def get_note(note, length=None):
        import struct
        from math import sin, pi

        if length is None:
            length = int(RATE / 4)

        wv_data = b""
        for i in range(0, length):
            max_vol = 2 ** 15 - 1.0
            raw = round(max_vol * sin(i * 2 * pi * note / RATE))
            wv_data += struct.pack('h', raw)
            wv_data += struct.pack('h', raw)
        return wv_data

    import wave

    noise_output = wave.open(filename, 'wb')
    noise_output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))

    C4 = 261.63
    D4 = 293.66
    E4 = 329.63
    wv_data = b"".join([get_note(n) for n in [C4, D4, E4]])

    noise_output.writeframes(wv_data)

    noise_output.close()


def play_sound(end=False):
    dirname = os.path.expanduser("~/.local/share/pomop")
    try:
        os.mkdir(dirname)
    except Exception:
        pass

    filepath = os.path.join(dirname, 'sound.wav')
    _generate_sound_file(filepath)

    try:
        if sys.platform == 'darwin':
            spr.call(["afplay", filepath])
            if end:
                spr.call(['say', 'time up, move away from computer, now!'])
        elif 'win' in sys.platform:
            spr.call(["start", "wmplayer", filepath])
        else:
            # Linux or other non-tested platform such as BSD*
            try:
                spr.call(["aplay", filepath])
            except Exception:
                spr.call(["xdg-open", filepath])

    except Exception as e:
        print("Play sound error", e)


def send_notification(messages):
    if isinstance(messages, str):
        messages = [messages]

    assert isinstance(messages, list)

    try:
        spr.call(['notify-send',
                  '--app-name', 'POMODORO',
                  '--icon', 'dialog-information',
                  ] + messages)
    except OSError:
        # notify-send not installed, skip
        pass


def notify_start(start, sound=True, browser=True):
    start_msg = 'Start new Pomodoro!'

    if sound:
        play_sound()
    send_notification(start_msg)


def notify_end(start, end, sound=True, browser=True):
    start_str = start.strftime("%H:%M:%S")
    duration = (end - start).total_seconds() // 60
    end_msg = 'POMO: {0:.0f} minute passed.\tFrom {1}'.format(
        duration, start_str
    )

    send_notification(end_msg)

    if sound:
        play_sound(end=True)
    if browser:
        write_finish_page(start, end)


def cli():
    import argparse
    argp = argparse.ArgumentParser()
    argp.add_argument('-l', '--length',
                      help='Length in minutes of this pomodoro',
                      type=int,
                      default=25)

    argp.add_argument('-S', '--nosound',
                      help='Turn off sound notification',
                      action='store_true',
                      )

    argp.add_argument('-B', '--nobrowser',
                      help='Turn off browser-open notification',
                      action='store_true')

    argp.add_argument('--list',
                      action='store_true',
                      help='Show last 10 pomodoros')

    argp.add_argument('target', nargs='?', help='Target of the pomodoro', type=str)

    dbpath = os.path.expanduser('~/.pomop.db')

    conn = sqlite3.connect(dbpath)
    conn.execute('CREATE TABLE IF NOT EXISTS pomodoros (start DATETIME, stop DATETIME, task TEXT)')  # NOQA
    conn.commit()

    args = argp.parse_args()

    if args.list:
        for r in conn.execute('SELECT * from pomodoros ORDER BY start DESC LIMIT 10;'):
            print(*r)
        conn.close()
        exit(0)

    length = args.length
    sound_ntf = not args.nosound
    browser_ntf = not args.nobrowser

    ONE_MINUTE_IN_SEC = 60

    start = datetime.datetime.now()
    notify_start(start, sound=sound_ntf, browser=browser_ntf)
    print('Pomop started at {}'.format(start))

    for minute in range(length, 0, -1):
        print("{}: working on {} - remaining {} minutes".format(APP_NAME, args.target, minute))
        time.sleep(ONE_MINUTE_IN_SEC)
        clear_screen()

    end = datetime.datetime.now()

    notify_end(start=start, end=end, sound=sound_ntf, browser=browser_ntf)
    print('Pomop finished at {}'.format(end))

    if args.target:
        done = args.target
    else:
        done = input('What have you done in this session? ')

    conn.execute('INSERT INTO pomodoros VALUES (?, ?, ?)', (start, end, done))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    cli()
