"""Synthetic acceptance examples for the Nexo documentary protocol.

These tests exercise repository artifacts and local Git behavior. They are not a
classification engine and they never connect to, emulate, or modify Google Drive.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sistema.scripts.validate_nexo import validate_repository


AREAS = (
    "perfil",
    "salud",
    "relaciones",
    "trabajo",
    "finanzas",
    "hogar",
    "tecnologia",
    "aprendizaje",
    "ocio-y-viajes",
    "ideas-y-futuro",
)


def write_text(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def note(
    identifier: str,
    title: str,
    body: str,
    *,
    note_type: str = "tema",
    state: str = "activo",
    summary: str | None = None,
) -> str:
    return f'''---
id: {identifier}
tipo: {note_type}
estado: {state}
actualizado: "2026-10-03"
resumen: "{summary or title}"
---

# {title}

{body}
'''


def build_minimal_repository(root: Path) -> None:
    area_links = "\n".join(f"- [{area}]({area}/README.md)" for area in AREAS)
    write_text(root, "README.md", f"# Nexo sintético\n\n{area_links}")
    write_text(root, "START_HERE.md", "# Inicio\n\n[Índice](README.md)")
    write_text(root, "sistema/como-usar-nexo.md", "# Protocolo sintético\n\nUsar solo datos de prueba.")
    for area in AREAS:
        write_text(root, f"{area}/README.md", f"# {area}\n\nÍndice sintético del ámbito.")


def append_link(root: Path, index_path: str, label: str, target: str) -> None:
    path = root / index_path
    with path.open("a", encoding="utf-8") as index:
        index.write(f"\n- [{label}]({target})\n")


class NexoDocumentProtocolAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "nexo"
        self.root.mkdir()
        build_minimal_repository(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def assert_repository_valid(self) -> None:
        result = validate_repository(self.root)
        self.assertEqual([], result.errors, "\n".join(result.errors))

    def test_empty_starter_has_ten_navigation_covers_and_validates_cleanly(self) -> None:
        covers = [self.root / area / "README.md" for area in AREAS]
        self.assertEqual(10, len(covers))
        for cover in covers:
            with self.subTest(area=cover.parent.name):
                self.assertEqual([cover], list(cover.parent.rglob("*.md")))
                content = cover.read_text(encoding="utf-8")
                self.assertFalse(content.startswith("---"))
                self.assertNotRegex(content, r"https?://|n-[0-9a-f]{8}-")
        result = validate_repository(self.root)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_colleague_and_friend_keep_linked_scopes_with_one_shared_event(self) -> None:
        work_id = "n-11111111-1111-4111-8111-111111111111"
        friendship_id = "n-22222222-2222-4222-8222-222222222222"
        work_path = write_text(
            self.root,
            "trabajo/empresa-demo/equipo/ana.md",
            note(
                work_id,
                "Ana en el contexto laboral",
                """## Alcance

Esta nota conserva responsabilidades, feedback y coordinación profesional.

## Hecho compartido

EVENTO-SINTETICO-2026-09-14. Acordamos revisar un proyecto durante una conversación social. Este hecho se registra aquí porque el acuerdo fue laboral.

## Relación personal

La amistad se mantiene en [Ana en amistades](../../../relaciones/amistades/ana.md).""",
                note_type="persona",
            ),
        )
        friendship_path = write_text(
            self.root,
            "relaciones/amistades/ana.md",
            note(
                friendship_id,
                "Ana en el contexto personal",
                """## Alcance

Esta nota conserva la amistad, experiencias personales y cuidados mutuos.

## Contexto conectado

El acuerdo profesional se referencia en el [hecho compartido de la ficha laboral](../../trabajo/empresa-demo/equipo/ana.md#hecho-compartido).""",
                note_type="persona",
            ),
        )
        append_link(self.root, "trabajo/README.md", "Ana en equipo", "empresa-demo/equipo/ana.md")
        append_link(self.root, "relaciones/README.md", "Ana en amistades", "amistades/ana.md")

        combined = work_path.read_text(encoding="utf-8") + friendship_path.read_text(encoding="utf-8")
        self.assertEqual(1, combined.count("EVENTO-SINTETICO-2026-09-14"))
        self.assertIn("responsabilidades, feedback y coordinación profesional", combined)
        self.assertIn("amistad, experiencias personales y cuidados mutuos", combined)
        self.assert_repository_valid()

    def test_purchase_has_one_technology_home_and_finance_keeps_only_impact(self) -> None:
        purchase_path = write_text(
            self.root,
            "tecnologia/equipos/portatil.md",
            note(
                "n-33333333-3333-4333-8333-333333333333",
                "Compra de portátil",
                """## Resumen vigente

Esta es la sede del proyecto. Conserva criterios técnicos, comparación, decisión, configuración y garantía.

## Impacto financiero

El presupuesto y los pagos están en [impacto financiero](../../finanzas/compras/impacto-portatil.md).""",
                note_type="proyecto",
            ),
        )
        finance_path = write_text(
            self.root,
            "finanzas/compras/impacto-portatil.md",
            note(
                "n-44444444-4444-4444-8444-444444444444",
                "Impacto financiero del portátil",
                """## Resumen vigente

Reserva sintética de CLP 1.000 y tres cuotas. Esta nota conserva únicamente presupuesto, pagos y conciliación.

## Asunto principal

Los criterios, la configuración y la garantía están en la [sede tecnológica](../../tecnologia/equipos/portatil.md).""",
                note_type="registro",
            ),
        )
        append_link(self.root, "tecnologia/README.md", "Compra de portátil", "equipos/portatil.md")
        append_link(self.root, "finanzas/README.md", "Impacto del portátil", "compras/impacto-portatil.md")

        self.assertIn("Esta es la sede del proyecto", purchase_path.read_text(encoding="utf-8"))
        finance_body = finance_path.read_text(encoding="utf-8")
        self.assertIn("únicamente presupuesto, pagos y conciliación", finance_body)
        self.assertNotIn("16 GB", finance_body)
        self.assert_repository_valid()

    def test_current_update_preserves_id_and_history_without_daily_handoff(self) -> None:
        identifier = "n-55555555-5555-4555-8555-555555555555"
        path = write_text(
            self.root,
            "tecnologia/proyectos/sensor.md",
            note(
                identifier,
                "Sensor personal",
                """## Resumen vigente

El prototipo está en evaluación.

## Cambios significativos

- 2026-09-20. Se inició la evaluación.""",
                note_type="proyecto",
            ),
        )
        append_link(self.root, "tecnologia/README.md", "Sensor personal", "proyectos/sensor.md")
        original_id = re.search(r"^id: (.+)$", path.read_text(encoding="utf-8"), re.MULTILINE).group(1)

        write_text(
            self.root,
            "tecnologia/proyectos/sensor.md",
            note(
                identifier,
                "Sensor personal",
                """## Resumen vigente

El prototipo vigente usa el segundo sensor y la evaluación continúa.

## Cambios significativos

- 2026-09-20. Se inició la evaluación.
- 2026-10-03. Se cambió al segundo sensor conservando la procedencia del primer hito.""",
                note_type="proyecto",
            ),
        )

        updated = path.read_text(encoding="utf-8")
        self.assertIn(f"id: {original_id}", updated)
        self.assertIn("2026-09-20. Se inició la evaluación", updated)
        self.assertEqual([path], list((self.root / "tecnologia/proyectos").glob("sensor*")))
        self.assertFalse(any("handoff" in candidate.name for candidate in self.root.rglob("*.md")))
        self.assert_repository_valid()

    def test_note_moves_beside_topic_cover_without_losing_identity_links_or_history(self) -> None:
        identifier = "n-66666666-6666-4666-8666-666666666666"
        finance_id = "n-77777777-7777-4777-8777-777777777777"
        old_path = write_text(
            self.root,
            "hogar/movilidad/compra-auto.md",
            note(
                identifier,
                "Compra de auto",
                """## Resumen vigente

Proyecto sintético en evaluación.

## Cambios significativos

- 2026-09-18. Se definieron los criterios iniciales.

## Finanzas

Ver el [impacto financiero](../../finanzas/compras/impacto-auto.md).""",
                note_type="proyecto",
            ),
        )
        write_text(
            self.root,
            "finanzas/compras/impacto-auto.md",
            note(finance_id, "Impacto financiero del auto", "[Proyecto principal](../../hogar/movilidad/compra-auto.md).", note_type="registro"),
        )
        append_link(self.root, "hogar/README.md", "Compra de auto", "movilidad/compra-auto.md")
        append_link(self.root, "finanzas/README.md", "Impacto del auto", "compras/impacto-auto.md")
        self.assert_repository_valid()

        topic_dir = old_path.with_suffix("")
        topic_dir.mkdir()
        new_path = topic_dir / "estado.md"
        old_path.rename(new_path)

        invalid_transition = validate_repository(self.root)
        self.assertTrue(
            any("Broken local link movilidad/compra-auto.md" in error for error in invalid_transition.errors),
            "The validator must reject an index that still points at the pre-move path",
        )
        self.assertTrue(
            any("Broken local link ../../hogar/movilidad/compra-auto.md" in error for error in invalid_transition.errors),
            "The validator must reject a reverse reference that still points at the pre-move path",
        )

        write_text(
            self.root,
            "hogar/movilidad/compra-auto/criterios.md",
            note(
                "n-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "Criterios para la compra de auto",
                """## Función

Este detalle conserva los criterios de uso, seguridad y mantenimiento separados de la síntesis vigente.

## Tema principal

Volver a la [síntesis de la compra](estado.md).""",
                note_type="tema",
            ),
        )
        write_text(
            self.root,
            "hogar/movilidad/compra-auto/historico/README.md",
            """# Histórico de la compra de auto

- [Hitos de 2026](2026.md)
- [Volver a la síntesis](../estado.md)""",
        )
        write_text(
            self.root,
            "hogar/movilidad/compra-auto/historico/2026.md",
            note(
                "n-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "Histórico 2026 de la compra de auto",
                """## Hitos

- 2026-09-18. Se definieron los criterios iniciales.

## Tema principal

La síntesis vigente está en [Compra de auto](../estado.md).""",
                note_type="registro",
                state="archivado",
            ),
        )
        new_path.write_text(
            note(
                identifier,
                "Compra de auto",
                """## Resumen vigente

Proyecto sintético en evaluación. Esta entrada conserva la síntesis vigente después de dividir el tema.

## Navegación

- [Criterios](criterios.md)
- [Histórico](historico/README.md)

## Finanzas

Ver el [impacto financiero](../../../finanzas/compras/impacto-auto.md).""",
                note_type="proyecto",
            ),
            encoding="utf-8",
        )
        hogar_index = self.root / "hogar/README.md"
        hogar_index.write_text(
            hogar_index.read_text(encoding="utf-8").replace("movilidad/compra-auto.md", "movilidad/compra-auto/README.md"),
            encoding="utf-8",
        )
        finance_note = self.root / "finanzas/compras/impacto-auto.md"
        finance_note.write_text(
            finance_note.read_text(encoding="utf-8").replace(
                "../../hogar/movilidad/compra-auto.md",
                "../../hogar/movilidad/compra-auto/estado.md",
            ),
            encoding="utf-8",
        )

        cover = write_text(self.root, "hogar/movilidad/compra-auto/README.md", "# Compra de auto\n\nPortada del proyecto. [Estado vigente](estado.md).")
        self.assertNotIn("id:", cover.read_text(encoding="utf-8"))
        self.assertNotIn("Proyecto sintético en evaluación", cover.read_text(encoding="utf-8"))
        moved = new_path.read_text(encoding="utf-8")
        self.assertIn(f"id: {identifier}", moved)
        self.assertIn("síntesis vigente después de dividir el tema", moved)
        self.assertIn("[Histórico](historico/README.md)", moved)
        self.assertNotIn("2026-09-18. Se definieron los criterios iniciales", moved)
        self.assertIn(
            "2026-09-18. Se definieron los criterios iniciales",
            (topic_dir / "historico/2026.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "id: n-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            (topic_dir / "criterios.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "id: n-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            (topic_dir / "historico/2026.md").read_text(encoding="utf-8"),
        )
        self.assertIn("../../../finanzas/compras/impacto-auto.md", moved)
        self.assertIn(
            "../../hogar/movilidad/compra-auto/estado.md",
            finance_note.read_text(encoding="utf-8"),
        )
        self.assertFalse(old_path.exists())
        self.assert_repository_valid()

    def test_drive_examples_reuse_existing_folder_and_preserve_document_identity(self) -> None:
        drive_root = Path(self.temp_dir.name) / "synthetic-drive"
        medical_folder = drive_root / "EXAMENES SINTETICOS"
        medical_folder.mkdir(parents=True)
        existing = {
            "lab-2026-08-01.pdf",
            "lab-2026-09-15.pdf",
            "lab-2026-09-15-corregido.pdf",
        }
        for filename in existing:
            (medical_folder / filename).write_bytes(b"synthetic fixture")
        folders_before = {path.relative_to(drive_root) for path in drive_root.rglob("*") if path.is_dir()}

        shared_url = "https://files.example.invalid/document-2026-09-15"
        health = write_text(
            self.root,
            "salud/laboratorio.md",
            note(
                "n-88888888-8888-4888-8888-888888888888",
                "Laboratorio sintético",
                f"""## Fuentes y archivos

| Documento | Tipo | Fecha de muestra | Fecha de emisión | Fecha de subida | Relación | Original |
|---|---|---|---|---|---|---|
| lab-2026-08-01.pdf | panel sintético | 2026-08-01 | 2026-08-02 | 2026-08-03 | estudio independiente | [Drive]({shared_url.replace('2026-09-15', '2026-08-01')}) |
| lab-2026-09-15.pdf | panel sintético | 2026-09-15 | 2026-09-16 | 2026-09-18 | original | [Drive]({shared_url}) |
| lab-2026-09-15-corregido.pdf | panel sintético | 2026-09-15 | 2026-09-19 | 2026-09-20 | corrige el informe del 16 de septiembre sin eliminarlo | [Drive corregido](https://files.example.invalid/document-correction) |""",
                note_type="registro",
            ),
        )
        work = write_text(
            self.root,
            "trabajo/seguimiento-bienestar.md",
            note(
                "n-99999999-9999-4999-8999-999999999999",
                "Seguimiento laboral sintético",
                f"""## Fuente compartida

La recomendación de horario referencia el mismo original, sin copiarlo ni reinterpretarlo, [informe en Drive]({shared_url}).""",
                note_type="registro",
            ),
        )
        append_link(self.root, "salud/README.md", "Laboratorio sintético", "laboratorio.md")
        append_link(self.root, "trabajo/README.md", "Seguimiento laboral sintético", "seguimiento-bienestar.md")

        folders_after = {path.relative_to(drive_root) for path in drive_root.rglob("*") if path.is_dir()}
        self.assertEqual(folders_before, folders_after)
        self.assertEqual(existing, {path.name for path in medical_folder.iterdir()})
        self.assertEqual(2, (health.read_text(encoding="utf-8") + work.read_text(encoding="utf-8")).count(shared_url))
        health_text = health.read_text(encoding="utf-8")
        self.assertIn("lab-2026-08-01.pdf", health_text)
        self.assertIn("lab-2026-09-15.pdf", health_text)
        self.assertIn("lab-2026-09-15-corregido.pdf", health_text)
        self.assertRegex(health_text, r"2026-09-15 \| 2026-09-16 \| 2026-09-18")
        self.assertRegex(health_text, r"2026-09-15 \| 2026-09-19 \| 2026-09-20")
        self.assert_repository_valid()


class NexoGitConcurrencyAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.hooks = self.root / "empty-hooks"
        self.hooks.mkdir()
        self.env = os.environ.copy()
        self.env.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "LC_ALL": "C",
            }
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def git(self, *args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = [
            "git",
            "-c",
            f"core.hooksPath={self.hooks}",
            "-c",
            "user.name=Nexo Acceptance",
            "-c",
            "user.email=nexo-acceptance@example.invalid",
            *args,
        ]
        return subprocess.run(command, cwd=cwd, env=self.env, text=True, capture_output=True, check=check)

    def commit(self, clone: Path, message: str) -> None:
        self.git("add", "tema.md", cwd=clone)
        self.git("commit", "-m", message, cwd=clone)

    def test_stale_push_rebases_compatible_same_document_and_preserves_both_changes(self) -> None:
        remote = self.root / "remote.git"
        seed = self.root / "seed"
        clone_a = self.root / "clone-a"
        clone_b = self.root / "clone-b"
        verify = self.root / "verify"
        self.git("init", "--bare", "--initial-branch=main", str(remote))
        self.git("clone", str(remote), str(seed))
        initial = """# Tema compartido

## Cambio de Ada

Pendiente.

Texto estable uno.

Texto estable dos.

Texto estable tres.

## Cambio de Beto

Pendiente.
"""
        (seed / "tema.md").write_text(initial, encoding="utf-8")
        self.commit(seed, "test (Nexo): seed concurrent acceptance fixture")
        self.git("push", "origin", "main", cwd=seed)
        self.git("clone", str(remote), str(clone_a))
        self.git("clone", str(remote), str(clone_b))

        path_a = clone_a / "tema.md"
        path_a.write_text(path_a.read_text(encoding="utf-8").replace("## Cambio de Ada\n\nPendiente.", "## Cambio de Ada\n\nAda conserva su actualización."), encoding="utf-8")
        self.commit(clone_a, "test (Nexo): record Ada fixture update")
        self.git("push", "origin", "main", cwd=clone_a)

        path_b = clone_b / "tema.md"
        path_b.write_text(path_b.read_text(encoding="utf-8").replace("## Cambio de Beto\n\nPendiente.", "## Cambio de Beto\n\nBeto conserva su actualización."), encoding="utf-8")
        self.commit(clone_b, "test (Nexo): record Beto fixture update")
        stale_push = self.git("push", "origin", "main", cwd=clone_b, check=False)
        self.assertNotEqual(0, stale_push.returncode)
        self.assertRegex(stale_push.stderr, r"rejected|fetch first|non-fast-forward")

        self.git("fetch", "origin", cwd=clone_b)
        self.git("rebase", "origin/main", cwd=clone_b)
        reread = path_b.read_text(encoding="utf-8")
        self.assertIn("Ada conserva su actualización", reread)
        self.assertIn("Beto conserva su actualización", reread)
        self.git("push", "origin", "main", cwd=clone_b)

        self.git("clone", str(remote), str(verify))
        published = (verify / "tema.md").read_text(encoding="utf-8")
        self.assertIn("Ada conserva su actualización", published)
        self.assertIn("Beto conserva su actualización", published)
        parents = self.git("rev-list", "--first-parent", "--count", "main", cwd=verify).stdout.strip()
        self.assertEqual("3", parents)

    def test_semantic_collision_is_not_declared_automatically_resolved(self) -> None:
        remote = self.root / "semantic.git"
        seed = self.root / "semantic-seed"
        clone_a = self.root / "semantic-a"
        clone_b = self.root / "semantic-b"
        self.git("init", "--bare", "--initial-branch=main", str(remote))
        self.git("clone", str(remote), str(seed))
        (seed / "tema.md").write_text("# Decisión\n\nEstado vigente: por confirmar.\n", encoding="utf-8")
        self.commit(seed, "test (Nexo): seed semantic collision fixture")
        self.git("push", "origin", "main", cwd=seed)
        self.git("clone", str(remote), str(clone_a))
        self.git("clone", str(remote), str(clone_b))

        path_a = clone_a / "tema.md"
        path_a.write_text(path_a.read_text(encoding="utf-8").replace("por confirmar", "aprobada"), encoding="utf-8")
        self.commit(clone_a, "test (Nexo): record approved decision fixture")
        self.git("push", "origin", "main", cwd=clone_a)

        path_b = clone_b / "tema.md"
        path_b.write_text(path_b.read_text(encoding="utf-8").replace("por confirmar", "descartada"), encoding="utf-8")
        self.commit(clone_b, "test (Nexo): record discarded decision fixture")
        rejected = self.git("push", "origin", "main", cwd=clone_b, check=False)
        self.assertNotEqual(0, rejected.returncode)
        self.git("fetch", "origin", cwd=clone_b)
        rebase = self.git("rebase", "origin/main", cwd=clone_b, check=False)
        self.assertNotEqual(0, rebase.returncode)
        conflicted = path_b.read_text(encoding="utf-8")
        self.assertIn("<<<<<<<", conflicted)
        self.assertIn("aprobada", conflicted)
        self.assertIn("descartada", conflicted)
        self.git("rebase", "--abort", cwd=clone_b)


if __name__ == "__main__":
    unittest.main()
