class Time : 
    houre = 0
    minuts =0
    seconds = 0

def fromSeconds(seconds) : 
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    time = Time()
    time.houres = h
    time.minuts = m 
    time.seconds = s
    return time

def fromFrames(frames, fps=24) :
    fps = float (fps)
    frames = float(frames)

    seconds = frames/fps
    return fromSeconds(seconds)

