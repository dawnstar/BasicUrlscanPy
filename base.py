import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json

from .exceptions import UrlscanInvalidPayload

logger = logging.getLogger(__name__)

def urlscan_session(retries=5, backoff=1):

    """
    This function creates a new requests session object that is capable of retrying requests for urlscan.io

    urslcan.io will return a 429 status for "too many requests" so we include that along side other errors

    Adjust retries and backoff as needed for your setup. Backoff will exponentially increase the time between retries and is in seconds
    """

    STATUSES=[429, 500, 502, 503, 504]

    # Define our strategy
    strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=STATUSES,
    )

    # Create an adapter using that strategy
    adapter = HTTPAdapter(max_retries=strategy)
 
    # Initialise a standard requests session object
    session = requests.Session()
    # Only ever connect to urlscan.io over HTTPS but now using the adapter with our retry strategy
    session.mount('https://', adapter)

    return session


class BaseUrlscan:

    """
    Base class for handling interactions with the urlscan.io API.

    This is a very, very simple base class that does nearly no handling logic, just defines all the base
    API interactions with urlscan.io and the calls return either a requests Response object or None if the request failed.

    Subclass this class to add more complex interactions with the API and response handling.

    You don't need to provide an API key but it will be more effective if you do.

    Function names are written as HTTP verb and then the urlscan named action so they should be mostly self explanatory.

    Please see https://urlscan.io/docs/api/ for more information on the urlscan.io API

    Also see https://pro.urlscan.io/help for the Pro level API documentation
    """

    # The domain for urlscan.io - in theory should never change but just in case
    URLSCAN_DOMAIN = 'urlscan.io'

    # Our base interaction urls
    QUOTA_URL = f'https://{URLSCAN_DOMAIN}/user/quotas/'
    API_URL = f'https://{URLSCAN_DOMAIN}/api/v1'
    DOM_URL = f'https://{URLSCAN_DOMAIN}/dom'
    SCREENSHOT_URL = f'https://{URLSCAN_DOMAIN}/screenshots'
    RESPONSE_URL = f'https://{URLSCAN_DOMAIN}/responses'

    # The currently valid visibilities (note the setting private or unlisted requires a pro urlscan.io account)
    VISIBILITIES = ['public', 'private', 'unlisted']
  
    def __init__(self, api_key=None, user_agent=None, retries=5, backoff=1):

        """
        Init the base class. You must provide an API key for this class to work

        You should also set a useragent unique to your application e.g BobSecurityScanner/v1
        """

        # We don't want to do anything if we don't have an API key
        if not api_key:
            logger.warning('No API key provided, this may limit some actions you can do with urslcan.io')
        
        # Set the user agent if none provided
        if not user_agent:
            user_agent = 'BasicUrlscanPy/v1'
            logger.warning(f'No user agent provided, using default user agent: {user_agent}. It is recommended to set a custom user agent')

        # Our headers
        self.headers = {
            # Strictly speaking we don't need to set the content type to JSON on all requests
            # as the GET requests don't have a body but it doesn't hurt
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            }
        
        if api_key:
            # If we have an API key we need to set the auth header
            self.headers['API-Key'] = api_key

        # Create a session object using our custom session function
        self.session = urlscan_session(retries=retries, backoff=backoff)

    def execute(self, method, url, payload=None, params=None):

        """
        The base function for making requests to the urlscan.io API
        
        If you are providing a payload it should be a dictionary that can be converted to JSON
        """

        if payload and type(payload) != dict:
            raise ValueError('Payload must be a dictionary')
        
        if payload:
            # We need to convert the payload to JSON
            try:
                payload = json.dumps(payload)
            except TypeError as e:
                raise UrlscanInvalidPayload(f'Failed to convert payload to JSON: {e}')
        
        if params and type(params) != dict:
            raise ValueError('Params must be a dictionary')
       
        with self.session as urlscan_request:
            # Ok try and excecute the request
            try:
                response = urlscan_request.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    data=payload,
                    params=params,
                )
            except requests.RequestException as e:
                logger.error(f'Request of {url} failed with the following error: {e}')
                # Set the response to None
                return None
            
            
            return response

    def get_quotas(self):

        """
        Get the quota information for user and team (if appropiate) of the current API key
        """

        return self.execute('GET', self.QUOTA_URL)

    def get_result(self, result_uuid):

        """
        Pull the result of a scan from urlscan.io
        """

        return self.execute('GET', f'{self.API_URL}/result/{result_uuid}')

    def get_screenshot(self, result_uuid):

        """
        Pull the screenshot of a scan from urlscan.io
        """

        return self.execute('GET', f'{self.SCREENSHOT_URL}/{result_uuid}')
    
    def get_dom(self, result_uuid):

        """
        Pull the DOM of a scan from urlscan.io
        """

        return self.execute('GET', f'{self.DOM_URL}/{result_uuid}')
    
    def get_response(self, response_sha256):
        
        """
        Pull the response of a specific sha256 hash from urlscan.io
        """

        return self.execute('GET', f'{self.RESPONSE_URL}/{response_sha256}')
    
    def get_scan_countries(self):

        """
        Get the list of available endpoint countries for scanning from
        """

        return self.execute('GET', f'{self.API_URL}/availableCountries/')
    
    def post_scan(self, payload):

        """
        Submit a new scan to urlscan.io. The payload should be a dictionary that can be converted to JSON

        The payload may contain any of the following BUT url is a mandatory field:

        * url - the URL to scan
        * visibility - the visibility of the scan, must be one of 'public', 'private', 'unlisted'
        * tags - a list of comma seperated tags to apply to the scan (note urlscan.io has a max limit of 10 tags)
        * customAgent - a custom user agent to use for the scan
        * referer - a custom referer url to use for the scan
        * country - the country to scan from (see get_scan_countries to get a list of available countries)

        Only the url field is mandatory, all others will be set to your urslcan.io account defaults
        """

        # Perform some very basic validation
        if type(payload) != dict:
            raise ValueError('Payload must be a dictionary')
        
        # You need to provide a url to scan
        if 'url' not in payload:
            raise ValueError('Payload must contain a URL to scan')
        
        # Visibility must be one of the valid visibilities
        if visibility := payload.get('visibility'):
            if visibility not in self.VISIBILITIES:
                raise ValueError(f'Visibility must be one of {self.VISIBILITIES}')

        # Run the request
        return self.execute('POST', f'{self.API_URL}/scan/', payload=payload)
    
    def get_search(self, params):

        """
        Submit a search query to urlscan.io. The params should be a dictionary. Only the q (query) field is mandatory

        Params may contain any of the following:

        q - the query to search for, refer to https://urlscan.io/docs/search/ for more information. Must be provided.
        size - the number of results to return (default is 100, max is 10000 depending on your urlscan.io account)
        search_after - defines where the search picks from (see urlscan.io docs for more information)

        Additional fields are available for pro accounts - see https://pro.urlscan.io/help/apis
        """
        
        # Perform some very basic validation
        if type(params) != dict:
            raise ValueError('Params must be a dictionary')
        
        if 'q' not in params:
            raise ValueError('Params must contain a query to search for')

        return self.execute('GET', f'{self.API_URL}/search/', params=params)
    

