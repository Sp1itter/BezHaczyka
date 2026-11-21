"""Small offline regression suite: python -m unittest -v."""
import unittest
from unittest.mock import patch
from demo import analyze, make_clips, find_targets, is_language, candidates

PL = 'W tym odcinku przedstawiamy warunki oferty i wyjaśniamy, na co należy uważać przed wpłaceniem własnych pieniędzy. '
DICT = [
    {'id': 'company', 'type': 'organization', 'value': 'Firma Przykład', 'aliases': ['Przykład SA']},
    {'id': 'site', 'type': 'domain', 'value': 'broker.example'},
    {'id': 'person', 'type': 'agent', 'value': 'Agent Przykładowy'},
]
CONFIG = {'language': 'pl', 'max_clip_seconds': 30, 'max_clips': 2,
          'signals': ['gwarantowany zysk', 'załóż konto', 'link partnerski', 'bez ryzyka']}


def segments(*texts):
    return [{'text': t, 'start': i*6, 'duration': 5} for i, t in enumerate(texts)]


class DemoTests(unittest.TestCase):
    def test_full_description_and_only_author_comments_within_limit(self):
        description = PL + ' Firma Przykład: gwarantowany zysk. ' + PL * 5
        info = {'id': 'aaaaaaaaaaa', 'title': 'Oferta', 'description': description, 'channel_id': 'UCauthor',
                'comments': [
                    {'id': 'other', 'author_id': 'UCother', 'text': 'Cudzy tekst'},
                    {'id': 'reply', 'parent': 'other', 'author_id': 'UCauthor', 'text': 'Pełna odpowiedź bez trafień.'},
                    {'id': 'missing', 'text': 'Bez identyfikatora autora'},
                    {'id': 'late', 'author_id': 'UCauthor', 'text': 'Po limicie'}]}
        result = analyze(info, [], DICT, {**CONFIG, 'max_comments': 3})
        self.assertEqual(result['description'], description)
        self.assertEqual([c['comment_id'] for c in result['author_comments']], ['reply'])
        self.assertEqual(result['author_comments'][0]['text'], 'Pełna odpowiedź bez trafień.')
        self.assertEqual(result['author_comments'][0]['parent_id'], 'other')

    def test_comments_disabled_exports_no_comments(self):
        info = {'id': 'aaaaaaaaaaa', 'title': 'Oferta', 'description': PL + ' Firma Przykład: gwarantowany zysk.',
                'channel_id': 'UCauthor', 'comments': [{'id': 'x', 'author_id': 'UCauthor', 'text': 'Komentarz'}]}
        self.assertEqual(analyze(info, [], DICT, {**CONFIG, 'max_comments': 0})['author_comments'], [])

    def test_memory_mode_and_background_do_not_write_files(self):
        import demo, json
        with patch('demo.run', return_value=[{'title': 'Przykład'}]), patch('demo.save') as save:
            self.assertEqual(json.loads(demo.scan(as_json=True)), [{'title': 'Przykład'}])
            future = demo.start_background(as_json=True)
            self.assertEqual(json.loads(future.result(timeout=5)), [{'title': 'Przykład'}])
            save.assert_not_called()

    def test_stdout_is_json_and_does_not_save(self):
        import demo, io, json
        from contextlib import redirect_stdout
        output = io.StringIO()
        with patch('demo.run', return_value=[{'title': 'Przykład'}]), patch('demo.save') as save, redirect_stdout(output):
            demo.main(['--stdout'])
        self.assertEqual(json.loads(output.getvalue()), [{'title': 'Przykład'}])
        save.assert_not_called()

    def test_exclusions_are_field_specific_and_case_insensitive(self):
        info = {'id': 'aaaaaaaaaaa', 'title': 'PORADNIK dla klientów',
                'description': PL + ' Firma Przykład: gwarantowany zysk.'}
        config = {**CONFIG, 'exclude': {'title': ['poradnik']}}
        self.assertIsNone(analyze(info, [], DICT, config))
        config['exclude'] = {'transcript': ['poradnik']}
        self.assertIsNotNone(analyze(info, [], DICT, config))

    def test_exclusion_uses_word_boundaries(self):
        info = {'id': 'aaaaaaaaaaa', 'title': 'Nieporadnik',
                'description': PL + ' Firma Przykład: gwarantowany zysk.'}
        self.assertIsNotNone(analyze(info, [], DICT, {**CONFIG, 'exclude': {'title': ['poradnik']}}))

    def test_general_investing_is_not_a_hit(self):
        result = analyze({'id': 'aaaaaaaaaaa', 'title': 'Jak inwestować', 'description': PL},
                         segments(PL, 'Akcje, obligacje, ETF i ryzyko.'), DICT, CONFIG)
        self.assertIsNone(result)

    def test_company_mention_without_promotion_is_not_a_hit(self):
        self.assertIsNone(analyze({'id': 'aaaaaaaaaaa', 'title': 'Film', 'description': PL},
                                 segments(PL, 'Firma Przykład publikuje wyniki kwartalne.'), DICT, CONFIG))

    def test_domain_host_not_query_or_lookalike(self):
        text = 'https://evil.example?x=broker.example notbroker.example broker.example.evil.org https://sub.broker.example/?aff=1'
        hits = find_targets(text, DICT)
        self.assertEqual([h['value'] for h in hits], ['https://sub.broker.example/?aff=1'])

    def test_title_or_description_hit_survives_missing_transcript(self):
        r = analyze({'id': 'aaaaaaaaaaa', 'title': 'Oferta',
                     'description': PL + ' Załóż konto: https://broker.example/?ref=123'}, [], DICT, CONFIG)
        self.assertIsNotNone(r)
        self.assertEqual(r['clips'], [])
        self.assertEqual(r['timestamp_note'], 'Brak powiązanego fragmentu napisów; timestamp nieustalony.')
        self.assertTrue(r['evidence'])

    def test_clip_is_short_and_has_concrete_target_and_signal(self):
        data = segments(PL, 'Firma Przykład oferuje gwarantowany zysk.', 'Opisujemy szczegóły tej oferty.')
        r = analyze({'id': 'aaaaaaaaaaa', 'title': 'Oferta', 'description': PL}, data, DICT, CONFIG)
        self.assertEqual(len(r['clips']), 1)
        self.assertLessEqual(r['clips'][0]['end'] - r['clips'][0]['start'], 30)
        self.assertIn('gwarantowany zysk', r['clips'][0]['signals'])
        self.assertGreaterEqual(r['clips'][0]['start'], 4)
        self.assertLessEqual(r['clips'][0]['end'], 14)

    def test_distant_target_does_not_create_fake_ad_clip(self):
        data = [{'text': PL + ' Firma Przykład.', 'start': 0, 'duration': 5},
                {'text': 'Załóż konto.', 'start': 600, 'duration': 5}]
        self.assertEqual(make_clips(data, DICT, CONFIG), [])

    def test_repeated_hits_never_expand_into_whole_film(self):
        data = [{'text': 'Firma Przykład. Gwarantowany zysk.', 'start': i*10, 'duration': 5} for i in range(100)]
        clips = make_clips(data, DICT, CONFIG)
        self.assertLessEqual(len(clips), 2)
        self.assertTrue(all(c['end']-c['start'] <= 30 for c in clips))
        self.assertLessEqual(sum(c['end']-c['start'] for c in clips), 60)

    def test_description_link_does_not_timestamp_unrelated_speech(self):
        r = analyze({'id': 'aaaaaaaaaaa', 'title': 'Oferta', 'description': PL + ' Załóż konto: broker.example'},
                    segments(PL, 'Dzisiaj omawiamy jak działają obligacje i inflacja.'), DICT, CONFIG)
        self.assertEqual(r['clips'], [])

    def test_foreign_and_uncertain_text_excluded(self):
        self.assertFalse(is_language('ETF broker.example', 'pl'))
        self.assertFalse(is_language('This video explains the investment offer and account registration. Please read all the terms and conditions before depositing money into your account.', 'pl'))
        self.assertTrue(is_language(PL*3, 'pl'))

    def test_polish_intro_does_not_hide_english_transcript(self):
        english = 'This video explains the investment offer and account registration. Read the terms and conditions before depositing money. '
        self.assertFalse(is_language(PL*80 + english*400, 'pl'))

    def test_same_target_does_not_fill_output_with_repeated_evidence(self):
        text = PL + ' Firma Przykład: załóż konto. ' * 10
        r = analyze({'id': 'aaaaaaaaaaa', 'title': 'Oferta', 'description': text}, [], DICT, CONFIG)
        self.assertEqual(len(r['evidence']), 1)

    def test_search_deduplicates_ids_and_respects_candidate_limit(self):
        class Client:
            def __init__(self, options): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def extract_info(self, url, download):
                return {'entries': [{'id': 'aaaaaaaaaaa'}, {'id': 'bbbbbbbbbbb'}]}
        config = {'queries': ['q1', 'q2'], 'results_per_query': 2, 'max_candidates': 2}
        with patch('yt_dlp.YoutubeDL', Client):
            self.assertEqual(list(candidates(config)), ['aaaaaaaaaaa', 'bbbbbbbbbbb'])
            config['max_candidates'] = 1
            self.assertEqual(list(candidates(config)), ['aaaaaaaaaaa'])


if __name__ == '__main__':
    unittest.main()
