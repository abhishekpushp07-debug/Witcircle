"""One-shot PDF organiser. Invoked by sandbox.py, never as a server.

Loads trusted libraries/input bytes, then seals filesystem/network/process access
before opening an untrusted PDF. Returns bounded JSON and rendered PNGs on stdout.
"""
import base64
import codecs
import ctypes
import ctypes.util
import hashlib
import json
import math
import os
import re
import resource
import sys
import unicodedata
import fitz

LIMIT = 50 * 1024 * 1024
OUTPUT_LIMIT = 48 * 1024 * 1024
ANCHOR = re.compile(r'^(?:(?:Q(?:uestion)?\.?\s*)(\d{1,3})\s*[.:)\-]?\s*|(\d{1,3})\s*[.)]\s+)(.*)$', re.I)
SUBJECT = re.compile(r'^(Physics|Chemistry|Mathematics|Maths|English|Logical Reasoning|Biology)\b', re.I)
KEY = re.compile(r'(?:\bAnswer|\bAns\.?|\bCorrect\s+(?:option|answer))\s*(?:is\s*)?[:=\-]?\s*[\[(]?\s*([A-D](?![A-Za-z])|[+\-]?\d+(?![\d.]))\s*[\])]?', re.I)


def seal(directory):
    lib = ctypes.CDLL(ctypes.util.find_library('seccomp') or '')
    lib.seccomp_init.argtypes = [ctypes.c_uint32]; lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]; lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]; lib.seccomp_release.argtypes = [ctypes.c_void_p]
    if os.geteuid() != 0:
        raise RuntimeError('Required parser isolation unavailable')
    resource.setrlimit(resource.RLIMIT_CPU,(35,35))
    resource.setrlimit(resource.RLIMIT_AS,(1024*1024*1024,1024*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.chroot(directory); os.chdir('/')
    os.setgroups([]); os.setgid(65534); os.setuid(65534)
    libc=ctypes.CDLL(None)
    if libc.prctl(38,1,0,0,0) != 0:
        raise RuntimeError('Required parser isolation unavailable')
    ctx=lib.seccomp_init(0x7fff0000)
    if not ctx:
        raise RuntimeError('Required parser isolation unavailable')
    denied='open openat openat2 creat mkdir mkdirat unlink unlinkat rename renameat renameat2 link linkat symlink symlinkat socket socketpair connect bind listen accept accept4 sendto recvfrom ptrace execve execveat fork vfork clone clone3 mount umount2 chroot pivot_root unshare setns kill tgkill'.split()
    for name in denied:
        number=lib.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and lib.seccomp_rule_add(ctx,0x00050000|1,number,0) != 0:
            raise RuntimeError('Required parser isolation unavailable')
    if lib.seccomp_load(ctx) != 0:
        raise RuntimeError('Required parser isolation unavailable')
    lib.seccomp_release(ctx)


def open_pdf(data):
    if not data.startswith(b'%PDF-') or not 0 < len(data) <= LIMIT:
        raise ValueError('Use valid PDFs of at most50MB each')
    doc=fitz.open(stream=data,filetype='pdf')
    if doc.is_encrypted or not 1 <= len(doc) <= 300:
        raise ValueError('Use unlocked PDFs of1–300pages')
    if any(p.rect.width>2000 or p.rect.height>2000 for p in doc):
        raise ValueError('Export standard-size PDF pages')
    return doc


def segment(doc):
    anchors=[]; headings=[]; columns={}; extracted=0
    for pi,page in enumerate(doc):
        lines=[]
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                text=''.join(span['text'] for span in line['spans']).strip()
                if text:
                    lines.append((line['bbox'],text))
                    extracted+=len(text)
        if extracted>3000000:
            raise ValueError('The PDF has too much text; split the paper')
        found=[]
        for box,text in lines:
            m=ANCHOR.match(text)
            if m and 1<=int(m[1] or m[2])<=500 and (box[0]<page.rect.width*.27 or page.rect.width*.46<box[0]<page.rect.width*.68):
                found.append({'number':int(m[1] or m[2]),'page':pi,'top':max(12,box[1]-5),'x':box[0],'header':m[3].strip()})
        two=bool(any(a['x']<page.rect.width*.3 for a in found) and any(a['x']>page.rect.width*.46 for a in found))
        columns[pi]=2 if two else 1
        for a in found:
            a['col']=int(two and a['x']>page.rect.width*.46)
            anchors.append(a)
        for box,text in lines:
            m=SUBJECT.match(text)
            if m and len(text)<90:
                headings.append((pi,int(two and box[0]>page.rect.width*.46),box[1],m[1].title().replace('Maths','Mathematics')))
    anchors.sort(key=lambda a:(a['page'],a['col'],a['top']))
    if not anchors or len(anchors)>300:
        raise ValueError('No reliable numbered questions found. Upload a searchable PDF with numbered questions and solutions')
    slots=[(p,c) for p in range(len(doc)) for c in range(columns[p])]
    records=[]
    for index,a in enumerate(anchors):
        start_slot=slots.index((a['page'],a['col']))
        end=anchors[index+1] if index+1<len(anchors) else None
        end_slot=slots.index((end['page'],end['col'])) if end else len(slots)-1
        if end_slot-start_slot>5:
            raise ValueError('A question spans too many regions; check the PDF numbering')
        refs=[]; texts=[]
        for slot in range(start_slot,end_slot+1):
            p,c=slots[slot]; page=doc[p]; width=page.rect.width
            top=a['top'] if slot==start_slot else 25
            bottom=end['top']-2 if end and slot==end_slot else page.rect.height-25
            if bottom<=top+3: continue
            x0=16 if c==0 else width*.49
            x1=width-16 if columns[p]==1 or c==1 else width*.49-4
            rect=fitz.Rect(x0,top,x1,bottom)
            text=page.get_text(clip=rect).strip()
            if text:
                if len(text)>30000: raise ValueError('A question is too large; check numbering')
                refs.append({'page':p+1,'rect':[round(v,2) for v in rect]})
                texts.append(text)
        before=[h for h in headings if (h[0],h[1],h[2]) <= (a['page'],a['col'],a['top']+6)]
        subject=before[-1][3] if before else 'General'
        records.append({**a,'subject':subject,'refs':refs,'text':'\n'.join(texts)})
    return records


def organise(qdoc,sdoc):
    questions=segment(qdoc); solutions=segment(sdoc)
    output=[]; issues=[]; matched_solution_ids=set(); seen=set(); asset_bytes=0
    header=' '.join(qdoc[p].get_text()[:12000] for p in range(min(2,len(qdoc))))
    exam='BITSAT' if re.search(r'\bBITSAT\b',header,re.I) else 'JEE Main'
    duration=180
    time=re.search(r'(?:duration|time allowed)\s*[:=]\s*(\d+)\s*(minutes?|mins?|hours?|hrs?)',header,re.I)
    if time: duration=min(360,max(1,int(time[1])*(60 if time[2].lower().startswith(('h','hr')) else 1)))
    for order,q in enumerate(questions,1):
        local=[]
        identity=(q['subject'],q['number'])
        if identity in seen: local.append('Duplicate question identity')
        seen.add(identity)
        candidates=[(i,s) for i,s in enumerate(solutions) if s['number']==q['number'] and (s['subject']==q['subject'] or 'General' in (s['subject'],q['subject']))]
        solution=candidates[0][1] if len(candidates)==1 else None
        if solution is None: local.append('No unique matching solution')
        else: matched_solution_ids.add(candidates[0][0])
        labels=set(re.findall(r'\(([A-D1-4])\)',q['text']))
        labels.update(re.findall(r'(?:^|\n)\s*([A-D])[.)]\s',q['text']))
        family='ABCD' if set('ABCD')<=labels else '1234' if set('1234')<=labels else ''
        kind='mcq' if family else 'integer'
        keys=set(m[1].upper() for m in KEY.finditer(solution['text'] if solution else ''))
        if not keys and solution:
            bare=re.match(r'^\s*[\[(]([A-D1-4])[\])]\s*(?:$|[.:])',solution['header'])
            if bare: keys.add(bare[1])
        answer=next(iter(keys)) if len(keys)==1 else ''
        if not answer: local.append('A single explicit answer key is required in the solution')
        if kind=='mcq' and answer and answer not in family:
            # A numbered key is accepted for lettered options only as explicit1–4mapping.
            if family=='ABCD' and answer in '1234' and len(answer)==1: answer='ABCD'[int(answer)-1]
            elif family=='1234' and answer in 'ABCD': answer=str('ABCD'.index(answer)+1)
            else: local.append('Answer key does not match the option labels')
        if kind=='integer' and answer and not re.fullmatch(r'[+-]?\d{1,20}',answer):
            local.append('Options or an exact integer answer could not be identified')
        if kind=='integer' and answer and re.fullmatch(r'[+-]?\d{1,20}',answer): answer=str(int(answer))
        options={}
        if family:
            pattern=r'(?:\((['+family+r'])\)|(?:^|\n)\s*(['+family+r'])[.)]\s)'
            matches=list(re.finditer(pattern,q['text']))
            for n,m in enumerate(matches):
                label=m[1] or m[2]
                end=matches[n+1].start() if n+1<len(matches) else len(q['text'])
                options[label]=q['text'][m.end():end].strip()[:8192] or 'See source option '+label
        assets={'question':[],'solution':[]}
        for role,doc,record in [('question',qdoc,q),('solution',sdoc,solution)]:
            if not record: continue
            for ref in record['refs']:
                rect=fitz.Rect(ref['rect']); scale=min(1.6,math.sqrt(3000000/max(1,rect.width*rect.height)))
                raw=doc[ref['page']-1].get_pixmap(matrix=fitz.Matrix(scale,scale),clip=rect,alpha=False).tobytes('png')
                asset_bytes+=len(raw)
                if asset_bytes>32*1024*1024: raise ValueError('Rendered paper is too large; split it into smaller tests')
                assets[role].append(base64.b64encode(raw).decode('ascii'))
        output.append({'number':order,'source_number':q['number'],'solution_number':order if solution else None,
            'source_solution_number':solution['number'] if solution else None,'subject':q['subject'],'section':q['subject'],
            'type':kind,'text':q['text'],'options':options,'answer':answer,'solution':solution['text'] if solution else '',
            'topic':'','difficulty':'','render_mode':'source','q_refs':q['refs'],'s_refs':solution['refs'] if solution else [],
            'assets':assets,'issues':local,'pairing_evidence':'Exact source number and compatible section; explicit key only'})
        issues.extend({'question':order,'message':message} for message in local)
    unmatched=len(solutions)-len(matched_solution_ids)
    if unmatched: issues.append({'question':None,'message':f'{unmatched} solution entries did not match a question'})
    return {'questions':output,'issues':issues,'unmatched_solutions':unmatched,'exam':exam,'duration_minutes':duration,
            'source_pages':{'questions':len(qdoc),'solutions':len(sdoc)},'sandbox':'chroot_low_uid_seccomp_resource_limits'}


def main():
    try:
        directory=sys.argv[1]
        with open(os.path.join(directory,'questions.pdf'),'rb') as f: qdata=f.read(LIMIT+1)
        with open(os.path.join(directory,'solutions.pdf'),'rb') as f: sdata=f.read(LIMIT+1)
        # Warm encoders before denying filesystem access.
        json.dumps({'text':'हिन्दी'},ensure_ascii=False).encode('utf-8')
        unicodedata.normalize('NFC','test')
        codecs.lookup('raw_unicode_escape')
        codecs.lookup('unicode_escape')
        seal(directory)
        qdoc=open_pdf(qdata); sdoc=open_pdf(sdata)
        result=organise(qdoc,sdoc)
        encoded=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        if len(encoded)>OUTPUT_LIMIT: raise ValueError('Organised output exceeds its safe size limit')
        sys.stdout.buffer.write(encoded)
    except ValueError as exc:
        sys.stdout.write(json.dumps({'error':'The PDFs could not be organised safely. '+str(exc)[:200]}))
        sys.exit(2)
    except Exception:
        sys.stdout.write(json.dumps({'error':'Safe PDF processing could not complete. Use searchable, unlocked PDFs with clear numbering and explicit answer keys.'}))
        sys.exit(3)


if __name__=='__main__': main()
