from pathlib import Path

from mypyc.build import mypycify

pwd = Path("src/asgi_etags/")
FILES = [str(file) for file in pwd.glob("**/*.py")]

print(FILES)

def pdm_build_hook_enabled(context):
    return context.target != "sdist"


def pdm_build_update_setup_kwargs(context, setup_kwargs) -> None:
    setup_kwargs.update(
        ext_modules=mypycify(
            paths=FILES,
            target_dir="build/mypy-out/",
            multi_file=False,
            separate=False,
        )
    )
