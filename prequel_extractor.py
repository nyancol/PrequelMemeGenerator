from docopt import docopt
import argparse
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

version = 1.0
help_msg = """PrequelExtractor
Usage:
prequel_extractor --pattern PATTERN [--to-jpg]

Options:
-h, --help      Show this screen.
--version       Show version.

-p, --pattern   A pattern to find.
--to-jpg        Generates an image including the masked subtitles
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

    def __str__(self):
        return self._begin + ' ' + ''.join(self._lines)


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


def replace_letters(subtitle, pattern):
    substitute = '█'
    text = list('\n'.join(subtitle))
    text_squares = [' '] * len(text)
    pattern = list(pattern)
    i = 0

    while pattern:
        if text[i].lower() not in ['\n', ' ', pattern[0]]:
            text[i] = ' '
            text_squares[i] = substitute
        if text[i].lower() == pattern[0]:
            del pattern[0]
        i += 1

    for j in range(i, len(text)):
        text[i] = ' '
        text_squares[i] = substitute

    for i, c in enumerate(text):
        if c == '\n':
            text_squares[i] = c

    return (''.join(text), ''.join(text_squares))


def add_subtitle(clip, subtitle, pattern):
    text, text_squares = replace_letters(subtitle, pattern)
    text = (TextClip(text, fontsize=50,
                         font="Arial", color="white", stroke_color="black", stroke_width=2)
                 .margin(bottom=15, opacity=0)
                 .set_position(("center","bottom")))
    text_squares = (TextClip(text_squares, fontsize=50,
                         font="Arial", color="black")
                 .margin(bottom=15, opacity=0)
                 .set_position(("center","bottom")))

    return (CompositeVideoClip([clip, text])
            .set_duration(clip.duration))



def main():
    args = docopt(help_msg, version="Prequel Extractor " + str(version))

    sources = ['1.The.Phantom.Menace.srt', '2.Attack.of.the.Clones.srt', '3.Revenge.of.the.Sith.srt']
    movies = ['1.The.Phantom.Menace.mp4', '2.Attack.of.the.Clones.mp4', '3.Revenge.of.the.Sith.mp4']

    subtitles = [decode(s) for s in sources]
    res = [search(s, args['PATTERN']) for s in subtitles]
    for i, movie in enumerate(res):
        if len(movie):
            print("In " + movies[i] + ": ")
            for j, sub in enumerate(movie):
                print(sub.begin, sub.end, sub.lines)
                if args['--to-jpg']:
                    clip = VideoFileClip(movies[i])
                    current_clip = clip.subclip(sub.begin, sub.end)
                    current_clip = add_subtitle(current_clip, sub.lines, args['PATTERN'])
                    # current_clip.write_gif('test' + str(j) + '.gif', fps=15)
                    current_clip.write_images_sequence('frame%03d.png', fps=3)
            print()

main()
