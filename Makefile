cov:
	coverage run jwzthreading/tests/test_jwz.py
	coverage annotate -d /tmp/ jwzthreading/jwzthreading.py
