"""
Pre-flight validation for PMC daily report exports.

validate_daily_report_export(report) -> list[str]
  Hard errors have no prefix; warnings are prefixed "WARNING:".
  An empty list means the report is safe to export.
"""
from decimal import Decimal


def validate_daily_report_export(report):
    errors = []

    # FINAL status requires an approver
    if report.status == 'Approved' and report.approved_by is None:
        errors.append(
            'Approved By cannot be empty when report status is Approved (FINAL).'
        )

    # Equipment Standby/Breakdown must have remarks
    eq_records = report.equipment_records.select_related('equipment').all()
    for rec in eq_records:
        if rec.status in ('Standby', 'Breakdown') and not rec.remarks.strip():
            errors.append(
                f"Equipment '{rec.equipment.name}' has status '{rec.status}' "
                f"but Remarks is empty — a reason is required."
            )

    # Work activities must have at least one row
    if report.activities.count() == 0:
        errors.append('Work Activities table has 0 rows — at least one activity is required.')

    # Lookahead: warning only
    if report.lookaheads.count() == 0:
        errors.append('WARNING: Next Day Plan has 0 rows.')

    # No negative numeric values
    for rec in report.manpower_records.all():
        if rec.quantity < 0:
            errors.append(f"Manpower quantity for '{rec.company}' is negative ({rec.quantity}).")

    for rec in eq_records:
        if rec.working_hours < Decimal('0'):
            errors.append(
                f"Equipment '{rec.equipment.name}' has negative working hours ({rec.working_hours})."
            )

    for act in report.activities.all():
        if act.quantity is not None and act.quantity < Decimal('0'):
            errors.append(
                f"Activity '{act.description[:60]}' has negative quantity ({act.quantity})."
            )

    return errors
