# slash-afterwork
This slash command is a utility for creating after work events with your team. It is built with serverless and comes with and automatic setup.

##Description
The command is built with serverless using AWS services to run.

###Services
The services used are:
* DynamoDB - Used for storing information about the after work events
* API Gateway - Used to receive commands from Slack.
* Lambda - Used for the actual processing of the commands from Slack.

##Installation
To install slash-afterwork you simply clone this repository and make sure that you have an AWS profile setup and ready. You also need to have serverless installed.

If not, run `npm -g install serverless`.

You also need to change the `apiKey` in `conf.yml` so that the lambda can integrate with the slack API.

When this is complete you can setup your stack using `serverless deploy`.

Make a note of the `endpoints` that is returned from the deployment command. This value is your endpoint in the Slack Slash command. Go ahead and copy/paste that url to Slack and save the integration.

##Commands
Once everything is deployed you are ready to run commands to slash-afterwork. Not suprisingly, the slash command is:

`/afterwork`

Only running `/afterwork` will give you the available options.

```
/afterwork

No command given, Possible commands are: list, create <day> <time> <place>, join <day>, leave <day>, delete <day>
```
To see the upcoming after work events run: `/afterwork list`
```
/afterwork list

Upcoming after work:
Monday at 17:30 by Unspecified location started by @alexhogberg
Participants:
@alexhogberg
@another_user
@third_user
```
To join an upcoming after work run: `/afterwork join <day>`
```
/afterwork join monday

Great! You've joined the after work on monday!
```

To leave an upcoming after work run: `/afterwork leave <day>`
```
/afterwork leave monday

You are now removed from the after work!
```

Have you created an after work and want to delete it run: `/afterwork delete <day>`
```
/afterwork delete monday

#general: The after work on monday has now been cancelled, sorry!
```

You can only do this if you are the author of the after work event.

##Future improvements
Since this was built quite fast I have yet to implement a couple of other features:
* Notify channel when it is time for after work
* Smarter handling of date parameter, e.g. `/afterwork create friday in two weeks 16:00 TBD`
