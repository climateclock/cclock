import sys

FRAME_CONSTRUCTORS = {
    'mpv': lambda: __import__('mpv_frame').MpvFrame(192, 32, 30),
    'sdl': lambda: __import__('sdl_frame').SdlFrame(192, 32, 30),
}

def play(frame):
    t = 0
    while True:
        for i in range(192):
            for j in range(32):
                frame.set(i, j, (
                    ((i + t) ^ (j + 128)) & 0xff,
                    ((i + 128) ^ (j + t)) & 0xff,
                    ((i + t) ^ (j + t)) & 0xff
                ))
        frame.send()
        t = (t + 1) & 0xff

if __name__ == '__main__':
    try:
        frame_constructor = FRAME_CONSTRUCTORS[sys.argv[1]]
    except:
        print(f'Usage: {sys.argv[0]} <frame-type>')
        print()
        constructors = ', '.join(FRAME_CONSTRUCTORS)
        print(f'<frame-type> is one of: {constructors}')
        sys.exit(1)
    play(frame_constructor())
