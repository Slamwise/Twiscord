from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from tweets import create_api
import tweepy as tp

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""

    # Start our TwiML response
    resp = MessagingResponse()
    args = request.form['Body'].split(' ')

    #Check if response is actionable
    if not request.form['Body']:
        return
    if args[0] not in ['START', 'STOP']:
        return
    if len(args) < 2:
        return
    else:
        file = open("changes.txt", "a")

        to_remove = []
        to_add = []

        number = request.values.get('From')
        print(number)

        if args[1] != "ALL":
            api: tp.API = create_api()
            for handle in args[1:]:
                try:
                    _ = api.get_user(handle)
                    if args[0] == 'STOP':
                        to_remove.append(handle)
                    elif args[0] == 'START':
                        to_add.append(handle)
                except tp.NotFound as e:
                    continue
                except Exception as e:
                    continue
            if args[0] == 'STOP':
                resp.message(f'Unsubscribed from: {" ".join(to_remove)}')
                file.write(f'\nhandle')
            else:
                resp.message(f'Now subscribed to: {" ".join(to_add)}')
        
        elif args[1] == "ALL":
            

if __name__ == "__main__":
    app.run(debug=True)