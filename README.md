# Airy Rasa Demo

This project serves as a code reference for [this guide](https://docs.airy.co/guides/airy-core-and-rasa). It has been created using the `rasa init` command. 
Be sure to follow their [installation guide](https://rasa.com/docs/rasa/user-guide/installation/) before proceeding.
 

## Run locally

`rasa run`

## Run with Docker

`docker run -it -p 5005:5005  -v $(pwd):/app rasa/rasa:2.1.2-full run`

Instead of run you can also use any other rasa command like `train` and the changes will be reflected in this directory.

## Airy connector

The [Airy connector](./channels/airy.py) is a custom connector implemented by following the [rasa documentation](https://rasa.com/docs/rasa/user-guide/connectors/custom-connectors/). When running rasa in a container this directory needs to be mounted to `/app`.

Once running the rasa server will expose the webhook at `/webhooks/airy/webhook` 

## Testing the connector

For testing the connector you can use [ngrok](https://ngrok.com/). 

1) Replace the `system_token` and `api_host` in the `credentials.yml` file

2) Launch `ngrok http 5005` and keep it running

3) Point your webhook subscription to the url assigned to you by ngrok

4) `docker run -it  -p 5005:5005  -v $(pwd):/app rasa/rasa:2.1.2-full run`

5) Send a test message like "Hello there!" to one of your connected source channels

## Deploying to Heroku

Authenticate:

```
heroku login
```

Build and upload the image:

```
heroku container:push web
```

Release the image:

```
heroku container:release web
```
