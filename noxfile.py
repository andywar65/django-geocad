import nox

# 5.0 of life April 2025
@nox.session(python=["3.10", "3.11", "3.12"])
def test510(session):
    session.install("django>=5.1,<5.2")
    session.run("./load_tests.py", external=True)