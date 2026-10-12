"""Real-function audit regressions. RED means unresolved, never a passing repair.

Only A06 stubs parser/storage bytes. A02/A03 use forwarding read barriers;
A05 pauses the real grader; A06 replaces lease at the destination-write boundary.
"""
import asyncio
import copy
from uuid import uuid4
import pytest

pytestmark = pytest.mark.asyncio(loop_scope='session')

from fastapi import HTTPException, BackgroundTasks


class OpenInvariant(AssertionError):
    """Only the final known invariant may produce an expected failure."""


def correct(condition, name):
    if not condition:
        raise OpenInvariant(name)


def question(number=1):
    return {'id': str(uuid4()), 'number': number, 'solution_number': number,
            'subject': 'Physics', 'section': 'Physics', 'type': 'mcq',
            'text': 'Synthetic isolated practice item', 'options': {'1': 'One', '2': 'Two'},
            'answer': '1', 'solution': 'Synthetic solution', 'approved': True, 'issues': [],
            'render_mode': 'typed', 'q_refs': [], 's_refs': [], 'topic': 'Synthetic',
            'difficulty': 'Easy', 'review_note': '', 'accessible_text': '',
            'solution_accessible_text': '', 'disposition': 'standard'}


def source_set():
    return {'id': str(uuid4()), 'title': 'ISOLATED SYNTHETIC PRACTICE', 'exam': 'JEE Main',
            'status': 'published', 'revision': 1, 'version': 1, 'questions': [question(), question(2)],
            'rules': {'minutes': 0, 'correct': 4, 'wrong': -1, 'skipped': 0,
                      'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
            'audience': 'all', 'expires': None, 'rights_upload': True, 'rights_publish': True,
            'rights_report': True, 'file_ids': [], 'source': 'Synthetic isolated fixture',
            'attribution': 'Not approved academic content', 'profile_mode': 'practice'}


async def same_preimage(monkeypatch, content, set_id):
    original, arrivals, gate = content.get, 0, asyncio.Event()
    async def read(collection, id):
        nonlocal arrivals
        value = await original(collection, id)
        if collection is content.sets and id == set_id:
            arrivals += 1
            if arrivals == 2:
                gate.set()
            await asyncio.wait_for(gate.wait(), 3)
        return value
    monkeypatch.setattr(content, 'get', read)


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A01; permanent repair Packet 06')
async def test_a01_retry_alias_survives_completed_retry(clean_db, synthetic_student_user):
    from tejas import attempts, corrections
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    u = synthetic_student_user
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(start_key='initial-' + str(uuid4()), device_checked=True), u)
    await attempts.finalize(a['id'])
    await corrections.freeze_ledger(await attempts.owned(a['id'], u))
    r1 = await attempts.retry(a['id'], {'start_key': 'retry-first-' + str(uuid4())}, u)
    key2 = 'retry-second-' + str(uuid4())
    assert (await attempts.retry(a['id'], {'start_key': key2}, u))['id'] == r1['id']
    await attempts.finalize(r1['id'])
    replay = await attempts.retry(a['id'], {'start_key': key2}, u)
    correct(replay['id'] == r1['id'], 'A01: accepted retry alias lost after completion')


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A02; permanent repair Packet 05')
async def test_a02_publish_has_one_same_version_archive(clean_db, synthetic_owner_user, monkeypatch):
    from tejas import content, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    s = source_set()
    s.update(status='review', version=0)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await same_preimage(monkeypatch, content, s['id'])
    outcomes = await asyncio.gather(*(content.publish(s['id'], {'confirm': True}, synthetic_owner_user) for _ in range(2)), return_exceptions=True)
    # Only a real optimistic conflict is acceptable; any fixture/parser failure is an ERROR.
    for result in outcomes:
        if isinstance(result, Exception) and not (isinstance(result, HTTPException) and result.status_code in (409, 412)):
            raise result
    rows = await clean_db.tejas_versions.count_documents({'set_id': s['id'], 'version': 1})
    assert rows >= 1, 'Fixture failed to publish any version'
    correct(rows == 1, 'A02: duplicate same-version archive')


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A03; permanent repair Packet 05')
async def test_a03_concurrent_question_edits_preserve_both(clean_db, synthetic_owner_user, monkeypatch):
    from tejas import content
    s = source_set()
    s['status'] = 'draft'
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await same_preimage(monkeypatch, content, s['id'])
    q1 = s['questions'][0]
    outcomes = await asyncio.gather(
        content.edit_question(s['id'], q1['id'], {'text': 'Editor one'}, synthetic_owner_user),
        content.edit_question(s['id'], q1['id'], {'solution': 'Editor two'}, synthetic_owner_user), return_exceptions=True)
    conflicts = 0
    for result in outcomes:
        if isinstance(result, HTTPException) and result.status_code in (409, 412):
            conflicts += 1
        elif isinstance(result, Exception):
            raise result
    final = await clean_db.tejas_sets.find_one({'id': s['id']})
    edited = next(q for q in final['questions'] if q['id'] == q1['id'])
    correct(conflicts == 1 or (edited['text'] == 'Editor one' and edited['solution'] == 'Editor two'), 'A03: accepted edit overwritten')


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A04; permanent repair Packet 05')
async def test_a04_unknown_audience_denied():
    from tejas.content import permitted
    correct(permitted({'audience': 'unknown-private-value', 'expires': None}, None) is False,
            'A04: unknown audience failed open')


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A05; permanent repair Packet 04')
async def test_a05_waiting_grade_job_drains_without_second_trigger(clean_db, synthetic_student_user, monkeypatch):
    from tejas import jobs, corrections
    from tejas.db import now
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    monkeypatch.setitem(jobs.LANE_LIMITS, 'grade', 1)
    jobs._active['grade'].clear()
    entered, release = asyncio.Event(), asyncio.Event()
    original = corrections.freeze_ledger
    calls = 0
    async def paused_real_grader(a):
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await asyncio.wait_for(release.wait(), 3)
        return await original(a)
    monkeypatch.setattr(corrections, 'freeze_ledger', paused_real_grader)
    ids = []
    for _ in range(2):
        s = source_set()
        a = {**s, 'id': str(uuid4()), 'set_id': s['id'], 'user_id': synthetic_student_user['id'],
             'mode': 'practice', 'start_key': str(uuid4()), 'status': 'completed', 'answers': {}, 'started_at': now(), 'submitted_at': now(), 'deadline': 0}
        await clean_db.tejas_attempts.insert_one(a)
        j = await jobs.enqueue('grade', a['user_id'], a['set_id'], {'attempt_id': a['id']})
        ids.append(j['id'])
    first = asyncio.create_task(jobs.run_job(ids[0]))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        await jobs.run_job(ids[1])
        assert (await clean_db.tejas_jobs.find_one({'id': ids[1]}))['status'] == 'queued'
        release.set()
        await asyncio.wait_for(first, 3)
        assert (await clean_db.tejas_jobs.find_one({'id': ids[0]}))['status'] == 'done'
        await asyncio.sleep(0.1)  # No periodic worker exists: no second explicit trigger.
        final = await clean_db.tejas_jobs.find_one({'id': ids[1]})
        correct(final['status'] == 'done', 'A05: persisted waiting job never dispatches after slot release')
    finally:
        release.set()
        if not first.done():
            first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        jobs._active['grade'].clear()


@pytest.mark.xfail(strict=True, raises=OpenInvariant, reason='OPEN A06; permanent repair Packet 04')
async def test_a06_replaced_lease_cannot_write_destination(clean_db, synthetic_owner_user, monkeypatch):
    from tejas import jobs, safety
    monkeypatch.setattr(safety, 'HELD_CAPABILITIES', frozenset())
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    s = source_set()
    s.update(status='draft', questions=[])
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    fid = str(uuid4())
    await clean_db.tejas_files.insert_one({'id': fid, 'path': 'synthetic-no-network'})
    j = await jobs.enqueue('extract', synthetic_owner_user['id'], s['id'], {'qfile': fid, 'sfile': fid, 'revision': s['revision']})
    proposal = [question()]
    async def fake_threadpool(fn, *args, **kwargs):
        if fn is jobs.get_object:
            return b'synthetic-parser-fixture'
        if fn is jobs.build_questions:
            return copy.deepcopy(proposal)
        raise RuntimeError('Unexpected extraction dependency')
    monkeypatch.setattr(jobs, 'run_in_threadpool', fake_threadpool)
    real_sets, injected = jobs.sets, []
    class DestinationBoundary:
        def __getattr__(self, name):
            return getattr(real_sets, name)
        async def update_one(self, query, update, *args, **kwargs):
            # Crucial: after real require_lease, immediately before real destination write.
            replaced = await clean_db.tejas_jobs.update_one({'id': j['id'], 'status': 'running'}, {'$set': {'lease': str(uuid4())}})
            assert replaced.modified_count == 1
            injected.append(True)
            return await real_sets.update_one(query, update, *args, **kwargs)
    monkeypatch.setattr(jobs, 'sets', DestinationBoundary())
    await jobs.run_job(j['id'])
    assert injected == [True], 'Lease injection never reached destination boundary'
    final = await real_sets.find_one({'id': s['id']})
    correct(final['questions'] == [] and final['revision'] == s['revision'], 'A06: stale extraction wrote academic destination')


async def test_motor_namespace_guards(test_client):
    from motor.motor_asyncio import AsyncIOMotorDatabase
    with pytest.raises(RuntimeError, match='boundary violation'):
        test_client['forbidden']
    with pytest.raises(RuntimeError, match='boundary violation'):
        test_client.get_database('forbidden')
    with pytest.raises(RuntimeError, match='boundary violation'):
        AsyncIOMotorDatabase(test_client, 'forbidden')
    with pytest.raises(RuntimeError, match='boundary violation'):
        await test_client.drop_database('forbidden')


async def test_held_jobs_preserve_exact_intent_before_lease(clean_db, monkeypatch):
    from tejas import jobs
    monkeypatch.setattr(jobs, 'INLINE_JOBS', True)
    for kind in ('extract', 'regrade'):
        j = {'id': str(uuid4()), 'kind': kind, 'status': 'queued', 'attempts': 0, 'lease_until': 0, 'payload': {}}
        await clean_db.tejas_jobs.insert_one(copy.deepcopy(j))
        await jobs.run_job(j['id'])
        after = await clean_db.tejas_jobs.find_one({'id': j['id']}, {'_id': 0})
        assert after == j
        assert jobs.public_job(after)['processing_held'] is True
    assert jobs.job_held('grade') is False and jobs.job_held('report') is False


async def test_hold_rejects_without_receiving_body():
    from tejas.safety import ContentSafetyHold
    async def never(*args, **kwargs):
        raise RuntimeError('Held request reached body parser or downstream app')
    sent = []
    async def send(message):
        sent.append(message)
    scope = {'type': 'http', 'method': 'POST', 'path': '/api/studio/sets/synthetic/files',
             'headers': [(b'content-type', b'multipart/form-data; boundary=broken'), (b'content-length', b'999999999999')]}
    await ContentSafetyHold(never)(scope, never, send)
    assert sent[0]['status'] == 503


async def test_direct_protected_functions_deny_before_lookup():
    from tejas import content, corrections, jobs
    calls = [content.publish('missing', {}, {}), content.extract('missing', {}, BackgroundTasks(), {}),
             content.source_page('missing', 1, {}), content.source_text('missing', 1, {}),
             corrections.regrade('missing', {}, BackgroundTasks(), {}), corrections.run_regrade({}),
             jobs.enqueue('extract', 'u', 's', {}), jobs.enqueue('regrade', 'u', 's', {})]
    for call in calls:
        with pytest.raises(HTTPException) as exc:
            await call
        assert exc.value.status_code == 503


async def test_command_nested_body_is_immutable():
    from tejas.command_contracts import CommandIntent
    uid = str(uuid4())
    original = {'nested': {'values': [1, 2]}}
    intent = CommandIntent(tenant_id=uid, actor_id=uid, target_id=uid, operation='COMMIT',
                           request_key='synthetic-key', expected_version=1, writer_generation=1, body=original)
    before = intent.intent_digest()
    original['nested']['values'].append(3)
    with pytest.raises(TypeError):
        intent.body['nested']['values'].append(4)
    with pytest.raises(TypeError):
        intent.body['nested']['values'][0] = 9
    with pytest.raises(TypeError):
        intent.body.update({'other': True})
    assert intent.intent_digest() == before


async def test_phone_practice_save_resume_submit_preserved(http_client, clean_db):
    s = source_set()
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    login = await http_client.post('/api/auth/phone', json={'phone': '+12025550184'})
    assert login.status_code == 200
    assert login.json()['data']['access_type'] == 'unverified_phone'
    pf = await http_client.post(f'/api/sets/{s["id"]}/preflight', json={})
    assert pf.status_code == 200
    start = await http_client.post(f'/api/sets/{s["id"]}/start', json={'start_key': 'practice-' + str(uuid4()), 'device_checked': True})
    assert start.status_code == 200
    a = start.json()['data']
    assert 'answer' not in a['questions'][0]
    qid = s['questions'][0]['id']
    body = {'value': '1', 'revision': 1, 'request_id': 'answer-' + str(uuid4()), 'marked': False}
    url = f'/api/attempts/{a["id"]}/answers/{qid}'
    saved = await http_client.put(url, json=body)
    assert saved.status_code == 200
    duplicate = await http_client.put(url, json=body)
    assert duplicate.status_code == 200 and duplicate.json()['data']['duplicate'] is True
    resumed = await http_client.get(f'/api/attempts/{a["id"]}')
    assert resumed.json()['data']['answers'][qid]['value'] == '1'
    submitted = await http_client.post(f'/api/attempts/{a["id"]}/submit')
    assert submitted.status_code in (200, 202)
    replay = await http_client.post(f'/api/attempts/{a["id"]}/submit')
    assert replay.json()['data']['receipt'] == submitted.json()['data']['receipt']
    result = await http_client.get(f'/api/attempts/{a["id"]}/results')
    assert result.status_code == 200
    assert result.json()['data']['summary']['score_exact'] == '4'
