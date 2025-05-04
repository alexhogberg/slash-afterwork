# slash-event
[![CodeQL](https://github.com/alexhogberg/slash-event/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/alexhogberg/slash-event/actions/workflows/github-code-scanning/codeql)

This slash command is a utility for creating events with your team. It is built with Slack Bolt, MongoDB, and Google Places API, and comes with an automatic setup.

## Description
The command is built using Slack Bolt for Python and deployed with Fly.io for a simple and scalable setup.

## Prerequisites
You need the following to deploy the solution:
* A Fly.io account
* A Slack workspace where you have admin privileges
* A Google Places API key
* A MongoDB Atlas database (or any MongoDB instance)

### Services
The services used are:
* **MongoDB** - Used for storing information about the events
* **Google Places API** - Used for suggesting event locations
* **Slack Bolt** - Used for handling Slack commands and events

## Installation
Run `./setup.sh` to set up a local virtual environment with all dependencies. After that, run `./local.sh` to start the app locally.

### Configuration
The configuration is stored in the `.env` file. The file should look as follows:
```env
SLACK_AUTH_KEY=
SLACK_CHANNEL_NAME=

SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=

MONGO_DB_CONNECTION_STRING=

GOOGLE_PLACES_API_KEY=
```

- `SLACK_AUTH_KEY`: The Slack bot key retrieved from the Slack Bot API.
- `SLACK_CHANNEL_NAME`: The Slack channel where announcements should be sent. The bot must be invited to this channel.
- `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`: Tokens used to connect to the Slack APIs. These are generated when you create a Slack app.
- `MONGO_DB_CONNECTION_STRING`: The connection string for your MongoDB instance.
- `GOOGLE_PLACES_API_KEY`: Retrieved from the Google Developers Console.

### Deployment
The app is deployed using Fly.io. The deployment process is automated with a GitHub Actions workflow. On every push to the `master` branch:
1. Tests are run using `pytest`.
2. If all tests pass, the app is deployed to Fly.io.

To deploy manually, run:
```bash
flyctl deploy
```

### Notifications
The app includes a daily notification feature that announces events scheduled for the current day. This can be triggered manually or scheduled using a cron job.

## Commands
Once everything is deployed, you can use the `/event` slash command in Slack. The bot provides both private and public messages.

### Available Commands
1. **List Events**:
   ```
   /event list
   ```
   Displays a list of upcoming events.

2. **Create an Event**:
   ```
   /event create
   ```
   Opens a dialog to create a new event. You can specify the date, time, and location.

3. **Suggest a Place**:
   ```
   /event suggest <area>
   ```
   Provides top 5 recommendations from Google Places for the specified area.

4. **Join an Event**:
   ```
   /event join <event_id>
   ```
   Adds you to the participant list of the specified event.

5. **Leave an Event**:
   ```
   /event leave <event_id>
   ```
   Removes you from the participant list of the specified event.

6. **Delete an Event**:
   ```
   /event delete <event_id>
   ```
   Deletes an event. Only the creator of the event can delete it.

### Example Usage
- **List Events**:
   ```
   /event list

   Upcoming events:
   - Monday at 17:30 at The Pub
     Participants: @alexhogberg, @another_user
   ```

- **Create an Event**:
   ```
   /event create
   ```
   Opens a dialog where you can specify the event details.

- **Join an Event**:
   ```
   /event join monday
   ```
   Adds you to the event happening on Monday.

- **Delete an Event**:
   ```
   /event delete monday
   ```
   Deletes the event scheduled for Monday (if you are the creator).

## Future Improvements
- [ ] Add support for recurring events.
- [ ] Improve error handling for edge cases.
- [ ] Add more granular permissions for event management.
- [ ] Enhance the UI for the Slack App Home tab.

## Contributing
Feel free to fork this repository and submit pull requests for new features or bug fixes.

## License
This project is licensed under the MIT License.
