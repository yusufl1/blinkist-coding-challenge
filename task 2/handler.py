import json
import os
from datetime import datetime
import requests
import boto3

# these values are stored as environment variables so they can easily be swapped out
# without changing source code and so that secrets are not versioned (APP_ID)
EXCHANGE_ENDPOINT = os.environ['EXCHANGE_ENDPOINT']
BASE_RATE = os.environ['BASE_RATE']
APP_ID = os.environ['APP_ID']
S3_BUCKET = os.environ['S3_BUCKET']


class Pipeline():
    # use a class to cleanly contain and pass all required variables and API response
    """
    Data pipeline fetching latest exchange rates from provided endpoint 
    and saving the result to S3 bucket as JSON. 

    Attributes
    ----------
    exchange_endpoint : str
        URL of the API from which to fetch latest exchange rates

    app_id : str
        API key to authenticate into the exchange endpoint

    s3_bucket : str
        Name of the S3 bucket where results will be stored 

    base_rate : str
        base rate for currency exchange, default EUR

    current_time : str
        timestamp at the time of instantiating this Pipeline

    Methods
    -------
    get_rates():
        Query exchange endpoint to fetch latest exchange rates

    put_into_s3():
        Store the latest exchange rates in S3 as JSON
    """

    def __init__(self, exchange_endpoint, app_id, s3_bucket, base_rate='EUR'):
        """
        Constructs all the necessary attributes for the Pipeline object.

        Parameters
        ----------
        exchange_endpoint : str
            URL of the API from which to fetch latest exchange rates

        app_id : str
            API key to authenticate into the exchange endpoint

        s3_bucket : str
            Name of the S3 bucket where results will be stored 

        base_rate : str
            base rate for currency exchange, default EUR
        """
        self.exchange_endpoint = exchange_endpoint
        self.base_rate = base_rate
        # get current timestamp to use in the file name, to keep a record
        # of the exchange rates being the latest as of when
        self.current_time = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        self.app_id = app_id
        self.s3_bucket = s3_bucket

    def get_rates(self):
        """
        Query exchange endpoint to fetch latest exchange rates

        Returns
        -------
        None
        """
        params = {'app_id': self.app_id,
                  'base': self.base_rate}
        request = requests.get(self.exchange_endpoint, params=params)
        self.exchange_rates = request.json()

        print('grabbed exchange rates')

    def put_into_s3(self):
        """
        Store the latest exchange rates in S3 as JSON

        Returns
        -------
        None
        """
        # make a descriptive file name for the exchange rates
        self.filename = '%s_exchange_rates_as_of_%s.json' % (
            self.base_rate, self.current_time
        )

        # instantiate S3 object and set key to above file name
        s3 = boto3.resource('s3')
        self.s3_object = s3.Object(S3_BUCKET, self.filename)

        # convert the exchange rates to binary to avoid saving the
        # file on disk by mounting an EFS to our Lambda, and encode
        # in utf8 so it's readable
        exchange_rates_binary = bytes(
            json.dumps(self.exchange_rates).encode('UTF-8'))

        self.s3_object.put(Body=exchange_rates_binary)

        print('placed into s3')


def main(event, context):
    """
    Lambda handler which fetches the latest exchange rates 
    and stores result in S3 as JSON using a Pipline object 

    Parameters
    ----------
    event : json
        Data passed to this Lambda function upon execution. Could 
        be a Cloudwatch trigger, an HTTP call or other

    context : json
        Contains data about this Lambda function's execution environment

    Returns
    -------
    json
        JSON object containing statusCode and message stating as of when the 
        fetched exchange rates are the latest

    """
    p = Pipeline(EXCHANGE_ENDPOINT, APP_ID, S3_BUCKET, BASE_RATE)
    p.get_rates()
    p.put_into_s3()

    # return status code OK and descriptive message so caller
    # knows the function worked
    return {
        "statusCode": 200,
        "body": "Exchange rates as of %s stored in S3" % p.current_time
    }
