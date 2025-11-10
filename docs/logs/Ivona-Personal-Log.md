# Personal Log - Ivona

## (Week 3) Monday 15th - Sunday 21st September

![Screenshot of this week's peer eval](./screenshots/Ivona-Sept15-21.PNG)

Week Recap:
Monday: Met teammates and discussed the project and worked on functional and non-functional requirments.
Wednesday: Talked to other teams as a sub team of 3 about their functional/ non-fucntional requirments. Met back up with our full team and discussed what we found out.

## (Week 4) Monday 22th - Sunday 28st September
![Screenshot of this week's peer eval](./screenshots/Ivona-Sept.22-28.PNG)

Week Recap:
I was absent from class this week due to health reasons. I provided my professor with a doctor’s note and informed my team of my situation. Because of this, I wasn’t able to contribute earlier in the week, but by Saturday night/Sunday I caught up on all team discussions and reviewed the work completed. I contributed by helping with the UML Use Case Diagram.

## (Week 5) SeptemberMonday 29th - Sunday October 5th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Sept29-Oct5.PNG)

Helped polish up the DFD. Then on Wednesday my team and I talked to other teams and compared DFDs in class. We took notes on their DFDs on how they differed from ours. We had dissucions with the teams to better understand their diagrams.

## (Week 6) Monday 6th - Sunday 12st October
![Screenshot of this week's peer eval](./screenshots/Ivona-Oct.6-12.PNG)

This week I worked on the external consent feature for milestone #1. Pr #40.
I implemented the tests, file and updated main file to ask user's permission to use external services on their files. Reviewed teammate's PRs.

## (Week 7) Monday 13th - Sunday 19st October
![Screenshot of this week's peer eval](./screenshots/Ivona-Oct.13-19.PNG)

This week I worked on the feature for detecting languages and frameworks used in coding projects. I implemented the languages and framework detection and then refactored the languages to be more efficient(PR 90).
My plan now is to do the same with the framework but there is an aditional step that needs to be done (adding config files to the database) which I discussed with the team. So I will continue to work on that next week. As well as with extracting key contributation metrics in a project (without LLM).

## (Week 8) Monday 20th - Sunday 26st October
![Screenshot of this week's peer eval](./screenshots/Ivona-Oct.20-26.PNG)

This week I completed two PRs (109 and 122). 
I reviewed a few PRs, attended team meetings and helped team members when needed.

The first PR was a refactoring of the implementation of language detection, I rewrote the code to utilize the attribute project_name that was added to the files table this week instead of manually filtering out projects.

The second PR, I worked on the framework detection for coding projects. I made a new table in the database, added logic for extracting config./ dep. files during the parsing process and storing them in the new table. And then using these files to find frameworks for a given project. 

Next week I will continue working on the language/framework detection feature. I plan to add support for frameworks that aren't usually declared in config./dep. files. Store the languages/frameworks found in a database. And maybe expand the language detection supported files (depending on what the team decides on Monday.) And If time premits I will start working on extracting key contributation metrics in a project.

## (Week 9) Monday October 27th - Sunday November 2nd 
![Screenshot of this week's peer eval](./screenshots/Ivona-Oct.27-Nov.2.PNG)

This week I completed the PR 168.
I reviewed teammate's PRs and attended team meeting.

My PR this week was connecting Google Drive to our project. I did some learning on how to set up a Google Drive API and connect it with Oauth. I then focused on integrating the files selected from the user's Google Drive account to match the files they want to provide us with. This was an approached my team discussed doing so that we can extract better contributation metric for non-coding files. 

I originally didn't plan to work on this week but at the Wednesday meeting we discussed this is useful to get done since we walk to be able to get contributation analysis feature done.

Next Week: I plan to either go back to explanding the framework detector as I originally planned to last week or/and to get contributation metrics from the Google Drive files.


## (Week 10) Monday Nov 3rd - Sunday November 9th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Nov.3-9.PNG)

