import os
import re


def clean_file(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()

    # Remove lines containing tenant=... or tenant_id=...
    content = re.sub(r"^\s*tenant_id=.*$\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*tenant=.*$\n", "", content, flags=re.MULTILINE)

    # Remove imports
    content = re.sub(
        r"^from .*tenants\.models import Tenant.*$\n", "", content, flags=re.MULTILINE
    )

    # Replaces in format strings
    content = re.sub(r" for tenant \{instance\.tenant\.name\}", "", content)
    content = re.sub(r" for tenant \{request\.tenant\}", "", content)
    content = re.sub(r"self\.tenant = tenant\n", "", content)

    with open(filepath, "w") as f:
        f.write(content)


for root, _, files in os.walk("backend/apps"):
    for file in files:
        if file.endswith(".py"):
            clean_file(os.path.join(root, file))
