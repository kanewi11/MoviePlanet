# Telegram bot [MoviePlanet](https://t.me/watch_films_and_serials_bot)

![LOGO](https://kingzmsk.ru/static/img/logo.png "MoviePlanet")

## Telegram bot for watching movies.

It works through the api of a third-party site. 

There is also a small problem, it is related to the fact that the links to the shows do not open. They do not open due to the fact that when requested the server looks for the title "Referer" and if it is absent, the player will show a download error. 

Solved the problem banal, bought a domain and hosting, and simply redirected from this hosting, to that link.

## If you want to run a bot

1. If you want to run a bot, add your token to the environment with the ```API_TOKEN``` key.

2. In the configuration file, change the link to your group and to the site.

3. The home page of the site must take the parameter ```"q" example (https://site.com/?q=https://...)``` in which the link to the movie or TV series will be passed, then the site must redirect the user to the link in the request using JS. This repository already has a redirection site written in Flask, you can check it out.

4. After that you should run ```start.py``` in the ```/MoviePlanet``` directory
