# Accounts Service BUILD file

python_sources(
    name="accounts",
    dependencies=[
        ":accounts-requirements",
    ],
)

python_requirements(
    name="accounts-requirements",
    source="requirements.txt",
)

pex_binary(
    name="accounts-server",
    entry_point="main.py",
    dependencies=[":accounts"],
)

