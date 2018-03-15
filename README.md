# Prequel Memes Generator

## Dependencies
Without video editing:
- python3
- docopt

With video editing:
- imagemagick
- wand
- moviepy

## Usage
To find a pattern in the movies, run:
```sh
python3 prequel_extractor --pattern PATTERN
```

If the user already purchased a leagal version of the movies, by running the
following command, a sequence of frames of the movie will be generated:
```sh
python3 prequel_extractor --pattern PATTERN --to-jpg
```
