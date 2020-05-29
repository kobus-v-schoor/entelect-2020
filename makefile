files = bot.json requirements.txt sloth/weights.json sloth/__init__.py \
		sloth/main.py sloth/bot.py sloth/enums.py sloth/maps.py \
		sloth/state.py sloth/search.py sloth/ensemble.py sloth/log.py

zip:
	zip bot.zip $(files)

clean:
	rm -fvr sloth/bot.log tests/bot.log sloth/rounds
	rm -fvr bot.zip tools.zip
	rm -fvr sloth/__pycache__ profile.prof

run:
	cd sloth; python3 main.py

profile:
	cd sloth; ls -v rounds | python3 -m cProfile -o ../profile.prof main.py

lint:
	python3 -m flake8 sloth --count --statistics --show-source

test:
	cd tests; pytest-3 -v

tools_zip:
	zip -r tools.zip tools/*.py tools/tools/*.py

sec: clean zip tools_zip
	scp bot.zip tools.zip sec:
	ssh sec "rm -r tools; unzip tools.zip"
