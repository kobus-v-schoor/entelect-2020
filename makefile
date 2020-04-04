files = bot.json src/__init__.py src/main.py src/bot.py src/enums.py \
		src/map.py src/state.py
zip:
	zip bot.zip $(files)

clean:
	rm -fvr rounds bot.log bot.zip

run:
	cd src; python3 main.py
