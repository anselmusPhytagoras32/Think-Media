"""FR05: reproducible fictional one-page PDF for local presentation uploads."""
from pathlib import Path

target = Path(__file__).resolve().parents[1] / 'presentation' / 'fictional-resume.pdf'
target.parent.mkdir(exist_ok=True)
lines = [
    'FICTIONAL PRESENTATION DOCUMENT',
    'ThinkMedia sample application attachment',
    '',
    'Applicant: Presentation Student (synthetic)',
    'Email: presentation-student@example.test',
    'Institution: Demo Campus (fictional)',
    'Program: BS Information Technology',
    '',
    'Practice skills: React, Python, SQL, accessible web interfaces',
    'Practice project: a fictional learning-resource search page',
    '',
    'This document contains no real personal or employment information.',
    'Use it to demonstrate private PDF upload, review and download.',
    'It is not an actual resume, vacancy application or research observation.',
]
commands = ['BT /F1 13 Tf 50 780 Td 21 TL']
for index, line in enumerate(lines):
    escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    commands.append(('T* ' if index else '') + f'({escaped}) Tj')
commands.append('ET')
stream = '\n'.join(commands).encode('ascii')
objects = [
    b'<< /Type /Catalog /Pages 2 0 R >>',
    b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
]
output = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
offsets = [0]
for index, obj in enumerate(objects, 1):
    offsets.append(len(output))
    output.extend(str(index).encode() + b' 0 obj\n' + obj + b'\nendobj\n')
startxref = len(output)
output.extend(b'xref\n0 6\n0000000000 65535 f \n')
for offset in offsets[1:]:
    output.extend(f'{offset:010d} 00000 n \n'.encode())
output.extend(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n'.encode())
if target.exists():
    if target.read_bytes() != output:
        raise SystemExit('Existing sample differs; preserve it and review before regenerating.')
else:
    with target.open('xb') as file:
        file.write(output)
print(f'Fictional sample PDF ready: {target.name} ({len(output)} bytes)')
