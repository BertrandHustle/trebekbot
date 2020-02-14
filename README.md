# trebekbot

version 0.7.5 changelog (2-13-20):
Bugs:
  - answers with hyphens and slashes are handled as logical or's

version 0.7.4 changelog (10-24-19):
Bugs:
  - single letter answer bug is fixed
  
Features:
  - added /next route to get more questions from same category

version 0.7.3 changelog (10-3-19):

Bugs:
  - prevent multiple users from answering at once
  - non-debug slash commands now only work in #trivia
  
Features:
  - win tracking is now fixed

version 0.7.2 changelog (9-26-19):

Bugs:
  - fixed issue with daily double wrong answers not returning
  - fixed /nope not cancelling question

version 0.7.1 changelog (8-25-19):

Features:
  - anyone can use /debug
  - added /current_question

Bugs:
  - added retry for 500 timeout errors (to be tested)
  - nope bug is fixed
  - trebekbot no longer responds in channels other than #trivia

version 0.7.0 changelog (8-22-19):

Features:
  - trebekbot now uses slash commands

Bugs:
  - fixed question filtering for 'heard/seen here'
  - fixed 'be less specific' bug

version 0.6.5 changelog (4-18-19):

Features:
  - migrated to Postgres

Bugs:
  - fixed double restarts

version 0.6.4 changelog (3-28-19):

Bugs:
  - filtering issue (maybe) fixed
  - single letter issue (maybe) fixed

version 0.6.3 changelog (3-21-19):

Bugs:
  - fixed slack api token

version 0.6.2 changelog (11-8-18):

Bugs:
  - fixed crashing on close answers

version 0.6.1 changelog (11-8-18):

Bugs:
  - single letter answer bug fixed

Features:
  - added a win counter with ..mywins
  - repackaged project

version 0.6.0 changelog (10-18-18):

Bugs:
  - ACTUALLY fixed the 'be less specific than' bug

version 0.5.9 changelog (9-18-18):

Bugs:
  - fixed 'be less specific than' bug

Features:
  - None

version 0.5.8 changelog (9-13-18):

Bugs:
  - fixed issue with winning score checking
  - persistent score db functioning as intended

Features:
  - Added debug commands
  - Added 'be less specific' response

version 0.5.7 changelog (9-8-18):

Bugs:
  - fixed topten bug

Features:
  - Added persistent storage so scores aren't erased if trebekbot crashes
  - Added ..changelog, ..uptime, and ..pass commands

version 0.5.6 changelog (7-8-18):

Bugs:
  - None

Features:
  - Added html scrubber, questions no longer have html and valid links are displayed separately

version 0.5.5 changelog (6-19-18):

Bugs:
  - fixed (hopefully) json decoding error when asking slack api for user (see issue #18)

version 0.5.4 changelog (6-18-18):

Bugs:
  - fixed websocket crash

version 0.5.3 changelog (4-5-18):

Bugs:
  - fixed crash from querying slack api for channel
  - fixed issue with 'spelling bee' questions
  - parentheses in answers now treated as optional to the answer

Features:
  - trebekbot now announces latest changes on startup

version 0.5.2 changelog (3-22-18):

Bugs:
  - fixed wager crash bug

version 0.5.1 changelog (3-19-18):

Bugs:
- fixed answer control flow so we get true 'close' answer responses

version 0.5.0 changelog:

Bugs:
- fixed numerical answers not counting as correct
- updated slackclient to 1.1.0 (hoping this will fix the restart issue)

Features:
- improved answer checking

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
