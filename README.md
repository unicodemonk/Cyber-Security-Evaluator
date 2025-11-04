## Quickstart
1. Clone (or fork) the repo:
```
git clone git@github.com:Mauttaram/SecurityEvaluator.git
cd SecurityEvaluator
```
2. Install dependencies
```
uv sync
```
3. Set environment variables
```
cp sample.env .env
```
Add your Google API key to the .env file

```
cd SecurityEvaluator/scenarios/security/purple_agent
docker-compose up
docker-compose run

## when shutting down do the below
docker-compose down
```

4. Run the [debate example](#example)
```
uv run agentbeats-run scenarios/security/scenario.toml
```


This command will:
- Start the agent servers using the commands specified in scenario.toml
- Construct an `assessment_request` message containing the participant's role-endpoint mapping and the assessment config
- Send the `assessment_request` to the green agent and print streamed responses

**Note:** Use `--show-logs` to see agent outputs during the assessment, and `--serve-only` to start agents without running the assessment.

To run this example manually, start the agent servers in separate terminals, and then in another terminal run the A2A client on the scenario.toml file to initiate the assessment.

After running, you should see an output similar to this.
