import json


LOG_CHANNEL_PREFIX = "training_log_"
STATUS_CHANNEL_PREFIX = "training_status_"


def redis_pubsub_listener(socketio, app):
    with app.app_context():
        pubsub = app.redis_client.pubsub()
        pubsub.psubscribe(f'{LOG_CHANNEL_PREFIX}*')
        pubsub.psubscribe(f'{STATUS_CHANNEL_PREFIX}*')

        for message in pubsub.listen():
            if message['type'] == 'pmessage':
                channel = message['channel']
                data = message['data']

                channel_str = channel
                data_str = data

                task_id = channel_str.split('_')[-1]

                if channel_str.startswith(LOG_CHANNEL_PREFIX):
                    log_content = data
                    socketio.emit('training_log_update',
                                  {'task_id': task_id, 'log': log_content})

                elif channel_str.startswith(STATUS_CHANNEL_PREFIX):
                    try:
                        parsed_data = json.loads(data_str)
                    except json.JSONDecodeError as e:
                        app.logger.error(f"JSON decode error for task {task_id}: {e}")
                        parsed_data = None
                    if parsed_data and 'status' in parsed_data:
                        parsed_data['task_id'] = task_id
                        socketio.emit('task_status_update', parsed_data)
                        app.logger.info(f"Emitted status update for task {task_id}: {parsed_data.get('status', 'N/A')}")
                    else:
                        app.logger.warning(f"Received malformed status message on channel {channel_str}: {data_str}")

            elif message['type'] == 'subscribe' or message['type'] == 'psubscribe':
                app.logger.info(f"Redis Pub/Sub listener subscribed to: {message['channel']}")