# Accounts Service BUILD file

python_sources(
    name="accounts",
    dependencies=[
        ":accounts-requirements",
        "shared/events",
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

docker_image(
    name="accounts-image",
    source="Dockerfile",
    context_root="../..",
    image_tags=["latest", "{env.GIT_SHA}"],
    dependencies=[":accounts"],
)

