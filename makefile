files = bot.json requirements.txt src/__init__.py src/main.py src/bot.py \
		src/enums.py src/map.py src/state.py

zip:
	zip bot.zip $(files)

clean:
	rm -fvr bot.zip src/rounds src/bot.log src/__pycache__

run:
	cd src; python3 main.py
