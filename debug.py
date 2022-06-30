import gc

def mem(*args):
    pass

if hasattr(gc, 'mem_free'):
    def mem(label):
        gc.collect()
        print(label, gc.mem_free())
