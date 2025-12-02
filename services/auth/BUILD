# Auth Service BUILD file

python_sources(
    name="auth",
    dependencies=[
        ":auth-requirements",
    ],
)

python_requirements(
    name="auth-requirements",
    source="requirements.txt",
)

pex_binary(
    name="auth-server",
    entry_point="main.py",
    dependencies=[":auth"],
)


