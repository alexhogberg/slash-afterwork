# slash-afterwork
![CircleCI](https://circleci.com/gh/alexhogberg/slash-afterwork.svg?style=shield&circle-token=:circle-token)

This slash command is a utility for creating after work events with your team. It is built with serverless and comes with an automatic setup.

## Description
The command is built with serverless using AWS services to run which enables super simple setup.

## Prerequisites
You need the following to deploy the solution:
* An AWS Account
* A slack team that you have the ability to manage
* A Google Places API key

### Services
The services used are:
* DynamoDB - Used for storing information about the after work events
* API Gateway - Used to receive commands from Slack.
* Lambda - Used for the actual processing of the commands from Slack.
* Google Places API - Used to suggesting places to go for afterwork

## Installation
To install serverless dependency: `npm install`

Serverless will handle packaging of requirements on deploy so don't worry about that.

### Configuration
The configuration is stored in the `conf.yml`. The file looks as follows:
```yml
apiKey: <SLACK_SLASH_COMMAND_API_KEY>
authKey: <SLACK_BOT_API_KEY>
botName: <BOT_NAME>
channelName: <CHANNEL_NAME>
tableName: <DYNAMODB_TABLE_NAME>
googleMapsApiKey: <GOOGLE_API_KEY>
```

The `apiKey` is so that the lambda can integrate with the slack API. You get this key when you setup your slash command in the Slack API. `authKey` is the slack bot key that is retrieved from Slack Bot API. `botName` is used to send the channel messages with a specific name.
`channelName` is the channel in your slack setup that annoucements should be sent to. __NOTE:__ the bot must be invited to the channel in order to send the message.

When this is complete you can setup your stack using `serverless deploy`.

Make a note of the `endpoints` that is returned from the deployment command. This value is your endpoint in the Slack Slash command. Go ahead and copy/paste that url to Slack and save the integration.

### Notifications
The serverless sets up a cron for scheduling daily invocations of the lambda in order to look for after work events today.
It is configured in `serverless.yml`

```
rate: cron(0 12 ? * MON-FRI *)
```
You may alter this command if you want the announcement to be made at a different time.

## Commands
Once everything is deployed you are ready to run commands to slash-afterwork. Not suprisingly, the slash command is:

`/afterwork`

The bot gives both private messages and public messages. The only two possibilities of sending a public message is either when you create an after work or deletes one.

Only running `/afterwork` will give you the available options.

```
/afterwork

No command given, Possible commands are:
list
create <day> <time> <place>
join <day>
leave <day>
delete <day>
suggest <area>
```

Suggest will give you top 5 recommendations from Google around the area you specified, e.g. Gamla Stan, Old Trafford.

Days are either monday-friday or mon-fri or a specified date in Y-m-d.

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

## Future improvements
Since this was built quite fast I have yet to implement a couple of other features:
* ~~Notify channel when it is time for after work~~ Added in [ebe4dd4](https://github.com/alexhogberg/slash-afterwork/commit/ebe4dd4164ef320117a9a905102d1a3d67861256)
* Smarter handling of date parameter, e.g. `/afterwork create friday in two weeks 16:00 TBD`
* ~~Install slacker for better integration with the Slack API~~ Added in [ebe4dd4](https://github.com/alexhogberg/slash-afterwork/commit/ebe4dd4164ef320117a9a905102d1a3d67861256)
* Add support to create afterwork with Google Places integration (only possible through suggest)
* Add inline responses and multiple options for time and date when using suggest
