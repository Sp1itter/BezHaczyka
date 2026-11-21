"""Demo: concrete dictionary target + promotion signal -> short YouTube evidence."""
import argparse
from concurrent.futures import Future
from copy import deepcopy
from threading import Thread
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
from urllib.parse import urlsplit

URL = re.compile(r'https?://[^\s<>"“”]+|(?<![\w@/])(?:[\w-]+\.)+[^\W\d_]{2,}(?:[/?#][^\s<>"“”]*)?', re.I)
VIDEO_ID = re.compile(r'[A-Za-z0-9_-]{11}\Z')

# Domyślne wejście bez plików. Można przekazać własne obiekty do scan/start_background.
DEFAULT_CONFIG = {
    'language': 'pl', 'queries': ['XTB link partnerski', 'XTB partnerem odcinka', 'XTB kod polecający', 'bossa współpraca'],
    'signals': ['gwarantowany zysk', 'zysk bez ryzyka', 'pewny zysk', 'gwarantowana stopa zwrotu',
                'zarabiaj automatycznie', 'link partnerski', 'link afiliacyjny', 'kod polecający',
                'kod promocyjny', 'bonus za rejestrację', 'partnerem odcinka', 'partnerem kanału',
                'partnerem dzisiejszego', 'sponsorem odcinka', 'we współpracy z'],
    'exclude': {'title': [], 'description': [], 'transcript': []},
    'limit': 5, 'results_per_query': 8, 'max_candidates': 30,
    'max_clip_seconds': 30, 'max_clips': 2, 'max_comments': 10,
}
DEFAULT_DICTIONARY = [
    {'id': 'xtb', 'type': 'organization', 'value': 'XTB', 'aliases': ['XTB S.A.', 'iks te be', 'X T B']},
    {'id': 'bos', 'type': 'organization', 'value': 'Dom Maklerski Banku Ochrony Środowiska', 'aliases': ['DM BOŚ', 'Bossa']},
    {'id': 'xtb-domain', 'type': 'domain', 'value': 'xtb.com'},
    {'id': 'bossa-domain', 'type': 'domain', 'value': 'bossa.pl'},
]


def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def host(value):
    try:
        name = urlsplit(value if '://' in value else 'https://' + value).hostname
        return name.rstrip('.').encode('idna').decode('ascii').lower() if name else ''
    except (ValueError, UnicodeError):
        return ''


def find_targets(text, dictionary):
    """Only concrete agents/organizations/domains. Generic keywords never admit a film."""
    hits, seen = [], set()
    for entry in dictionary:
        if entry['type'] == 'keyword':
            continue
        for value in [entry['value'], *entry.get('aliases', [])]:
            if entry['type'] == 'domain':
                domain = host(value)
                occurrences = [m for m in URL.finditer(text) if domain and
                               (host(m.group().rstrip('.,;!)]}')) == domain or
                                host(m.group().rstrip('.,;!)]}')).endswith('.' + domain))]
            else:
                pattern = r'(?<!\w)' + r'\s+'.join(re.escape(w) for w in value.split()) + r'(?!\w)'
                occurrences = re.finditer(pattern, text, re.I)
            for match in occurrences:
                key = (entry['id'], match.start(), match.end())
                if key in seen:
                    continue
                seen.add(key)
                hits.append({'type': entry['type'], 'name': entry['value'],
                             'value': match.group().rstrip('.,;!)]}') if entry['type'] == 'domain' else match.group(),
                             'start': match.start(), 'end': match.end()})
    return hits


def signals_in(text, config):
    text = normalize(text)
    return [s for s in config['signals'] if re.search(r'(?<!\w)' + re.escape(normalize(s)) + r'(?!\w)', text)]


@lru_cache(maxsize=1)
def language_factory():
    from langdetect import DetectorFactory
    from langdetect.detector_factory import PROFILES_DIRECTORY
    factory = DetectorFactory()
    factory.load_json_profile([p.read_text('utf-8') for p in sorted(Path(PROFILES_DIRECTORY).iterdir()) if p.is_file()])
    factory.set_seed(0)
    return factory


def is_language(text, language):
    """Check bounded samples across the FULL text, never just a possibly misleading intro."""
    from langdetect.lang_detect_exception import LangDetectException
    text = ' '.join(re.findall(r'[^\W\d_]+', URL.sub(' ', text)))
    if sum(c.isalpha() for c in text) < 80 or len(text.split()) < 12:
        return False
    starts = [0] if len(text) <= 1500 else [0, max(0, len(text)//2-750), len(text)-1500]
    for start in starts:
        detector = language_factory().create()
        detector.append(text[start:start+1500])
        try:
            scores = detector.get_probabilities()
        except LangDetectException:
            return False
        if not scores or scores[0].lang != language or scores[0].prob < .95:
            return False
    return True


def evidence(text, field, dictionary, config):
    items, seen = [], set()
    for hit in find_targets(text, dictionary):
        key = (hit['type'], hit['name'])
        if key in seen:
            continue
        quote = text[max(0, hit['start']-160):hit['end']+160]
        signals = signals_in(quote, config)
        if signals:
            seen.add(key)
            items.append({'field': field, 'type': hit['type'], 'target': hit['name'],
                          'quote': quote, 'signals': signals,
                          **({'url': hit['value']} if hit['type'] == 'domain' else {})})
    return items[:5]


def make_clips(segments, dictionary, config):
    """Never merge distant mentions or expand a clip beyond the configured hard bound."""
    clips = []
    maximum = config['max_clip_seconds']
    for i, first in enumerate(segments):
        if clips and first['start'] < clips[-1]['end']:
            continue
        group = []
        for current in segments[i:]:
            end = current['start'] + current['duration']
            if end - first['start'] > maximum:
                break
            if group and current['start'] - (group[-1]['start'] + group[-1]['duration']) > 2:
                break
            group.append(current)
            text = ' '.join(s['text'] for s in group)
            hits, signals = find_targets(text, dictionary), signals_in(text, config)
            if not hits or not signals:
                continue
            while len(group) > 1:
                shorter = ' '.join(s['text'] for s in group[1:])
                if not find_targets(shorter, dictionary) or not signals_in(shorter, config):
                    break
                group = group[1:]
                text = shorter
            hits, signals = find_targets(text, dictionary), signals_in(text, config)
            # Caption boundaries are evidence bounds, not inferred word boundaries.
            start = max(0, group[0]['start'] - 2)
            clip_end = min(end + 3, start + maximum, segments[-1]['start'] + segments[-1]['duration'])
            if clip_end < end:  # preserve the full evidence span; drop optional leading context
                start, clip_end = group[0]['start'], end
            clips.append({'start': round(start, 3), 'end': round(clip_end, 3),
                          'text': text, 'targets': sorted({h['name'] for h in hits}), 'signals': signals})
            break
        if len(clips) >= config['max_clips']:
            break
    return clips


def analyze(info, segments, dictionary, config):
    title, description = info.get('title') or '', info.get('description') or ''
    texts = {'title': title, 'description': description,
             'transcript': ' '.join(s['text'] for s in segments)}
    for field, phrases in config.get('exclude', {}).items():
        if signals_in(texts[field], {'signals': phrases}):
            return None
    language_text = ' '.join(s['text'] for s in segments) if segments else title + '\n' + description
    if not is_language(language_text, config['language']):
        return None
    clips = make_clips(segments, dictionary, config)
    found = evidence(title, 'title', dictionary, config) + evidence(description, 'description', dictionary, config)
    author_comments, seen_comments = [], set()
    for comment in (info.get('comments') or [])[:config.get('max_comments', 10)]:
        if info.get('channel_id') and comment.get('author_id') == info['channel_id']:
            if not comment.get('id') or comment['id'] in seen_comments:
                continue
            seen_comments.add(comment['id'])
            author_comments.append({'comment_id': comment['id'],
                                    'parent_id': None if comment.get('parent') == 'root' else comment.get('parent'),
                                    'author_channel_id': comment['author_id'], 'text': comment.get('text') or ''})
            found.extend({**e, 'comment_id': comment.get('id')} for e in
                         evidence(comment.get('text') or '', 'author_comment', dictionary, config))
    if not clips and not found:
        return None
    url = 'https://www.youtube.com/watch?v=' + info['id']
    for clip in clips:
        if info.get('duration') is not None:
            clip['end'] = min(clip['end'], info['duration'])
        clip['url'] = url + '&t=' + str(math.floor(clip['start'])) + 's'
    return {'url': url, 'title': title, 'channel': info.get('channel'), 'language': config['language'],
            'description': description, 'author_comments': author_comments,
            'evidence': found[:5], 'clips': clips,
            **({'timestamp_note': 'Brak powiązanego fragmentu napisów; timestamp nieustalony.'} if not clips else {})}


class QuietLogger:
    def debug(self, message): pass
    def info(self, message): pass
    def warning(self, message): pass
    def error(self, message): pass


def ydl_options(config):
    options = {'skip_download': True, 'quiet': True, 'logger': QuietLogger(), 'cachedir': False,
               'noplaylist': True, 'socket_timeout': 12, 'retries': 1, 'extractor_retries': 1,
               'ignore_no_formats_error': True, 'getcomments': False,
               'extractor_args': {'youtube': {'skip': ['hls', 'dash', 'translated_subs']}}}
    if os.getenv('INVESTWATCH_PROXY'):
        options['proxy'] = os.environ['INVESTWATCH_PROXY']
    if os.getenv('INVESTWATCH_USER_AGENT'):
        options['http_headers'] = {'User-Agent': os.environ['INVESTWATCH_USER_AGENT']}
    return options


def candidates(config):
    import yt_dlp
    # Round-robin queries so the first query does not monopolize the candidate budget.
    lists, seen = [], set()
    for query in config['queries']:
        options = ydl_options(config)
        options.update(extract_flat=True, playlistend=config['results_per_query'])
        try:
            with yt_dlp.YoutubeDL(options) as client:
                data = client.extract_info(f"ytsearch{config['results_per_query']}:{query}", download=False)
                lists.append([e['id'] for e in (data or {}).get('entries', []) if e and VIDEO_ID.fullmatch(e.get('id', ''))])
        except Exception:
            print('Nie udało się wykonać zapytania: ' + query, file=sys.stderr)
    for position in range(config['results_per_query']):
        for results in lists:
            if position >= len(results) or results[position] in seen:
                continue
            seen.add(results[position])
            yield results[position]
            if len(seen) >= config['max_candidates']:
                return


def metadata(video_id, config):
    import yt_dlp
    options = ydl_options(config)
    if config['max_comments']:
        options['getcomments'] = True
        options['extractor_args']['youtube']['max_comments'] = [str(config['max_comments'])]
        options['extractor_args']['youtube']['comment_sort'] = ['top']
    with yt_dlp.YoutubeDL(options) as client:
        return client.extract_info('https://www.youtube.com/watch?v=' + video_id, download=False)


def transcript(video_id, language):
    from requests import Session
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import GenericProxyConfig
    class TimedSession(Session):
        def request(self, method, url, **kwargs):
            kwargs.setdefault('timeout', 12)
            return super().request(method, url, **kwargs)
    with TimedSession() as session:
        proxy = os.getenv('INVESTWATCH_PROXY')
        if os.getenv('INVESTWATCH_USER_AGENT'):
            session.headers['User-Agent'] = os.environ['INVESTWATCH_USER_AGENT']
        api = YouTubeTranscriptApi(http_client=session,
            proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy) if proxy else None)
        tracks = sorted((t for t in api.list(video_id) if t.language_code == language), key=lambda t: t.is_generated)
        if not tracks:
            return []
        return [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in tracks[0].fetch()
                if math.isfinite(s.start) and math.isfinite(s.duration) and s.start >= 0 and s.duration >= 0]


def run(config, dictionary):
    results = []
    for number, video_id in enumerate(candidates(config), 1):
        print(f"[{number}/{config['max_candidates']}] {video_id}; trafienia: {len(results)}/{config['limit']}", file=sys.stderr)
        try:
            info = metadata(video_id, config)
            if not info:
                continue
            try:
                captions = transcript(video_id, config['language'])
            except Exception:
                captions = []
                print('  Napisy niedostępne; sprawdzam tylko dowody tekstowe.', file=sys.stderr)
            result = analyze(info, captions, dictionary, config)
            if result:
                results.append(result)
                if len(results) >= config['limit']:
                    break
        except Exception as error:
            print('  Pominięto: ' + type(error).__name__, file=sys.stderr)
    return results


def validate_inputs(config, dictionary):
    config.setdefault('max_comments', 10)
    for key in ('limit', 'results_per_query', 'max_candidates', 'max_clip_seconds', 'max_clips'):
        if type(config.get(key)) is not int or config[key] <= 0:
            raise ValueError(f'{key} musi być dodatnią liczbą całkowitą')
    if config['max_clip_seconds'] > 30 or config['max_clips'] > 2:
        raise ValueError('Demo dopuszcza najwyżej 2 fragmenty po 30 sekund na film')
    if type(config.get('max_comments')) is not int or not 0 <= config['max_comments'] <= 100:
        raise ValueError('max_comments musi być w zakresie 0–100')
    if not config.get('language') or not config.get('queries') or not config.get('signals'):
        raise ValueError('Podaj language, queries i signals')
    exclusions = config.get('exclude', {})
    if not isinstance(exclusions, dict) or any(
            field not in ('title', 'description', 'transcript') or not isinstance(phrases, list)
            or any(not isinstance(p, str) or not p.strip() for p in phrases)
            for field, phrases in exclusions.items()):
        raise ValueError('exclude: dozwolone title, description, transcript; wartości to listy niepustych fraz')
    if len(config['queries']) > 10 or config['max_candidates'] > 100:
        raise ValueError('Demo: maksymalnie 10 zapytań i 100 kandydatów')
    entries = dictionary['entries'] if isinstance(dictionary, dict) else dictionary
    if any(e.get('type') not in ('organization', 'agent', 'domain', 'keyword') or not e.get('id') or not e.get('value') for e in entries):
        raise ValueError('Wpis słownika wymaga id, type i value')
    if not any(e['type'] != 'keyword' for e in entries):
        raise ValueError('Podaj konkretne firmy, agentów lub domeny; same hasła nie wystarczą')
    return config, entries


def load_inputs(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text('utf-8-sig'))
    dictionary = json.loads((path.parent / config['dictionary']).read_text('utf-8-sig'))
    config, entries = validate_inputs(config, dictionary)
    return config, entries, path.parent / config['output']


def scan(config=None, dictionary=None, *, as_json=False, output_path=None):
    """Return a list (or JSON string); no filesystem I/O unless output_path is supplied."""
    config, entries = validate_inputs(deepcopy(DEFAULT_CONFIG if config is None else config),
                                     deepcopy(DEFAULT_DICTIONARY if dictionary is None else dictionary))
    results = run(config, entries)
    if output_path is not None:
        save(results, Path(output_path))
    return json.dumps(results, ensure_ascii=False, allow_nan=False) if as_json else results


def start_background(config=None, dictionary=None, *, as_json=False, output_path=None):
    """Start a worker thread and return Future. The host process must remain alive."""
    config = deepcopy(DEFAULT_CONFIG if config is None else config)
    dictionary = deepcopy(DEFAULT_DICTIONARY if dictionary is None else dictionary)
    future = Future()
    def worker():
        if not future.set_running_or_notify_cancel():
            return
        try:
            future.set_result(scan(config, dictionary, as_json=as_json, output_path=output_path))
        except BaseException as error:
            future.set_exception(error)
    Thread(target=worker, name='investwatch-demo', daemon=False).start()
    return future


def save(results, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(results, stream, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Demo wyszukiwania konkretnych promocji inwestycyjnych')
    parser.add_argument('--config', help='Opcjonalny plik wejściowy; bez flagi używa danych w kodzie')
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument('--stdout', action='store_true', help='Tylko JSON na stdout, bez zapisu pliku')
    destination.add_argument('--output', help='Ścieżka pliku wynikowego')
    parser.add_argument('--limit', type=int, help='Maksymalna liczba filmów, np. 5')
    args = parser.parse_args(argv)
    if args.config:
        config, dictionary, output = load_inputs(args.config)
    else:
        config, dictionary, output = deepcopy(DEFAULT_CONFIG), deepcopy(DEFAULT_DICTIONARY), Path('wynik.json')
    if args.limit is not None:
        if args.limit < 1:
            parser.error('--limit musi być dodatni')
        config['limit'] = args.limit
    results = scan(config, dictionary)
    if args.stdout:
        print(json.dumps(results, ensure_ascii=False, allow_nan=False))
    else:
        output = Path(args.output) if args.output else output
        save(results, output)
        print(f'Zapisano {len(results)}/{config["limit"]} filmów: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
