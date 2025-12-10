# Auth Service BUILD file

python_sources(
    name="auth",
    dependencies=[
        ":auth-requirements",
        "shared/events",
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

docker_image(
    name="auth-image",
    source="Dockerfile",
    context_root="../..",
    image_tags=["latest", "{env.GIT_SHA}"],
    dependencies=[":auth"],
)

