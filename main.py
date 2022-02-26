import os
import sys
import time
import moviepy.editor
import pygame
from blessed import Terminal
from PIL import Image, ImageOps
import cv2

term = Terminal()


HALF = '\N{LOWER HALF BLOCK}'


def image(im):
    im = ImageOps.fit(im, (term.width, term.height * 2))
    pixels = im.load()
    res = ''
    for y in range(im.size[1] // 2):
        for x in range(im.size[0]):
            # false positives, pycharm doesn't like this for some reason
            # noinspection PyUnresolvedReferences
            r, g, b = pixels[x, y * 2]
            # noinspection PyUnresolvedReferences
            r2, g2, b2 = pixels[x, y * 2 + 1]
            res += term.on_color_rgb(r, g, b) + term.color_rgb(r2, g2, b2) + HALF
    return res


def video(path):
    with term.cbreak(), term.hidden_cursor(), term.fullscreen():
        # get start time
        start = time.time()
        # variables
        frame_count = 1
        dropped_frames = 0
        # load video
        capture = cv2.VideoCapture(path)
        # get fps
        fps = capture.get(cv2.CAP_PROP_FPS)
        # load audio from video
        v = moviepy.editor.VideoFileClip(path)
        audio = v.audio
        audio.write_audiofile(path.split(".")[0] + ".wav")
        # play audio
        pygame.mixer.init()
        pygame.mixer.music.load(path.split(".")[0] + ".wav")
        pause = False
        first = True
        # main loop
        while capture.isOpened():
            # for pause/exit
            inp = term.inkey(timeout=0.01)
            # esc
            if inp == "\x1b" or inp == "q":
                break
            if inp == ' ':
                pause = not pause
                pygame.mixer.music.pause() if pause else pygame.mixer.music.unpause()
                print(term.home + term.move_y((term.height - 1) // 2))
                print(
                    term.black_on_white(
                        term.center(
                            'Paused. Press %s to unpause, or %s or %s to exit.' % (
                                term.italic(term.bold("Space")) + term.normal,
                                term.italic(term.bold("Escape")) + term.normal,
                                term.italic(term.bold("Q")) + term.normal
                            )
                        )
                    )
                )
            if not pause:
                if first:
                    pygame.mixer.music.play()
                    first = False
                ret, frame = capture.read()
                elapsed = time.time() - start
                expected_frame = int(elapsed * fps)
                if frame_count < expected_frame:
                    frame_count += 1
                    dropped_frames += 1
                    continue
                if not ret:
                    break
                frame_count += 1
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(img)
                sys.stdout.write(term.home + image(im))
                sys.stdout.write(
                    term.white_on_black +
                    "Elapsed time: {} | "
                    "Actual frame: {} | "
                    "Theoretical frame: {} | "
                    "Dropped frames: {} | "
                    "FPS: {}".format(
                        elapsed, frame_count - dropped_frames,
                        expected_frame, dropped_frames,
                        (frame_count - dropped_frames) / elapsed
                    )
                )
                sys.stdout.flush()

    capture.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop()


video(sys.argv[1])
