<div align="center">
    <h1>Telegram bot <a href="https://t.me/watch_films_and_serials_bot">MoviePlanet</a></h1>
    <img width="80" src="https://raw.githubusercontent.com/kanewi11/MoviePlanet/main/redirect_site/static/img/logo.png">
</div>

## The bot knows how:
1. Search for movies and TV series.
2. Make posts automatically, the input link to the movie or series.
3. Send posts by time to the channel (for admins).
4. Change the time of sending (for admins).
5. Delete unsent posts (for admins).
6. Send promotional posts to all bot users and to the channel (for admins).

## Telegram bot for watching movies.

It works through the api of a third-party site. 

There is also a small problem, it is related to the fact that the links to the shows do not open. They do not open due to the fact that when requested the server looks for the title "Referer" and if it is absent, the player will show a download error. 

Solved the problem banal, bought a domain and hosting, and simply redirected from this hosting, to that link.

## If you want to run a bot

1. If you want to run a bot, add your token to the environment with the ```API_TOKEN``` key.

2. In the configuration file, change the link to your group and to the site.

3. The home page of the site must take the parameter "q" example ```https://yoursite.com/?q=https://film.com/Avengers: Endgame``` in which the link to the movie or TV series will be passed, then the site must redirect the user to the link in the request using JS. This repository already has a redirection site written in Flask, you can check it out.

4. After that you should run ```start.py``` in the ```/MoviePlanet``` directory
