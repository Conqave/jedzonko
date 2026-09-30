from django.core.management.base import OutputWrapper

from catalog.application.reference_import import ReferenceImportRun


def write_reference_report(run: ReferenceImportRun, output: OutputWrapper) -> None:
    output.write(
        f"Updated {len(run.updated)}, unchanged {len(run.unchanged)}, "
        f"skipped manual {len(run.skipped_manual)}, unknown {len(run.unknown)}."
    )
    for entry in run.updated:
        output.write(f"  + {entry.tag_name} ({entry.fact.value})")
    for entry in run.skipped_manual:
        output.write(f"  = {entry.tag_name} ({entry.fact.value}, manual value kept)")
    for tag_name in run.unknown:
        output.write(f"  ? {tag_name}")
