import json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop
import tornado.web
import tornado.auth

# your client ID and secret
_SINGLY_CLIENT_SECRET = ""
_SINGLY_CLIENT_ID = ""


class SinglyAuthStartHandler(tornado.web.RequestHandler, tornado.auth.OAuth2Mixin):
    """
    A handler to start the oauth2 flow with Singly.
    """
    _OAUTH_AUTHORIZE_URL = "https://api.singly.com/oauth/authenticate"

    def get(self):
        self.authorize_redirect(
            redirect_uri="http://localhost:8888/auth/callback",
            client_id=_SINGLY_CLIENT_ID,
            client_secret=_SINGLY_CLIENT_SECRET,
            extra_params={
                "service": "facebook"
            }
        )


class SinglyAuthCallbackHandler(tornado.web.RequestHandler):
    """
    A callback handler for the oauth2 flow with Singly.
    """

    @tornado.web.asynchronous
    def get(self):
        code = self.get_argument("code")
        url = "https://api.singly.com/oauth/access_token"
        body = {
            "client_id": _SINGLY_CLIENT_ID,
            "client_secret": _SINGLY_CLIENT_SECRET,
            "code": code
        }
        headers = {
            "Content-Type": "application/json"
        }
        client = AsyncHTTPClient()
        req = HTTPRequest(
            url,
            method="POST",
            headers=headers,
            body=json.dumps(body)
        )

        def callback(response):
            body = json.loads(response.body)
            access_token = body["access_token"]

            self.application.singly = {
                "access_token": access_token,
            }

            self.redirect("/profiles")

        client.fetch(req, callback)


class SinglyProfilesHandler(tornado.web.RequestHandler):
    """
    A handler that calls Singly's profiles API (once the oauth2 flow has completed).
    """

    @tornado.web.asynchronous
    def get(self):
        url = "https://api.singly.com/profiles"
        access_token = self.application.singly["access_token"]
        url = "{}?access_token={}".format(url, access_token)

        def callback(response):
            self.write(response.body)
            self.finish()

        AsyncHTTPClient().fetch(url, callback)


application = tornado.web.Application([
    (r"/auth/start", SinglyAuthStartHandler),
    (r"/auth/callback", SinglyAuthCallbackHandler),
    (r"/profiles", SinglyProfilesHandler)
], debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()