"""Source guide04 metric identities and formulas. Never infer missing observational evidence."""
import json
from pathlib import Path
from fractions import Fraction
from pydantic import BaseModel, Field
from .scoring import canonical

REGISTRY=json.loads(Path(__file__).with_name('analytics_registry.json').read_text())

class Metric(BaseModel):
    metric_id:str
    name:str
    inputs:str
    formula:str
    evidence:str
    action:str
    limitation:str
    state:str='not_collected'
    reason:str='The required validated observations are not collected for this attempt.'
    value:int|float|str|dict|list|None=None
    unit:str=''
    sample_size:int=0
    question_ids:list[str]=Field(default_factory=list)
    scope:str='This attempt · frozen scoring version'

class Analysis(BaseModel):
    registry_version:str
    source_sha256:str
    metrics:list[Metric]
    available_count:int
    total_count:int=60
    computed_at:float
    score_version:str
    note:str='Descriptive practice evidence, not ability, admission readiness or official rank. Missing values are not zero. Wall-clock elapsed time is not focused study time.'


def build_analytics(attempt,result):
    rows=result['questions'];summary=result['summary']
    metrics={m['metric_id']:Metric(**m) for m in REGISTRY['metrics']}
    eligible=[q for q in rows if q['outcome'] not in ('dropped','bonus')]
    attempted=[q for q in eligible if q['outcome'] in ('correct','incorrect')]
    wrong=[q for q in eligible if q['outcome']=='incorrect']
    def put(n,value,items=eligible,unit='',reason='',state='available'):
        m=metrics[f'A{n:02d}'];m.value=value;m.state=state;m.reason=reason;m.unit=unit
        m.sample_size=len(items);m.question_ids=[q['id'] for q in items]
    def missing(n,reason,state='not_collected',items=eligible):put(n,None,items,reason=reason,state=state)
    pct=lambda a,b:round(100*a/b,2) if b else None
    p=Fraction(str(attempt['rules']['correct']));w=Fraction(str(attempt['rules']['wrong']))
    positive=sum((max(Fraction(q['marks_exact']),Fraction(0)) for q in eligible),Fraction(0))
    penalty=sum((max(-Fraction(q['marks_exact']),Fraction(0)) for q in rows),Fraction(0))
    # Identities A01–A09 exactly match the source catalogue; do not renumber these.
    put(1,summary['score'],rows,'marks','Net signed awarded marks, including separately identified special awards.')
    put(2,summary['correct'],[q for q in eligible if q['outcome']=='correct'],'questions','Fully correct ordinary responses; bonus/dropped excluded.')
    put(3,{'incorrect':summary['incorrect'],'partial_credit':0},wrong,'questions','The supported single-choice/integer adapters have no partial-credit outcome. Awards and dropped items are not incorrect responses.')
    if attempted:put(4,pct(summary['correct'],len(attempted)),attempted,'%',f"{summary['correct']}/{len(attempted)} attempted eligible responses. No strength label below 10 attempts.")
    else:missing(4,'No attempted eligible responses; accuracy is undefined.','unavailable',[])
    if eligible:put(5,pct(len(attempted),len(eligible)),eligible,'%',f'{len(attempted)}/{len(eligible)} eligible responses committed; {len(eligible)-len(attempted)} unanswered.')
    else:missing(5,'No ordinary eligible questions.','unavailable',[])
    put(6,float(positive),eligible,'marks','Sum of positive ordinary question marks, excluding bonus/award-only adjustments.')
    put(7,float(penalty),wrong,'marks','Magnitude of all negative ledger marks; zero is valid for a no-penalty preset.')
    if positive>0:put(8,round(float(100*penalty/positive),2),eligible,'%',f'Penalty {float(penalty)} / ordinary positive marks {float(positive)} × 100; not a probability.')
    else:missing(8,f'Ordinary positive marks are zero; ratio undefined. Penalty marks lost: {float(penalty)}.','unavailable',wrong)
    if summary['maximum']>0:put(9,pct(summary['score'],summary['maximum']),rows,'%',f"{summary['score']} / {summary['maximum']} configured maximum × 100. Negative values are not clamped.")
    else:missing(9,'The configured maximum is zero.','unavailable')
    grouped={}
    for q in rows:
        g=grouped.setdefault(q['type'],{'score':0.,'maximum':0.,'count':0})
        g['score']+=float(Fraction(q['marks_exact']));g['count']+=1
        if q['outcome']!='dropped':g['maximum']+=float(p)
    put(13,[{'type':k,**g,'score_ratio':round(g['score']/g['maximum'],6) if g['maximum']>0 else None} for k,g in grouped.items()],rows,'ratio','Signed score / configured maximum separately for each supported response type. No strategy recommendation below 10 items per type.')
    if not any(g['maximum']>0 for g in grouped.values()):missing(13,'All response-type maxima are zero.','unavailable')
    start=attempt.get('started_at');end=attempt.get('submitted_at')
    if start is not None and end is not None and end>=start:
        put(16,round(max(0,min(end,attempt.get('deadline') or end)-start),1),rows,'seconds','Server-authorized elapsed interval only; includes idle time. Never labelled focused time.')
    else:missing(16,'Complete ordered server clock ledger is missing.','unavailable')
    first=attempt.get('first_answers',{})
    history=attempt.get('answer_history_version')==1 and all(q['id'] in first for q in attempted)
    if history:
        revised=[];positive_delta=Fraction(0);negative_delta=Fraction(0)
        for q in eligible:
            initial=first.get(q['id'])
            if not initial:continue
            value=canonical(initial.get('value',''),q['type'])
            if value==q['normalized_response']:continue
            revised.append(q)
            initial_correct=value in [canonical(k,q['type']) for k in q['accepted_answers']]
            old=p if initial_correct else w if value else Fraction(0)
            delta=Fraction(q['marks_exact'])-old
            positive_delta+=max(delta,Fraction(0));negative_delta+=max(-delta,Fraction(0))
        put(24,float(positive_delta),revised,'marks','Positive part of final-minus-first-commit marks under the same key; exact descriptive differences, even after one revision. Not proof revision caused improvement.')
        put(25,float(negative_delta),revised,'marks','Negative part of final-minus-first-commit marks under the same key. Clears use the accepted final score; intermediate reversals excluded.')
        if attempt.get('deadline') and attempt['deadline']>start:
            boundary=start+0.8*(attempt['deadline']-start)
            late=[q for q in attempted if first[q['id']].get('accepted_at',0)>=boundary]
            early=[q for q in attempted if first[q['id']].get('accepted_at',0)<boundary]
            if all(isinstance(first[q['id']].get('accepted_at'), (int, float)) and start <= first[q['id']]['accepted_at'] <= attempt['deadline'] for q in attempted) and len(late)>=10 and len(early)>=10:
                put(26,{'late_accuracy_percent':pct(sum(q['outcome']=='correct' for q in late),len(late)),'earlier_accuracy_percent':pct(sum(q['outcome']=='correct' for q in early),len(early)),'late_count':len(late),'earlier_count':len(early)},attempted,'%', 'First commits in final 20% of authorized duration vs earlier; at least 10 items in each group.')
            else:missing(26,'Requires valid first-commit times and at least 10 items in EACH of the final 20% and earlier groups.','insufficient_sample',attempted)
        else:missing(26,'No authorized timed window.','unavailable')
    else:
        for n in (24,25,26):missing(n,'Complete first-commit history is not available. Older attempts are not retrospectively reconstructed.')
    for n in (10,11,12,14,47,51,54,55):missing(n,'Reviewed subject/chapter/concept/difficulty or confirmed error labels are absent; source-supplied tags are not substituted for approved evidence.')
    for n in (17,18,19,20,21,22,23,27,28,29,30,57,60):missing(n,'Validated visible-window, ordered review/navigation or preassigned timing events are not collected. Answer timestamps are not thinking time.')
    for n in range(31,41):missing(n,'Requires a finalized comparable first-exposure cohort of at least 100 learners plus the metric-specific sample and privacy thresholds. Unverified phone-profile standings are not that validated cohort.','unavailable')
    missing(40,'Requires at least 200 comparable first-exposure learners, 50 per rest-score group, nonconstant rest scores and documented boundary-tie weights.','unavailable')
    for n in (15,46,48,49,52,53):missing(n,'Canonical exposure state and the required approved comparable/fresh multi-attempt observations are not available.')
    for n in (41,42,43):missing(n,'Pre-commit confidence probabilities are not collected. They cannot be inferred from speed or correctness.')
    missing(44,'This is a hypothetical calculator, not an inferred ability metric. It needs a learner-supplied probability assumption.','unavailable')
    missing(45,'Optional learner-confirmed error labels are not collected. Error causes are never guessed.')
    missing(50,'No assigned review-task lifecycle is recorded; missed-question lists are not completed review tasks.')
    if attempt.get('solution_events_version')==1 and rows:
        opened=set(attempt.get('solution_opened',[]));put(56,pct(sum(q['id'] in opened for q in rows),len(rows)),rows,'%',f'{sum(q["id"] in opened for q in rows)}/{len(rows)} distinct authorized review expansions. Eligible review set: all released delivered questions. Opening is not proof of understanding.')
    else:missing(56,'A positive released set and explicit consultation logging are required; this attempt has no complete event history.')
    original=attempt.get('original_ledger')
    if original and attempt.get('regrade_reason'):
        old_rows={q['id']:q for q in original['rows']};changes=[];changed=[]
        for q in rows:
            before=old_rows.get(q['id'])
            if before is None:continue
            difference=Fraction(q['marks_exact'])-Fraction(before['marks_exact'])
            if difference:changes.append({'question':q['number'],'delta':float(difference)});changed.append(q)
        put(58,{'net_change':summary['score']-original['summary']['score'],'question_changes':changes},changed,'marks',attempt['regrade_reason'])
    else:missing(58,'Select a reviewed correction version with both reproducible ledgers and a published correction reason. Original results remain unchanged.','unavailable')
    if rows and all(isinstance(q.get('approved'),bool) for q in rows):
        approved=[q for q in rows if q['approved'] and (q.get('solution') or q.get('s_refs'))]
        put(59,pct(len(approved),len(rows)),rows,'%',f'{len(approved)}/{len(rows)} released delivered items have approved explanation mappings. Deterministic import pairing is not independent academic approval.')
    else:missing(59,'Approval provenance is incomplete. Structural source pairing is not presented as independent academic verification.')
    from .db import now
    values=list(metrics.values())
    return Analysis(registry_version=REGISTRY['registry_version'],source_sha256=REGISTRY['source_sha256'],metrics=values,
        available_count=sum(m.state=='available' for m in values),computed_at=now(),score_version=attempt.get('score_version','original')).model_dump()
