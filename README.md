# Discordbot
## Personal Discord bot written in Python. 

Hosted on an AWS linux server. Wrote the bot to practice python.

## Features and Commands

1. Music Integration - can play links from youtube
    - !play - can play or queue youtube links with !play '*youtube link*' and can search songs with !play '*search terms*'. Plays and queues the top search. Can also play youtube playlists.
    - !pause - pause the music
    - !resume - unpause the music 
    - !queue - view queue
    - !clear - clears the queue 
    - !stop - clears the queue and stops the music
    - !leave - leave the voice channel
    - !move - move the specify index up to the front of the queue
2. Danbooru - fetch a random image from danbooru with a search tag 
    - !danbooru - search a random image from danbooru with !danbooru '*tag*'
3. Manga Update Tracker - add mangadex links to a sqlite database to track updates using an api wrapper for the mangadex api. If there is an update for a manga, send an embeded message to the main channel of my server.
    - !addmanga - add a manga title with !addmanga http://mangadex.org/title link
    - !mangalist - sends an embedded list of manga being tracked 
4. Point System - users can accrue points through implemented games such as blackjack which is manage by a JSON file
    - !daily - gives 200 credits to the user
    - !credit - shows how many credits you have
    - !blackjack '*# of credits*' - input a number to bet that many points.
    - !give '*@user mention*' '*# of credits*' - give another user credits.
    - sending messages will yield 5 credits with a 2 minunte cooldown for messages that can yield credits.
5. Miscellaneous 
    - !stock - Look up a stock with its ticker name. Displays final adjusted call from a 1 year period. !stock 'ticker'
    - !blackjack - Simulate a game of blackjack. Uses reactions to control and discord embeds as the display.




