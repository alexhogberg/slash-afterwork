# slash-event
![CircleCI](https://circleci.com/gh/alexhogberg/slash-event.svg?style=shield&circle-token=:circle-token)

This slash command is a utility for creating events with your team. It is built with serverless and comes with an automatic setup.

## Description
The command is built with serverless using AWS services to run which enables super simple setup.

## Prerequisites
You need the following to deploy the solution:
* An AWS Account
* A slack team that you have the ability to manage
* A Google Places API key

### Services
The services used are:
* MongoDB - Used for storing information about the events

## Installation
Run `./setup.sh` and it will setup a local virtualenv with all dependencies. After that run `./local.sh` in order to run bolt locally.

### Configuration
The configuration is stored in the `.env`. The file looks as follows:
```yml
SLACK_AUTH_KEY=
SLACK_CHANNEL_NAME=

SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=

MONGO_DB_CONNECTION_STRING=

GOOGLE_PLACES_API_KEY=
```

`SLACK_AUTH_KEY` is the slack bot key that is retrieved from Slack Bot API.
`SLACK_CHANNEL_NAME` is the channel in your slack setup that annoucements should be sent to. __NOTE:__ the bot will be invited to the channel in order to send the message.
`GOOGLE_PLACES_API_KEY` is retrieved from the google developers console. `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` is used to connect to the slack APIs. So you obviously need to create a slack app. The Manifest is in the root.
``
``
Make a note of the `endpoints` that is returned from the deployment command. This value is your endpoint in the Slack Slash command and place suggestions. Go ahead and copy/paste the /event and /placessuggester url to Features -> Interactive components, then save the changes

### Notifications
The serverless sets up a cron for scheduling daily invocations of the lambda in order to look for after work events today.

```
rate: cron(0 12 ? * MON-FRI *)
```
You may alter this command if you want the announcement to be made at a different time.


## Commands
Once everything is deployed you are ready to run commands to slash-event. Not suprisingly, the slash command is:

`/event`

The bot gives both private messages and public messages. The only two possibilities of sending a public message is either when you create an after work or deletes one.

Only running `/event` will give you the available options.

```
/event

No command given, Possible commands are:
list
create
suggest <area>
```

Suggest will give you top 5 recommendations from Google around the area you specified, e.g. Gamla Stan, Old Trafford.

Running `/event create` will open a dialog with inline suggestions for real bars
around the value you specify. Add your time and date after that and you are good to go

The date can be specified however you like, we'll try to parse it into a proper date for storage.

To see the upcoming after work events run: `/event list`
```
/event list

Upcoming after work:
Monday at 17:30 by Unspecified location started by @alexhogberg
Participants:
@alexhogberg
@another_user
@third_user
```
To join an upcoming after work run: `/event join <day>` or click the button when someone created an event
```
/event join monday

Great! You've joined the after work on monday!
```

To leave an upcoming after work run: `/event leave <day>` or `/event list` and click the leave button
```
/event leave monday

You are now removed from the after work!
```

Have you created an after work and want to delete it run: `/event delete <day>` or type `/event list` and click the delete button
```
/event delete monday

#general: The after work on monday has now been cancelled, sorry!
```

You can only do this if you are the author of the after work event.

## Future improvements
Since this was built quite fast I have yet to implement a couple of other features:
* ~~Notify channel when it is time for after work~~ Added in [ebe4dd4](https://github.com/alexhogberg/slash-event/commit/ebe4dd4164ef320117a9a905102d1a3d67861256)
* ~~Smarter handling of date parameter, e.g.~~ `/event create friday in two weeks 16:00 TBD` Added in [63811db](https://github.com/alexhogberg/slash-event/commit/63811bdcecbb82268f9574589e505cd007ad74bb)
* ~~Install slacker for better integration with the Slack API~~ Added in [ebe4dd4](https://github.com/alexhogberg/slash-event/commit/ebe4dd4164ef320117a9a905102d1a3d67861256)
* ~~Add support to create event with Google Places integration (only possible through suggest)~~ Added in [63811db](https://github.com/alexhogberg/slash-event/commit/63811bdcecbb82268f9574589e505cd007ad74bb)
* ~~Add inline responses and multiple options for time and date when using suggest~~ Added in [63811db](https://github.com/alexhogberg/slash-event/commit/63811bdcecbb82268f9574589e505cd007ad74bb)
* ~~Better multi tenancy options and smoother setup with Slack API~~ Added in [a659f9f](https://github.com/alexhogberg/slash-event/commit/a659f9f1acfcaf043a7dc47339da8ec1e384a15e)
* Able to join an event via the slack message
