"""Executable route catalogue built from actual FastAPI routes/dependencies.

No per-request database/global-catalogue dependency. Every mounted API operation
must have a reviewed local contract entry; unknown operations fail startup.
"""
from dataclasses import dataclass
from fastapi.routing import APIRoute
from .request_contracts import MODELS, EmptyPayload

# owner boundary, workload tier, current idempotency behavior
SPEC = {
    'server.health': ('public_liveness_only', 'normal', 'read'),
    'auth.register': ('removed_endpoint', 'normal', 'gone'),
    'auth.login': ('staff_password_session', 'normal', 'new_session'),
    'auth.session': ('cookie_identity', 'normal', 'read_refresh_side_effect'),
    'auth.me': ('current_identity', 'normal', 'read'),
    'auth.refresh': ('current_refresh_session', 'normal', 'session_refresh'),
    'auth.logout': ('current_cookie_sessions_only', 'normal', 'repeatable_delete'),
    'auth.preferences': ('current_profile_only', 'normal', 'replace_field'),
    'phone.access': ('unverified_phone_profile_only', 'normal', 'profile_upsert_new_session'),
    'content.catalogue': ('public_published_audience', 'normal', 'read'),
    'content.set_detail': ('public_published_audience', 'normal', 'read'),
    'content.studio_sets': ('authorized_editorial_workspace', 'control', 'read'),
    'content.create_set': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.studio_set': ('authorized_editorial_workspace', 'control', 'read'),
    'content.update_set': ('authorized_editorial_workspace', 'control', 'legacy_unfenced_edit'),
    'content.upload': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_page': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_text': ('authorized_private_source', 'batch', 'HELD'),
    'content.source_download': ('authorized_private_source', 'normal', 'read'),
    'content.extract': ('authorized_editorial_workspace', 'batch', 'HELD'),
    'content.add_question': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.edit_question': ('authorized_editorial_workspace', 'control', 'legacy_unfenced_edit'),
    'content.approve_question': ('authorized_editorial_workspace', 'control', 'revision_CAS'),
    'content.publish': ('owner_publication_rights', 'control', 'HELD'),
    'content.withdraw': ('owner_publication_rights', 'control', 'repeatable_state_change_audit_each_call'),
    'content.subset': ('authorized_editorial_workspace', 'control', 'not_idempotent'),
    'content.preview_asset': ('authorized_private_source', 'batch', 'HELD'),
    'answers.save_answer': ('attempt_owner_active_deadline', 'live', 'stored_request_receipt_CAS'),
    'attempts.my_sets': ('current_profile_audience', 'normal', 'read'),
    'attempts.my_set': ('current_profile_audience', 'normal', 'read'),
    'attempts.preflight': ('current_profile_audience_or_staff_preview', 'normal', 'upsert_preflight'),
    'attempts.start': ('current_profile_audience_or_staff_preview', 'live', 'start_key_receipt_legacy'),
    'attempts.history': ('attempt_owner', 'normal', 'read_with_expiry_side_effect'),
    'attempts.read_attempt': ('attempt_owner', 'live', 'read_with_expiry_side_effect'),
    'attempts.visit_question': ('attempt_owner_active_deadline', 'live', 'set_membership'),
    'attempts.submit': ('attempt_owner', 'live', 'atomic_seal_receipt'),
    'attempts.results': ('attempt_owner_and_solution_release', 'normal', 'read_grade_enqueue_side_effect'),
    'attempts.asset': ('attempt_owner_and_solution_release', 'normal', 'read_with_expiry_side_effect'),
    'attempts.retry': ('attempt_owner_frozen_grade', 'normal', 'KNOWN_A01_alias_gap'),
    'attempts.report': ('attempt_owner_and_report_rights', 'batch', 'versioned_report_job'),
    'jobs.status': ('job_owner_or_staff_set_scope', 'normal', 'read_dispatch_side_effect'),
    'jobs.retry_job': ('job_owner_or_staff_set_scope', 'batch', 'job_state_retry'),
    'jobs.download': ('job_owner_and_report_rights', 'normal', 'read'),
    'jobs.cron': ('cron_secret_dependency', 'batch', 'maintenance_replay'),
    'reviewers.update_access': ('owner_reviewer_administration', 'control', 'role_replace'),
    'profiles.profiles': ('authorized_editorial_workspace', 'control', 'read'),
    'corrections.regrade': ('owner_scoring_successor', 'batch', 'HELD'),
    'engineering.capacity_profile': ('staff_engineering_only', 'normal', 'read'),
    'engineering.safety_status': ('staff_engineering_only', 'normal', 'read'),
}


@dataclass(frozen=True)
class RouteContract:
    route: APIRoute
    key: str
    owner: str
    tier: str
    idempotency: str
    roles: tuple[str, ...]
    body_limit: int
    model: type | None
    json_body: bool


def roles(dependant):
    names = set()
    def visit(dep):
        names.add(getattr(dep.call, '__name__', ''))
        for child in dep.dependencies:
            visit(child)
    visit(dependant)
    if 'owner' in names:
        return ('owner',)
    if 'staff' in names:
        return ('owner', 'reviewer')
    if 'current' in names:
        return ('authenticated_profile',)
    return ('public_or_handler_checked',)


def install_contracts(app):
    registry = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith('/api/'):
            continue
        module = route.endpoint.__module__.split('.')[-1]
        key = module + '.' + route.endpoint.__name__
        if key not in SPEC:
            raise RuntimeError('API route lacks an explicit local contract: ' + key)
        owner, tier, idem = SPEC[key]
        writes = bool(route.methods & {'POST', 'PUT', 'PATCH', 'DELETE'})
        upload = key == 'content.upload'
        model = (MODELS.get(key, EmptyPayload) if writes and not upload else None)
        if writes and not upload and route.body_field and key not in MODELS:
            raise RuntimeError('Body-bearing route lacks an explicit input model: ' + key)
        limit = 256 * 1024 if key == 'content.edit_question' else 64 * 1024 if key in ('content.create_set', 'content.update_set', 'content.subset') else 4096
        if not writes or upload:
            limit = 0
        registry.append(RouteContract(route, key, owner, tier, idem, roles(route.dependant), limit, model, writes and not upload))
    app.state.route_contracts = tuple(registry)
    original = app.openapi
    def openapi():
        spec = original()
        components = spec.setdefault('components', {}).setdefault('schemas', {})
        for c in registry:
            for method in c.route.methods:
                operation = spec['paths'].get(c.route.path, {}).get(method.lower())
                if not operation:
                    continue
                operation.update({'x-owner-policy': c.owner, 'x-role-scope': list(c.roles),
                    'x-workload-tier': c.tier, 'x-idempotency-mode': c.idempotency,
                    'x-body-limit-bytes': c.body_limit, 'x-contract-stage': 'pilot_ingress_not_qualified_live_cell'})
                if c.model:
                    schema = c.model.model_json_schema(ref_template='#/components/schemas/{model}')
                    components.update(schema.pop('$defs', {}))
                    components[c.model.__name__] = schema
                    operation['requestBody'] = {'required': bool(c.route.body_field and c.route.body_field.required),
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/' + c.model.__name__}}}}
                operation['x-known-gaps'] = ['Target SQL authority, field-level response DTOs and cross-resource transaction proof are separate qualification requirements']
        return spec
    app.openapi = openapi
    return tuple(registry)
