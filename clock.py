import ccapi
import cctime
import ccui

FRAME_CONSTRUCTORS = {
    'mpv': lambda: __import__('mpv_frame').MpvFrame(192, 32, 30),
    'sdl': lambda: __import__('sdl_frame').SdlFrame(192, 32, 30),
}


def run(frame):
    cctime.enable_rtc()
    # data = ccapi.fetch()
    data = ccapi.load_file('climateclock.json')
    cv = frame.pack(*data.config.display.deadline.primary)
    carbon_module = data.module_dict['carbon_deadline_1']

    symbol_label = frame.new_label('CO₂ H₂O CH₄  é å Î ç Ç', 'kairon-10', cv)
    f = 0
    while True:
        text = ccui.format_deadline_module(carbon_module)
        carbon_label = frame.new_label(text, 'kairon-10', cv)
        f += 1
        count_label = frame.new_label('%08d' % f, 'kairon-10', cv)
        frame.paste(0, 1, carbon_label)
        frame.paste(0, 11, symbol_label)
        frame.paste(0, 21, count_label)
        frame.send()

if __name__ == '__main__':
    import sys
    try:
        frame_constructor = FRAME_CONSTRUCTORS[sys.argv[1]]
    except:
        print(f'Usage: {sys.argv[0]} <frame-type>')
        print()
        constructors = ', '.join(FRAME_CONSTRUCTORS)
        print(f'<frame-type> is one of: {constructors}')
        sys.exit(1)
    run(frame_constructor())
