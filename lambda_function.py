import boto3
option_table = boto3.resource('dynamodb').Table('options')
vote_table = boto3.resource('dynamodb').Table('votes')

def build_response(message, message_type="Close", session_attributes=None):
    resp = {
        "dialogAction": {
            "type": message_type,
            "message": {
                "contentType": "PlainText",
                "content": message
            }
        }
    }
    if message_type is 'Close':
         resp["dialogAction"]["fulfillmentState"] = "Fulfilled"
    if session_attributes:
        resp['sessionAttributes'] = session_attributes
    return resp

def lambda_handler(event, context):
    if 'GetName' == event['currentIntent']['name']:
        name = event['currentIntent']['slots']['name']
        session_attributes = {'name': event['currentIntent']['slots']['name']}
        return build_response("Thanks {} you can ask me to describe the episodes".format(name), message_type="ElicitIntent", session_attributes=session_attributes)
    if 'DescribeEpisodesTwo' == event['currentIntent']['name']:
        options = option_table.get_item(Key={'poll': 'episodes'})['Item']['options']
        msg = ""
        for i, option in enumerate(options):
            msg += "{} {}\n".format(i, option)
        return build_response(msg, message_type="ElicitIntent", session_attributes=event['sessionAttributes'])
    elif 'VoteEpisodeTwo' == event['currentIntent']['name']:
        item = {
            'user': event['userId'],
            'vote': event['currentIntent']['slots']['option'],
            'poll': 'episodes'
        }
        name = event['userId']
        if event['sessionAttributes'].get('name'):
            item['name'] = event['sessionAttributes']['name']
            name = item['name']
        vote_table.put_item(Item=item)
        return build_response("{} voted for {}".format(name, event['currentIntent']['slots']['option']), session_attributes=event['sessionAttributes'])
