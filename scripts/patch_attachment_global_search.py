from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
for old,new in [
    ("'max_tool_calls': 2", "'max_tool_calls': 5"),
    ("timeout=85", "timeout=httpx.Timeout(150.0, connect=10.0)"),
    ("await attach_source_images(report['_internal_sources'])", "await attach_source_images(report['_internal_sources'], report['offers'])"),
]:
    if text.count(old) != 1:
        raise SystemExit('REFUSED_ATTACHMENT_MARKER: ' + old)
    text = text.replace(old,new,1)
path.with_name(path.name + '.global.new').write_text(text,encoding='utf-8')
print('CANDIDATE_READY')
