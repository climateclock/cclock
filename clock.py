import ccapi
import cctime
import ccui

def run(frame):
    cctime.enable_rtc()
    # data = ccapi.fetch()
    data = ccapi.load_file('cache/climateclock.json')
    cv = frame.pack(*data.config.display.deadline.primary)
    carbon_module = data.module_dict['carbon_deadline_1']
    lifeline_modules = [m for m in data.modules if m.flavor == 'lifeline']
    l = 0
    while True:
        ccui.render_deadline_module(frame, 0, carbon_module, cv)
        ccui.render_lifeline_module(frame, 16, lifeline_modules[l], cv)
        frame.send()
