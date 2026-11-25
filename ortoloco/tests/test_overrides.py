"""
Guards for the template overrides of ortoloco.

Template overrides break silently on juntagrico releases: a renamed block or template is simply not rendered,
a removed tag or filter only fails when the page is visited. These tests fail instead.
"""
import hashlib
from pathlib import Path

from django.conf import settings
from django.template import Template, engines
from django.template.loader_tags import BlockNode, ExtendsNode
from django.test import SimpleTestCase

from juntagrico.config import Config

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / 'templates'

# Overrides that replace an upstream template completely instead of extending it.
# If juntagrico changes the upstream template, this test fails: compare the override with the new upstream version,
# take over the changes and update the hash (sha256 of the upstream file).
REPLACED_UPSTREAM = {
    # wording "Genossenschafter:in" instead of the member vocabulary
    'exports/share_certificate.html': 'c42e62e3385bd75b8fa5a4fd7df906e8692fbbc8b2aa09bdef22222a0fac3f6f',
    # ortoloco specific text about areas
    'juntagrico/my/area/snippets/intro.html': '6ba305a708b5d6513ae7f4e9be8e72288ab2fe694313b18d42219550937a6538',
}

# email keys used by ortoloco that are not defined by juntagrico
CUSTOM_EMAIL_KEYS = {
    'j_notify',  # ortoloco.util.area_admin_notify
}


def engine():
    return engines['django'].engine


def own_templates():
    for path in sorted(TEMPLATE_DIR.rglob('*')):
        if path.is_file() and path.suffix in ('.html', '.txt'):
            yield path.relative_to(TEMPLATE_DIR).as_posix()


def upstream_origin(name, skip=()):
    """
    :return: origin of the next template with this name that is not ortoloco's or in skip, None if there is none
    """
    for loader in engine().template_loaders:
        for origin in loader.get_template_sources(name):
            path = Path(origin.name)
            if path.exists() and TEMPLATE_DIR not in path.parents and origin.name not in skip:
                return origin
    return None


def compile_origin(origin):
    return Template(Path(origin.name).read_text(), origin=origin, name=origin.template_name, engine=engine())


def parent_name(template):
    extends = template.nodelist.get_nodes_by_type(ExtendsNode)
    return extends[0].parent_name.resolve({}) if extends else None


def parent_template(template, history):
    """
    resolves the template that is extended, like ExtendsNode does: a template extending its own name
    gets the next template with that name (e.g. juntagrico-billing, then juntagrico)
    """
    name = parent_name(template)
    if name is None:
        return None
    if name == template.origin.template_name:
        origin = upstream_origin(name, skip=history)
        return compile_origin(origin) if origin else None
    return engine().get_template(name)


def available_blocks(template, history=()):
    """
    :return: names of all blocks of the template and its ancestors
    """
    history = (*history, template.origin.name)
    blocks = {node.name for node in template.nodelist.get_nodes_by_type(BlockNode)}
    parent = parent_template(template, history)
    if parent is not None:
        blocks |= available_blocks(parent, history)
    return blocks


class TemplateOverrideTests(SimpleTestCase):
    def test_templates_compile(self):
        # catches removed tags and filters, e.g. active_on in juntagrico 2.1
        for name in own_templates():
            with self.subTest(template=name):
                engine().get_template(name)

    def test_extended_templates_exist(self):
        for name in own_templates():
            with self.subTest(template=name):
                template = engine().get_template(name)
                parent = parent_name(template)
                if parent is None:
                    continue
                if parent == name:
                    self.assertIsNotNone(upstream_origin(name), f'{name} extends itself, but juntagrico has no such template')
                else:
                    engine().get_template(parent)

    def test_overridden_blocks_exist(self):
        # catches blocks that were renamed or removed upstream: their content is silently not rendered
        for name in own_templates():
            with self.subTest(template=name):
                template = engine().get_template(name)
                if parent_name(template) is None:
                    continue
                parent = parent_template(template, (template.origin.name,))
                if parent is None:
                    continue  # reported by test_extended_templates_exist
                own_blocks = {node.name for node in template.nodelist.get_nodes_by_type(BlockNode)}
                missing = own_blocks - available_blocks(parent, (template.origin.name,))
                self.assertFalse(missing, f'{name} overrides blocks that do not exist in {parent_name(template)}: {missing}')

    def test_replacements_are_registered(self):
        # full copies of upstream templates must be tracked, so that upstream changes are noticed
        for name in own_templates():
            with self.subTest(template=name):
                origin = upstream_origin(name)
                if origin is None or parent_name(engine().get_template(name)) == name:
                    continue
                self.assertIn(name, REPLACED_UPSTREAM, f'{name} replaces {origin.name}: add it to REPLACED_UPSTREAM')

    def test_replaced_upstream_unchanged(self):
        for name, sha256 in REPLACED_UPSTREAM.items():
            with self.subTest(template=name):
                origin = upstream_origin(name)
                self.assertIsNotNone(origin, f'juntagrico no longer has {name}: the override is not used anymore')
                current = hashlib.sha256(Path(origin.name).read_bytes()).hexdigest()
                self.assertEqual(
                    current, sha256,
                    f'juntagrico changed {name}: review the override against {origin.name} and update the hash'
                )

    def test_configured_templates_exist(self):
        names = [settings.MAIL_TEMPLATE, *settings.EMAILS.values()]
        names += [conf if isinstance(conf, str) else conf['template'] for conf in settings.DEPOT_LISTS.values()]
        for name in names:
            with self.subTest(template=name):
                engine().get_template(name)

    def test_email_keys_exist(self):
        # a renamed key in juntagrico would make the override ineffective
        # the defaults are only available in the closure of Config.emails
        defaults = [cell.cell_contents for cell in Config.emails.__closure__ or () if isinstance(cell.cell_contents, dict)]
        if not defaults:
            self.skipTest('juntagrico does not expose the default email keys')
        unknown = set(settings.EMAILS) - set(defaults[0]) - CUSTOM_EMAIL_KEYS
        self.assertFalse(unknown, f'EMAILS keys unknown to juntagrico: {unknown}')
