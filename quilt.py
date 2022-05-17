def run(frame, button_map):
    t = 0
    while True:
        for i in range(192):
            for j in range(32):
                frame.set(i, j, frame.pack(
                    ((i + t) ^ (j + 128)) & 0xff,
                    ((i + 128) ^ (j + t)) & 0xff,
                    ((i + t) ^ (j + t)) & 0xff
                ))
        frame.send()
        t = (t + 1) & 0xff
