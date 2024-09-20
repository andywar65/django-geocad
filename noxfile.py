import nox

# 4.2 is LTS end of life April 2026


@nox.session(python=["3.9", "3.10", "3.12"])
def test420(session):
    session.install("django>=4.2,<4.3")
    session.run("./load_tests.py", external=True)


# 5.0 of life April 2025
@nox.session(python=["3.10", "3.12"])
def test510(session):
    session.install("django>=5.1,<5.2")
    session.run("./load_tests.py", external=True)
