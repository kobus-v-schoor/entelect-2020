files = bot.json requirements.txt src/weights.json src/__init__.py src/main.py \
		src/bot.py src/enums.py src/maps.py src/state.py src/search.py \
		src/ensemble.py src/log.py

zip:
	zip bot.zip $(files)

clean:
	rm -fvr bot.zip src/bot.log src/rounds src/__pycache__ profile.prof

run:
	cd src; python3 main.py

profile:
	cd src; ls -v rounds | python3 -m cProfile -o ../profile.prof main.py
