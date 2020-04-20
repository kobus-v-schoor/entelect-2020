files = bot.json requirements.txt src/weights.json src/__init__.py src/main.py \
		src/bot.py src/enums.py src/maps.py src/state.py src/search.py \
		src/ensemble.py

zip:
	zip bot.zip $(files)

clean:
	rm -fvr bot.zip src/rounds src/__pycache__

run:
	cd src; python3 main.py
