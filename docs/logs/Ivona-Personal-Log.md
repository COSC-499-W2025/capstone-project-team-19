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

This week I worked on PR[COSC-499-W2025/capstone-project-team-19#198](https://github.com/COSC-499-W2025/capstone-project-team-19/issues/198). I spent a lot of time figuring out which metrics to use so that we can accurately assess collaborative text projects. And how to represent this in the database. 
-I made 2 tables in the database with helper methods for storing the metrics. I had Timmi help me out with how to create these tables. 
- I added the logic for processing the google drive connected files within a project
- I made API calls for extracting data from the Google Drive Doc files
- I made unit tests for all of this logic
- I integrated it into the analysis work flow
- I ran into 2 bugs that I coulnd't end up fixing but I made it an issue for next week.

Next Week:
Continue extracting/improving Google drive collaboration data. Fix the 2 bugs. Refactor/clean code.

## (Week 12) Monday Nov 17th - Sunday November 23th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Nov.17-23.PNG)

This week I attended group meetings, reviewed PRs, made 2 PRs and helped Timmi with starting the organization for planning what is left for milestone 1.

This week I worked on PR[COSC-499-W2025/capstone-project-team-19#235](https://github.com/COSC-499-W2025/capstone-project-team-19/issues/235):

This was a bug fix to optimize performance when connecting to Google Drive.

PR#245:
This was the start of the implementation of utilizing GoogleDrive for computing collaborative anlysis skills from text projects. 
-I added the modules functions for calculating all the initial skill computation flow.
-I added the profile module to store the computed skills.
-I added all the modules for calculating the anlaysis.
-Full unit testing.

Next Week:
I plan to finnish the contributation skills from text projects by getting the metrics from the comments API and stroing them in the database.


## (Week 13) Monday Nov 24th - Sunday November 30th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Nov.24-30.PNG)

This Week:
I worked on PR 275, attended team meetings, reviewed PRs and did project planning with Timmi about how the flow of adding new zip files should work in our system.

PR 275:
This PR added the functionality to list all of user's projects in chronological order. This is a requirement for milestone 1, hence the implementation. 

In the PR I wrote a query to the DB to retrieve all the project names along with the completion dates which we calculated previous during anlayis. I added a function that uses this to print out all the projects for a user and the completion dates in chronological order. And added an option on the menu for the user to select this. And I added full unit testing.

Next Week Plan:
I have started working on cleaning up the terminal and only outputting necessary information to be ready for the presentation however I don't have a PR up for this yet hence it will be counted for next week. 

Working with the team on the presentation slide and demo video.

Finishing the contributation skills from text projects by getting the metrics from the comments API and stroing them in the database.


## (Week 14) Monday Dec 1st - Sunday November 7th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Dec.1-7.PNG)
This Week:
I worked on making the presentation and preparing for it, creating PR#321, PR#299, reviewing PRs,and atttending team meetings.

The PRs:
I worked on PR 299:
This PR was to finish the implementation of the text collab contributation skills, I retrieved the user's comments and teams comments from the API and their username information and integrated it into the flow of previosuly made functions. I also asjusted some logic for how the skills are inferred to be more accurate. Disabled the revision that we inteded Google Drive to earlier and overall integrated into the flow of our project.

I worked on PR 321:
This PR conserned with writting the instructions to the TAs in the read me on how to set up a google drive api and credentials file.

Next Week:
Next week is winter break so I don't have any plans for the project yet.



## (Week 14) Monday Dec 1st - Sunday November 7th 
![Screenshot of this week's peer eval](./screenshots/Ivona-Jan.5-11.PNG)
This Week:
I worked on PR #350:
This PR was working on milestone requiremnt 21. It gave user the option to select the projects they want to show in their resume. I adjusted the code to allow users to pick and not let them pick more than 5 projects and then it be listed in the order of the score. I also wrote tests for this as well.

Next Week:
I will be taking on a new task probably to start implementing the APIs as we havent started that yet and don't have a lot of user customizarion tasks left to do.