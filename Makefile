publish-test:
	rm -r dist/*
	python setup.py sdist
	twine upload -r pypitest dist/*

publish:
	rm -r -f dist/*
	python setup.py sdist
	twine upload dist/*
