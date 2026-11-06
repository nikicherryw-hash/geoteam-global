"""Install only a staging pilot-service model override; never edit shared secrets."""
from pathlib import Path

if not Path('/srv/geoteam-staging/current').is_dir():
    raise SystemExit('REFUSED_NOT_STAGING_HOST')
path = Path('/etc/systemd/system/geoteam-ai-pilot.service.d/90-geoteam-staging-model.conf')
if path.exists() and path.read_text() != '[Service]\nEnvironment=GEOTEAM_OPENAI_MODEL=gpt-6.1-sol\n':
    raise SystemExit('REFUSED_OVERRIDE_EXISTS')
path.parent.mkdir(parents=True, exist_ok=True)
model_file = path.parent / 'geoteam-staging-model.env'
model_file.write_text('GEOTEAM_OPENAI_MODEL=gpt-6.1-sol\n', encoding='utf-8')
path.write_text('[Service]\nEnvironmentFile=' + str(model_file) + '\n', encoding='utf-8')
print('STAGING_MODEL_OVERRIDE_INSTALLED')
