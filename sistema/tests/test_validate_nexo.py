"""Adversarial offline validator tests using disposable synthetic repositories."""
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sistema.scripts.validate_nexo import validate_repository


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('README.md', '[Área](perfil/)\n')
        self.write('START_HERE.md', '[Inicio](README.md)\n')
        self.write('perfil/README.md', '[Nota](note.md)\n')
        self.note()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return target

    def note(self, path='perfil/note.md', body='# Nota\n', extra='', **values):
        data = {'id': 'n-' + str(uuid4()), 'tipo': 'tema', 'estado': 'activo', 'actualizado': f'"{date.today()}"', 'resumen': 'Una nota sintética.'}
        data.update(values)
        self.write(path, '---\n' + '\n'.join(f'{k}: {v}' for k, v in data.items()) + '\n' + extra + '\n---\n' + body)
        return data['id']

    def errors(self):
        return '\n'.join(validate_repository(self.root).errors)

    def test_valid_note_and_directory_navigation(self):
        self.assertEqual(validate_repository(self.root).errors, [])

    def test_missing_front_matter(self):
        self.write('perfil/note.md', '# Note\n')
        self.assertIn('requires front matter', self.errors())

    def test_inbox_requires_metadata(self):
        self.write('_bandeja/capture.md', '# Capture\n')
        self.assertIn('requires front matter', self.errors())

    def test_readme_with_metadata_is_content(self):
        self.note('perfil/README.md', tipo='wrong')
        self.assertIn('Invalid tipo', self.errors())

    def test_content_readme_moves_intact_beside_navigation_cover(self):
        self.note('perfil/README.md', body='# Topic\n\nDecision recorded in 2019.\n[Source](https://example.invalid/source)\n', actualizado='"2019-01-01"')
        old = self.root / 'perfil/README.md'
        original = old.read_bytes()
        old.rename(self.root / 'perfil/estado.md')
        self.write('perfil/README.md', '# Topic\n\n[State](estado.md)\n[Other note](note.md)\n')
        self.assertEqual((self.root / 'perfil/estado.md').read_bytes(), original)
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_navigation_and_guides_exempt(self):
        self.write('sistema/guide.md', '# Guide\n')
        self.write('sistema/como-usar-nexo.md', '# Protocol\n')
        self.assertEqual(self.errors(), '')

    def test_templates_and_fixtures_excluded(self):
        for folder in ('sistema/plantillas', 'sistema/tests/fixtures', 'sistema/tests'):
            self.write(folder + '/sample.md', '---\nmalformed: [\n---\n[missing](missing.md)\n<<<<<<< HEAD\n')
        self.assertEqual(self.errors(), '')

    def test_missing_required_fields(self):
        self.write('perfil/note.md', '---\nid: nope\n---\n# Note')
        self.assertIn('Missing metadata actualizado', self.errors())

    def test_front_matter_unclosed(self):
        self.write('perfil/note.md', '---\nid: nope')
        self.assertIn('Unclosed', self.errors())

    def test_yaml_scalar_or_sequence(self):
        for content in ('hello', '- entry', ''):
            with self.subTest(content=content):
                self.write('perfil/note.md', '---\n' + content + '\n---\n')
                self.assertIn('must be a mapping', self.errors())

    def test_invalid_yaml(self):
        self.write('perfil/note.md', '---\nbroken: [\n---\n')
        self.assertIn('Invalid or unsafe', self.errors())

    def test_yaml_duplicate_keys(self):
        self.note(extra='tipo: proyecto')
        self.assertIn('Invalid or unsafe', self.errors())

    def test_yaml_nonstring_keys(self):
        self.note(extra='[one, two]: value')
        self.assertIn('Invalid or unsafe', self.errors())

    def test_yaml_python_tags_never_execute(self):
        marker = self.root / 'executed'
        self.write('perfil/note.md', f'---\n!!python/object/apply:os.system ["touch {marker}"]\n---\n')
        self.assertIn('Invalid or unsafe', self.errors())
        self.assertFalse(marker.exists())

    def test_yaml_aliases_rejected(self):
        self.note(extra='one: &anchor [a]\ntwo: *anchor')
        self.assertIn('Invalid or unsafe', self.errors())

    def test_id_version_and_canonical_form(self):
        for ident in ('n-6e6dce15-34fc-1cb8-90cd-64f769b33506', 'n-' + str(uuid4()).upper(), 'nope', '42', '[a]'):
            with self.subTest(ident=ident):
                self.note(id=ident)
                self.assertIn('canonical n-UUIDv4', self.errors())

    def test_duplicate_ids(self):
        ident = self.note()
        self.note('perfil/other.md', id=ident)
        self.assertIn('Duplicate id', self.errors())

    def test_type_and_state_allowlists(self):
        for values in ({'tipo': '[tema]'}, {'estado': 'published'}, {'tipo': 'null'}, {'estado': 'true'}):
            with self.subTest(values=values):
                self.note(**values)
                self.assertIn('Invalid', self.errors())

    def test_summary_must_be_string(self):
        for summary in ('null', 'false', '42', '[]', '""'):
            with self.subTest(summary=summary):
                self.note(resumen=summary)
                self.assertIn('resumen must', self.errors())

    def test_aliases_must_be_string_list(self):
        for aliases in ('name', '[1]', '[null]', '[""]', '{}'):
            with self.subTest(aliases=aliases):
                self.note(extra='aliases: ' + aliases)
                self.assertIn('aliases must', self.errors())
        self.note(extra='aliases: [Nombre, Alternativo]')
        self.assertEqual(self.errors(), '')

    def test_malformed_dates_fail_without_crashing(self):
        for value in ('"2026-02-30"', '2026-02-30', '20261002', '"2026-1-2"', '"2026-10-02T12:00:00"', 'null', '[2026]'):
            with self.subTest(value=value):
                self.note(actualizado=value)
                self.assertTrue(self.errors())

    def test_yaml_date_accepted(self):
        self.note(actualizado=str(date.today()))
        self.assertEqual(self.errors(), '')

    def test_verification_date_accepts_human_scope_wording(self):
        self.note(extra=f'verificado: "{date.today()}"', body='# Nota\nComprobé solamente el nombre en la fuente original.\n')
        self.assertEqual(self.errors(), '')
        self.note(extra=f'verificado: "{date.today()}"', body='# Nota\nAlcance verificado.\n')
        self.assertEqual(self.errors(), '')

    def test_historical_dates_do_not_warn(self):
        old = date.today() - timedelta(days=1000)
        self.note(actualizado=f'"{old}"', extra=f'verificado: "{old}"')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_future_metadata_dates_only_warn(self):
        future = date.today() + timedelta(days=1)
        for field in ('actualizado', 'verificado'):
            with self.subTest(field=field):
                self.note(**{field: f'"{future}"'})
                result = validate_repository(self.root)
                self.assertEqual(result.errors, [])
                self.assertEqual(len(result.warnings), 1)
                self.assertIn(field, result.warnings[0])
                self.assertIn('perfil/note.md', result.warnings[0])
        self.note(body=f'# Plan\nAppointment planned for {future}.\n')
        self.assertEqual(validate_repository(self.root).warnings, [])

    def test_broken_markdown_reference_link(self):
        self.note(body='[Reference][ref]\n\n[ref]: missing.md\n')
        self.assertIn('Broken local link', self.errors())

    def test_broken_image(self):
        self.note(body='![Image](missing.png)\n')
        self.assertIn('Broken local link', self.errors())

    def test_code_examples_ignore_links_and_conflicts(self):
        self.note(body='```markdown\n[Missing](missing.md)\n<<<<<<< HEAD\n=======\n>>>>>>> branch\n```\n\n    [Missing](other.md)\n\n`[Missing](third.md)`\n')
        self.assertEqual(self.errors(), '')

    def test_real_conflicts_fail(self):
        for marker in ('<<<<<<< HEAD', '=======', '>>>>>>> branch', '||||||| base'):
            with self.subTest(marker=marker):
                self.note(body=marker + '\n')
                self.assertIn('conflict marker', self.errors())

    def test_setext_heading_is_not_conflict(self):
        self.note(body='Heading\n=======\n')
        self.assertEqual(self.errors(), '')

    def test_external_links_never_fetched(self):
        self.note(body='[Source](https://files.example.invalid/synthetic)\n[Site](https://invalid.test/nope)\n')
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
            self.assertEqual(self.errors(), '')

    def test_encoded_path_and_heading(self):
        self.write('perfil/a b.md', '# Área útil\n\n## Same\n## Same\n')
        self.note(body='[File](a%20b.md#%C3%A1rea-%C3%BAtil)\n[Repeat](a%20b.md#same-1)')
        # Make the target a guide instead of a content note for metadata purposes.
        self.note('perfil/a b.md', body='# Área útil\n\n## Same\n## Same\n')
        self.assertEqual(self.errors(), '')

    def test_bad_fragment(self):
        self.note(body='# Note\n[Section](#absent)\n')
        self.assertIn('Unknown heading', self.errors())

    def test_markdown_formatting_in_heading(self):
        self.note(body='# **Strong** and `code`\n[Here](#strong-and-code)')
        self.assertEqual(self.errors(), '')

    def test_directory_without_readme_is_broken(self):
        (self.root / 'empty').mkdir()
        self.note(body='[Empty](../empty/)')
        self.assertIn('Broken local link', self.errors())

    def test_orphan_note(self):
        self.note('perfil/orphan.md')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertTrue(any('Orphan content' in warning for warning in result.warnings))

    def test_disconnected_cycle_is_orphan(self):
        self.note('perfil/a.md', body='[B](b.md)')
        self.note('perfil/b.md', body='[A](a.md)')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertEqual(sum('Orphan content' in warning for warning in result.warnings), 2)

    def test_connected_chain_is_reachable(self):
        self.note(body='[Next](next.md)')
        self.note('perfil/next.md', body='[Last](last.md)')
        self.note('perfil/last.md', body='[Back](note.md)')
        self.assertEqual(self.errors(), '')

    def test_images_do_not_provide_navigation(self):
        self.note(body='![Note](other.md)')
        self.note('perfil/other.md')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertTrue(any('Orphan content' in warning for warning in result.warnings))

    def test_replacement_missing_self_and_malformed(self):
        self.note(extra='sustituido_por: n-' + str(uuid4()))
        self.assertIn('does not exist', self.errors())
        ident = 'n-' + str(uuid4())
        self.note(id=ident, extra='sustituido_por: ' + ident)
        self.assertIn('itself', self.errors())
        self.note(extra='sustituido_por: [wrong]')
        self.assertIn('must be an n-UUIDv4', self.errors())

    def test_replacement_cycle_multiple_nodes(self):
        a, b, c = ['n-' + str(uuid4()) for _ in range(3)]
        self.note(id=a, extra='sustituido_por: ' + b, body='[B](b.md)')
        self.note('perfil/b.md', id=b, extra='sustituido_por: ' + c, body='[C](c.md)')
        self.note('perfil/c.md', id=c, extra='sustituido_por: ' + a)
        self.assertIn('Replacement cycle', self.errors())

    def test_valid_replacement_chain(self):
        ident = self.note('perfil/new.md')
        self.note(extra='sustituido_por: ' + ident, body='[New](new.md)', estado='sustituido')
        self.assertEqual(self.errors(), '')

    def test_size_and_index_warnings(self):
        self.note(body=('word ' * 2001))
        self.write('perfil/README.md', '[Note](note.md)\n' * 40)
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 2)

    def test_byte_size_threshold_is_independent_of_word_count(self):
        self.note(body='x' * (30 * 1024 + 1))
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertTrue(result.warnings)

    def test_nonportable_paths_warn(self):
        self.note(body='[Local](/Users/synthetic/file.md)\n[Outside](../../elsewhere.md)\n')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 2)

    def test_file_url_warns(self):
        self.note(body='[Local](file:///Users/synthetic/file.md)')
        result = validate_repository(self.root)
        self.assertEqual(result.errors, [])
        self.assertIn('Nonportable', result.warnings[0])

    def test_exclusion_names_in_content_are_not_exempt(self):
        for folder in ('tests', 'fixtures', 'plantillas'):
            self.write(f'aprendizaje/{folder}/note.md', '# Missing metadata')
        self.assertEqual(self.errors().count('requires front matter'), 3)

    def test_required_entry_indexes(self):
        for name in ('README.md', 'START_HERE.md'):
            (self.root / name).unlink()
        self.assertEqual(self.errors().count('Required entry index'), 2)

    def test_utility_conflict_markers(self):
        self.write('.github/workflows/test.yml', '<<<<<<< HEAD\nname: test\n=======\n')
        self.assertIn('conflict marker in utility', self.errors())

    def test_malformed_url_does_not_crash(self):
        self.note(body='[Bad](http://[bad)')
        # markdown-it normalizes the malformed host to an external destination.
        self.assertEqual(self.errors(), '')

    def test_cli_unindexed_notes_and_disconnected_cycle_succeed(self):
        self.note('perfil/orphan.md')
        self.note('perfil/a.md', body='[B](b.md)')
        self.note('perfil/b.md', body='[A](a.md)')
        script = Path(__file__).resolve().parents[1] / 'scripts/validate_nexo.py'
        result = subprocess.run([sys.executable, str(script), '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count('WARNING'), 3)
        self.assertNotIn('ERROR', result.stdout)

    def test_cli_errors_and_warning_success(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/validate_nexo.py'
        self.note(body='word ' * 2001)
        command = [sys.executable, str(script), '--root', str(self.root)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.note(body='[Broken](no.md)')
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
