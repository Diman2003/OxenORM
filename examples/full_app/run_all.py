import asyncio, os, time, subprocess, sys


def compose_up():
    subprocess.run(["docker", "compose", "up", "-d"], cwd=os.path.join(os.getcwd(), "examples", "full_app"), check=True)
    time.sleep(8)


async def run():
    # Run business logic (models auto-create tables when engine is bound)
    import importlib
    mod = importlib.import_module('examples.full_app.business_logic')
    await mod.main()


if __name__ == '__main__':
    compose_up()
    # Ensure repo root on PYTHONPATH
    sys.path.insert(0, os.getcwd())
    asyncio.run(run())

