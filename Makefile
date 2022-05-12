.PHONY: package clean test image docker-compose configmap pex deploy redeploy
.DEFAULT_GOAL : package

clean:
	rm -rf dist *.egg-info htmlcov .coverage .pytest_cache include build __pycache__

cleanCache:
	rm -rf .tmp

resolve:
	poetry install --no-dev

assemble: clean
	rm -rf build.py src/version.py 
	touch build.py src/version.py
	echo '__VERSION__ = "'SEARCH.$$(date +"%Y%m%d%H%M%S")'"' >> src/version.py
	echo '__COMMIT__ = "'$$(git rev-parse HEAD)'"' >> src/version.py
	echo 'import sys' >> build.py
	echo 'print("".join(map(str, sys.version_info[:2])))' >> build.py
	cat build.py

package: assemble
	$(eval PYV = $(shell python build.py))
	pex -vv . -o dist/xsrc-$$(uname)-cp$(PYV)-$$(date +"%Y%m%d%H%M%S").pex --no-pypi -i https://mirrors.aliyun.com/pypi/simple --compile --disable-cache --script xsrc --validate-entry-point --use-system-time  --venv prepend  --venv-copies
	cat src/version.py
	rm -rf build.py src/version.py

docker-compose: clean
	docker-compose up --build --remove-orphans -d

test:
	poetry run pytest --cov-report=term