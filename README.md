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
4. Miscellaneous 
    - !aundre - a command to tease my friend
    - !stock - Look up a stock with its ticker name. Displays final adjusted call from a 1 year period. !stock 'ticker'
    - deletes any mention of the word 'boruto'.




