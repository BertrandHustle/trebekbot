# trebekbot

version 0.5.2 changelog (3-22-18):
Bugs:
  - fixed wager crash bug

version 0.5.1 changelog (3-19-18):
Bugs:
- fixed answer control flow so we get true 'close' answer responses

version 0.5.0 changelog:

Features:
- improved answer checking
Bugs:
- fixed numerical answers not counting as correct
- updated slackclient to 1.1.0 (hoping this will fix the restart issue)

version 0.3.9 changelog:

Bugs:
- fixed Tonight's Top Scorer's returning nothing

version 0.3.8 changelog:

Features:
- trebekbot now gives a top ten list of scorers before nightly restarts
- increased daily double timer to 90 seconds
Bugs:
- fixed syntax issues in questions and top_ten()
- fixed last night champion reporting wrong score

version 0.3.7 changelog:

Features:
- dates have been added to questions
Bugs:
- '00' bug has been fixed
- -0 wager bug should be fixed

version 0.3.6 changelog:

Features:
- Updated daily double text to indicate that wagers of 0 do NOT count as
valid wagers.
Bugs:
- Hyphens are now properly parsed as whitespace
- 0 value daily doubles are handled properly

Version 0.3.5 changelog:

Bugs:
- Daily double bug fixed where wager gets applied to every question
- Champion tracking fixed

Version 0.3 changelog:

Features:
- Trebekbot now restarts nightly and tracks who the winner is from the previous
day
- Daily doubles are now implimented
- Category/phrase filtering for questions

Bugs:
- Apostrophes and numerical answers are now handled correctly
- Questions with "heard here" or "seen here" no longer appear

Practice project, a Python slack bot that hosts a game of Jeopardy! in your slack channel.

Installation instructions:

1. Clone repo:
$ git clone https://github.com/BertrandHustle/trebekbot.git

2. Create a new bot-user for your slack channel:
https://my.slack.com/services/new/bot
Take note of the API token you get after configuring your new bot.

3. Set TREBEKBOT_API_TOKEN variable:

Linux:

3a) add the following to /etc/environment:
TREBEKBOT_API_TOKEN=<API token from step 2>

3b) $ source /etc/environment

Windows:

3a). right-click the start button or hit win+break

3b). select “Advanced system settings” → “Environment Variables”.

// Thank you to https://www.fullstackpython.com/blog/build-first-slack-bot-python.html for this script

4. Get your bot's ID:
$ python3 print_bot_id.py

5. Set TREBEKBOT_ID variable:
Use the same procedure as step 3, but set TREBEKBOT_ID=<output of question 4>

6. Set channel to your desired slack channel:
In main.py, change the following line:
channel = '#yourchannel'

7. Run trebekbot!
$ python3 main.py

NOTE: you will need a dictionary file named words.txt in /support_files if
you're not on a UNIX system.  I used one from the following repo:

https://github.com/dwyl/english-words
