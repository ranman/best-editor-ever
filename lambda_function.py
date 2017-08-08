import hashlib
import os
import boto3
users_table = boto3.resource('dynamodb').Table('editor-votes-users')
votes_table = boto3.resource('dynamodb').Table('editor-votes')

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
    if 'ConnectToAgent' == event['currentIntent']['name']:
        return build_response("Ok, connecting you to an agent.")
    elif 'VoteEditor' == event['currentIntent']['name']:
        editor = event['currentIntent']['slots']['editor'].lower()
        # sessionAttributes can be "None" so you can't just chain calls
        if event.get('sessionAttributes'):
            key = event.get('sessionAttributes').get('phone', event['userId'])
        else:
            key = event['userId']
        m = hashlib.sha256()
        m.update(key.encode("utf-8"))
        m.update(os.getenv('SALT').encode("utf-8"))
        resp = users_table.update_item(
            Key={"phone": m.hexdigest()},
            UpdateExpression="SET vote = :vote",
            ExpressionAttributeValues={":vote": editor},
            ReturnValues="UPDATED_OLD"
        )
        old_editor = resp.get('Attributes', {}).get('vote')
        if old_editor == editor:
            return build_response("You already voted for that!")
        if old_editor:
            votes_table.update_item(
                Key={'name': old_editor},
                UpdateExpression="SET votes = votes - :decr",
                ExpressionAttributeValues={":decr": 1}
            )
        resp = votes_table.update_item(
            Key={'name': editor},
            UpdateExpression="ADD votes :incr",
            ExpressionAttributeValues={":incr": 1},
            ReturnValues="ALL_NEW"
        )
        if old_editor:
            msg = "Changing your vote from {} to {}, {} now has {} votes! Bye!".format(
                old_editor, editor, editor, resp['Attributes']['votes']
            )
        else:
            msg = "Awesome, now {} has {} votes! Bye!".format(
                resp['Attributes']['name'],
                resp['Attributes']['votes'])
        return build_response(msg)
    else:
        return build_response("That intent is not supported yet.")
