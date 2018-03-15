from docopt import docopt

from moviepy.editor import CompositeVideoClip, concatenate_videoclips
from moviepy.editor import ImageClip, VideoFileClip, TextClip

from wand.color import Color
from wand.display import display
from wand.drawing import Drawing
from wand.image import Image

import argparse

version = 1.0
help_msg = """PrequelExtractor
Usage:
prequel_extractor --pattern PATTERN [--to-jpg]

Options:
-h, --help      Show this screen.
--version       Show version.

-p, --pattern   A pattern to find.
--to-jpg        Generates an image including the masked subtitles.
"""

class Subtitle:
    def __init__(self):
        self._lines = []

    def set_id(self, line):
        try:
            self._id = int(line)
        except ValueError:
            print("Shoud be an id: ", line)

    def set_time(self, line):
        self._begin, _, self._end = line.replace(',', '.').split(' ')
        # Removing '\n'
        self._end = self._end[:-1]

    def set_line(self, line):
        # Removing '\n\
        self._lines.append(line[:-1])

    def search(self, pattern):
        pattern = list(pattern)
        text = list(''.join(self._lines).lower())
        while text and pattern:
            if text[0] == pattern[0]:
                del text[0]
                del pattern[0]
            else:
                del text[0]
        return len(pattern) == 0

    begin = property(fget=lambda self: self._begin)
    end = property(fget=lambda self: self._end)
    lines = property(fget=lambda self: self._lines)

    def __iter__(self):
        self._index = 0
        self._setters = [self.set_id, self.set_time, self.set_line]
        return self

    def __next__(self):
        if self._index < 3:
            self._index += 1
        return self._setters[self._index - 1]


def decode(subtitles_source):
    subtitles = []
    current = iter(Subtitle())
    with open(subtitles_source, 'r') as f:
        for l in f:
            if l == '\n':
                subtitles.append(current)
                current = iter(Subtitle())
            else:
                next(current)(l)
    return subtitles


def search(subtitles, pattern):
    res = []
    for sub in subtitles:
        if sub.search(pattern):
            res.append(sub)
    return res


def draw_letter(draw, x, y, char):
    letter_width = 40
    draw.text(x, y, char)
    return draw


def draw_scribble(draw, x, y, l, scribble):
    letter_width = 40
    x_offset = -5
    y_offset = -40
    scribble.save(filename="test.png")
    draw.composite('add', x+x_offset, y+y_offset, 40, 50, scribble)
    return draw


def letter_width(c):
    return 40


def line_width(line):
    return sum([letter_width(c) for c in line])


def add_scribbles(clip, width, height, lines, pattern):
    pattern = list(pattern)
    with Drawing() as draw:
        with Image(filename='./scribble_square.png') as scribble_img:
            with Image(width=width, height=height, background=Color("NONE")) \
                    as scribble_layer:
                y = 3 * height // 4
                for l in lines:
                    x = width // 2 - line_width(l) // 2
                    for c in l:
                        if c == ' ':
                            x += letter_width(c)
                            continue
                        elif pattern and pattern[0] != c.lower():
                            draw = draw_scribble(draw, x, y, c, scribble_img)
                        elif pattern and pattern[0] == c.lower():
                            del pattern[0]
                        elif not pattern:
                            draw = draw_scribble(draw, x, y, c, scribble_img)
                        x += letter_width(c)
                    y = y + 100
                draw(scribble_layer)
                scribble_layer.save(filename="output2.png")
    scribble_image = ImageClip("./output2.png")
    return (CompositeVideoClip([clip, scribble_image])
            .set_duration(clip.duration))


def add_subtitle(clip, width, height, lines):
    with Drawing() as draw:
        draw.font_size = 40
        draw.fill_color = Color("white")
        with Image(width=width, height=height, background=Color("NONE")) \
                as text_layer:
            y = 3 * height // 4
            for l in lines:
                x = width // 2 - line_width(l) // 2
                for c in l:
                    draw = draw_letter(draw, x, y, c)
                    x += letter_width(c)
                y = y + 100
            draw(text_layer)
            text_layer.save(filename="output.png")
    subtitle_image = ImageClip("./output.png")
    return (CompositeVideoClip([clip, subtitle_image])
            .set_duration(clip.duration))


def main():
    args = docopt(help_msg, version="Prequel Extractor " + str(version))
    width, height = 1920, 816

    sources = ['1.The.Phantom.Menace.srt',
               '2.Attack.of.the.Clones.srt',
               '3.Revenge.of.the.Sith.srt']

    movies = ['1.The.Phantom.Menace.mp4',
              '2.Attack.of.the.Clones.mp4',
              '3.Revenge.of.the.Sith.mp4']

    subtitles = [decode(s) for s in sources]
    res = [search(s, args['PATTERN']) for s in subtitles]
    for i, movie in enumerate(res):
        if len(movie):
            print("In " + movies[i] + ": ")
            for j, sub in enumerate(movie):
                print(sub.begin, sub.end, sub.lines)
                if args['--to-jpg']:
                    clip = VideoFileClip(movies[i]).subclip(sub.begin, sub.end)
                    clip = add_subtitle(clip, width, height, sub.lines)
                    clip = add_scribbles(clip, width, height, sub.lines, args['PATTERN'])
                    # clip.write_gif('test' + str(j) + '.gif', fps=15)
                    clip.write_images_sequence('frame-' + str(i) + '-' + str(j) + '-%03d.png', fps=1)

main()
